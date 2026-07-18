"""ent command: Extract named entities from the supplied text."""

from typing import List
from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class EntConfig(BaseModel):
    language: str = Field("en_core_web_sm", description="spaCy model name for entity extraction")


class EntParams(BaseModel):
    top_n: int = Field(10, description="Maximum number of entities to return")
    normalize: bool = Field(False, description="Normalize candidates to lowercase")


class EntInput(BaseModel):
    content: str = Field(..., description="A text string to extract named entities from.")


class EntOutput(BaseModel):
    entities: List[str] = Field(..., description="The list of extracted entities.")


class EntCommand(AbstractBaseCommand):
    name = "ent"
    Config = EntConfig
    Params = EntParams
    Input = EntInput
    Output = EntOutput

    def __init__(self, config: EntConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else EntConfig()
        self._spacy = None  # cached spaCy model — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the spaCy model."""
        if self._spacy is None:
            import spacy
            try:
                self._spacy = spacy.load(self._config.language)
            except OSError:
                spacy.cli.download(self._config.language)
                self._spacy = spacy.load(self._config.language)

    def operation(self, data: EntInput, params: EntParams=None) -> EntOutput:
        """Extract named entities from the supplied text."""
        p = params or EntParams()
        if self._spacy is None:
            self.warmup()
        if p.normalize:
            entities = {ent.text.strip().lower() for ent in self._spacy(data.content).ents}
        else:
            entities = {ent.text.strip() for ent in self._spacy(data.content).ents}
        return EntOutput(entities=list(entities)[:p.top_n])
