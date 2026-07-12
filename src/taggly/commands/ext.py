"""ext command: Extract typed concepts (entities, topics, relations) via a language model."""

import json
from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.loaders import load_generator
from taggly.models.base import AbstractBaseCommand

# Define generative prompt template
PROMPT = (
    "Extract the following from the text as a JSON object with these keys: "
    "{}. Each value is a list of short strings. "
    "Return only the JSON object.\n\nText: {}"
)


class ExtConfig(BaseModel):
    model: str = Field("gemma-2b", description="Generative model: 'gemma-2b', 'gemma-4b', 'gemma-12b', or 'smollm-135m'")
    max_tokens: int = Field(256, description="Maximum number of tokens to generate")


class ExtParams(BaseModel):
    concepts: str = Field("concepts, entities, topics", description="Comma-separated concept categories to extract (spaces around commas are fine)")


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
        """Extract typed concepts from the supplied text as a JSON object."""
        from transformers import GenerationConfig
        params = params if params else ExtParams()
        keys = [c.strip() for c in params.concepts.split(",") if c.strip()]
        messages = [{"role": "user", "content": PROMPT.format(", ".join(keys), data.content)}]
        gen_config = GenerationConfig(max_new_tokens=self._config.max_tokens)
        output = load_generator(self._config.model)(messages, generation_config=gen_config)
        result = output[0]["generated_text"]
        text = result[-1]["content"] if isinstance(result, list) else result
        return ExtOutput(concepts=self._parse(text, keys))

    def _parse(self, text: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Parse the JSON object from the model output, defaulting to empty lists."""
        try:
            parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            parsed = {}
        return {c: list(parsed.get(c, [])) for c in concepts}
