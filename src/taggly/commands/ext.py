"""ext command: Extract typed concepts (entities, topics, relations) via a language model."""

import json
from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.loaders import load_generator
from taggly.models.base import AbstractBaseCommand

# Default concept categories the model is asked to extract
DEFAULT_CONCEPTS = ["entities", "topics", "relations"]


class ExtConfig(BaseModel):
    model: str = Field("gemma-1b", description="Generative model: 'gemma-1b', 'gemma-4b', or 'gemma-12b'")
    concepts: List[str] = Field(DEFAULT_CONCEPTS, description="Concept categories to extract")
    max_tokens: int = Field(256, description="Maximum number of tokens to generate")


class ExtInput(BaseModel):
    content: str


class ExtOutput(BaseModel):
    concepts: Dict[str, List[str]] = Field(..., description="Extracted concepts grouped by category")


class ExtCommand(AbstractBaseCommand):
    name = "ext"
    Input = ExtInput
    Output = ExtOutput
    Config = ExtConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else ExtConfig()
        super().__init__(api_url, cfg)

    def warmup(self) -> None:
        """Pre-load the configured generative model."""
        load_generator((self.config or ExtConfig()).model)

    def operation(self, data: ExtInput, config: ExtConfig=None) -> ExtOutput:
        """Extract typed concepts from the supplied text as a JSON object."""
        cfg = config or self.config or ExtConfig()
        prompt = (
            f"Extract the following from the text as a JSON object with these keys: "
            f"{', '.join(cfg.concepts)}. Each value is a list of short strings. "
            f"Return only JSON.\n\nText: {data.content}"
        )
        output = load_generator(cfg.model)(prompt, max_new_tokens=cfg.max_tokens, return_full_text=False)
        return ExtOutput(concepts=self._parse(output[0]["generated_text"], cfg.concepts))

    def _parse(self, text: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Parse the JSON object from the model output, defaulting to empty lists."""
        try:
            parsed = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except (ValueError, json.JSONDecodeError):
            parsed = {}
        return {c: list(parsed.get(c, [])) for c in concepts}
