"""ents command: Extract named entities from the supplied text."""

from typing import List
from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class EntsConfig(BaseModel):
    language: str = Field("en_core_web_sm", description="spaCy model name for entity extraction")


class EntsParams(BaseModel):
    top_n: int = Field(10, description="Maximum number of entities to return")
    normalize: bool = Field(False, description="Normalize candidates to lowercase")


class EntsInput(BaseModel):
    content: str = Field(..., description="A text string to extract named entities from.")


class EntsOutput(BaseModel):
    entities: List[str] = Field(..., description="The list of extracted entities.")


class EntsCommand(AbstractBaseCommand):
    name = "ents"
    Config = EntsConfig
    Params = EntsParams
    Input = EntsInput
    Output = EntsOutput

    def __init__(self, config: EntsConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else EntsConfig()
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

    def operation(self, data: EntsInput, params: EntsParams=None) -> EntsOutput:
        """Extract named entities from the supplied text."""
        p = params or EntsParams()
        if self._spacy is None:
            self.warmup()
        if p.normalize:
            entities = {ent.text.strip().lower() for ent in self._spacy(data.content).ents}
        else:
            entities = {ent.text.strip() for ent in self._spacy(data.content).ents}
        return EntsOutput(entities=list(entities)[:p.top_n])
