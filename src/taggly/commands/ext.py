"""ext command: Extract typed concepts (entities, topics, relations) via a language model."""

import json
import re
from typing import Dict, List

from pydantic import BaseModel, Field

from taggly.loaders import generate, load_generator
from taggly.models.base import AbstractBaseCommand

JSON_PROMPT = (
    "Extract the following from the text as a JSON object with these keys: "
    "{}. Each value is a list of at most 10 short strings. "
    "Return only the JSON object.\n\nText: {}"
)

# Long inputs make small models emit truncated / noisy JSON that `_parse` would
# otherwise swallow into empty groups. Stay under the observed ~2100-char cliff.
_CHUNK_CHARS = 1800
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


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
        merged = {k: [] for k in keys}
        for chunk in self._chunks(data.content):
            text = self._generate(JSON_PROMPT.format(", ".join(keys), chunk))
            for k, vals in self._parse(text, keys).items():
                merged[k].extend(vals)
        concepts = {k: self._truncate(vals, params.max_ngram) for k, vals in merged.items()}
        if params.normalize:
            concepts = {k: list({v.lower() for v in vals}) for k, vals in concepts.items()}
        return ExtOutput(concepts=concepts)

    def _generate(self, prompt: str) -> str:
        """Run one single-message generation and return the reply text."""
        return generate(self._config.model, [{"role": "user", "content": prompt}], self._config.max_tokens)

    def _parse(self, text: str, concepts: List[str]) -> Dict[str, List[str]]:
        """Parse a JSON object with the requested keys from the model output."""
        parsed = self._json_object(text, concepts)
        return {c: self._strings(parsed.get(c)) for c in concepts}

    @staticmethod
    def _json_object(text: str, preferred_keys: List[str] = None) -> dict:
        """Return the first decodable JSON object, preferring ones with concept keys."""
        cleaned = _THINK_BLOCK.sub("", text)
        decoder = json.JSONDecoder()
        fallback = {}
        for i, ch in enumerate(cleaned):
            if ch != "{":
                continue
            try:
                obj, _ = decoder.raw_decode(cleaned, i)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if preferred_keys and any(k in obj for k in preferred_keys):
                return obj
            if not fallback:
                fallback = obj
        return fallback

    @staticmethod
    def _chunks(text: str, max_chars: int = _CHUNK_CHARS) -> List[str]:
        """Split long text into bounded chunks at paragraph/sentence/word boundaries."""
        text = text.strip()
        if not text:
            return [""]
        if len(text) <= max_chars:
            return [text]
        chunks: List[str] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(start + max_chars, n)
            if end < n:
                window = text[start:end]
                brk = window.rfind("\n\n")
                if brk <= max_chars // 2:
                    brk = window.rfind(". ")
                if brk <= max_chars // 2:
                    brk = window.rfind(" ")
                if brk > max_chars // 2:
                    end = start + brk + (2 if window.startswith("\n\n", brk) else 1)
            piece = text[start:end].strip()
            if piece:
                chunks.append(piece)
            start = end if end > start else start + max_chars
        return chunks or [text[:max_chars]]

    @staticmethod
    def _strings(value) -> List[str]:
        """Keep only the string items of a parsed JSON value, dropping malformed shapes."""
        return list({i for i in value if isinstance(i, str)}) if isinstance(value, list) else []

    @staticmethod
    def _truncate(values: List[str], max_ngram: int) -> List[str]:
        """Trim each candidate to at most max_ngram words, deduplicating collisions."""
        return list(dict.fromkeys(" ".join(v.split()[:max_ngram]) for v in values))
