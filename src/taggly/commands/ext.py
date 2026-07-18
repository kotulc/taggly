"""ext command: Extract typed concepts (entities, topics, relations) via a language model."""

import json
from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.loaders import generate, load_generator
from taggly.models.base import AbstractBaseCommand

JSON_PROMPT = (
    "Extract the following from the text as a JSON object with these keys: "
    "{}. Each value is a list of short strings. "
    "Return only the JSON object.\n\nText: {}"
)


class ExtConfig(BaseModel):
    model: str = Field("qwen-0.8b", description="Generative model: 'qwen-0.8b', 'gemma-2b', 'gemma-4b', or 'gemma-12b'")
    max_tokens: int = Field(256, description="Maximum number of tokens to generate")


class ExtParams(BaseModel):
    concepts: str = Field("concepts, entities, topics", description="Comma-separated concept categories to extract (spaces around commas are fine)")
    max_ngram: int = Field(2, description="Maximum candidate tag word length")
    normalize: bool = Field(False, description="Normalize candidates to lowercase")


class ExtInput(BaseModel):
    content: str = Field(..., description="A text string to extract concepts from")


class ExtOutput(BaseModel):
    concepts: Dict[str, List[str]] = Field(..., description="Extracted concepts grouped by category")


class ExtCommand(AbstractBaseCommand):
    name = "ext"
    requires_llm = True
    Config = ExtConfig
    Params = ExtParams
    Input = ExtInput
    Output = ExtOutput

    def __init__(self, config: ExtConfig=None, **kwargs):
        super().__init__(**kwargs)
        # Store language model system configurations
        self._config = config if config else ExtConfig()

    def warmup(self) -> None:
        """Pre-load the configured generative model."""
        load_generator(self._config.model)

    def operation(self, data: ExtInput, params: ExtParams=None) -> ExtOutput:
        """Extract typed concepts from the supplied text."""
        params = params if params else ExtParams()
        keys = [c.strip() for c in params.concepts.split(",") if c.strip()]
        text = self._generate(JSON_PROMPT.format(", ".join(keys), data.content))
        concepts = self._parse(text, keys)
        concepts = {k: self._truncate(vals, params.max_ngram) for k, vals in concepts.items()}
        if params.normalize:
            concepts = {k: list({v.lower() for v in vals}) for k, vals in concepts.items()}
        return ExtOutput(concepts=concepts)

    def _generate(self, prompt: str) -> str:
        """Run one single-message generation and return the reply text."""
        return generate(self._config.model, [{"role": "user", "content": prompt}], self._config.max_tokens)

    def _parse(self, text: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Parse the JSON object from the model output, defaulting to empty lists."""
        try:
            parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            parsed = {}
        return {c: self._strings(parsed.get(c)) for c in concepts}

    @staticmethod
    def _strings(value) -> List[str]:
        """Keep only the string items of a parsed JSON value, dropping malformed shapes."""
        return list({i for i in value if isinstance(i, str)}) if isinstance(value, list) else []

    @staticmethod
    def _truncate(values: List[str], max_ngram: int) -> List[str]:
        """Trim each candidate to at most max_ngram words, deduplicating collisions."""
        return list(dict.fromkeys(" ".join(v.split()[:max_ngram]) for v in values))
