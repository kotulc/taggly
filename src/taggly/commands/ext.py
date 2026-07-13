"""ext command: Extract typed concepts (entities, topics, relations) via a language model."""

import json
from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.loaders import generate, load_generator
from taggly.models.base import AbstractBaseCommand

# Prompts include a one-shot worked example — small models copy a demonstrated
# format far more reliably than they follow format descriptions.
EXAMPLE_TEXT = "Marie Curie won the Nobel Prize in Paris."
LIST_PROMPT = "List the {} in this text, one per line.\n\nText: {}"
LIST_EXAMPLE = "- Marie Curie\n- Nobel Prize\n- Paris"
JSON_PROMPT = (
    "Extract the following from the text as a JSON object with these keys: "
    "{}. Each value is a list of short strings. "
    "Return only the JSON object.\n\nText: {}"
)
JSON_EXAMPLE = '{"entities": ["Marie Curie", "Nobel Prize", "Paris"], "topics": ["science awards"]}'

MAX_ITEM_WORDS = 6  # generated lines longer than this are prose, not list items


class ExtConfig(BaseModel):
    model: str = Field("smollm-135m", description="Generative model: 'smollm-135m', 'gemma-2b', 'gemma-4b', or 'gemma-12b'")
    max_tokens: int = Field(256, description="Maximum number of tokens to generate")


class ExtParams(BaseModel):
    concepts: str = Field("concepts, entities, topics", description="Comma-separated concept categories to extract (spaces around commas are fine)")
    structured: bool = Field(False, description="Extract all concepts in one structured JSON generation instead of one list generation per concept")


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
        if params.structured:
            messages = [
                {"role": "user", "content": JSON_PROMPT.format(", ".join(keys), EXAMPLE_TEXT)},
                {"role": "assistant", "content": JSON_EXAMPLE},
                {"role": "user", "content": JSON_PROMPT.format(", ".join(keys), data.content)},
            ]
            text = generate(self._config.model, messages, self._config.max_tokens)
            return ExtOutput(concepts=self._parse(text, keys))
        return ExtOutput(concepts={k: self._concept(k, data.content) for k in keys})

    def _concept(self, key: str, content: str) -> List[str]:
        """Generate and parse a bulleted list for one concept category."""
        messages = [
            {"role": "user", "content": LIST_PROMPT.format(key, EXAMPLE_TEXT)},
            {"role": "assistant", "content": LIST_EXAMPLE},
            {"role": "user", "content": LIST_PROMPT.format(key, content)},
        ]
        return self._lines(generate(self._config.model, messages, self._config.max_tokens))

    def _lines(self, text: str) -> List[str]:
        """Return the leading short list items, stopping at the first prose line."""
        items = []
        for line in text.strip().splitlines():
            line = line.strip().lstrip("-*").strip()
            if not line or len(line.split()) > MAX_ITEM_WORDS:
                break
            items.append(line)
        return items

    def _parse(self, text: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Parse the JSON object from the model output, defaulting to empty lists."""
        try:
            parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            parsed = {}
        return {c: list(parsed.get(c, [])) for c in concepts}
