"""ents command: Extract entities from the supplied text."""

from typing import List
from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class EntsConfig(BaseModel):
    top_n: int = Field(10, description="Number of entities to extract")
    language: str = Field("en_core_web_lg", description="Language for spacy nlp model")


class EntsInput(BaseModel):
    content: str


class EntsOutput(BaseModel):
    entities: List[str]


class EntsCommand(AbstractBaseCommand):
    name = "ents"
    Input = EntsInput
    Output = EntsOutput
    Config = EntsConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else EntsConfig()
        super().__init__(api_url, cfg)
        self._spacy = None  # cached spacy model — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the spacy model."""
        if self._spacy is None:
            import spacy
            try:
                self._spacy = spacy.load(self.config.language)
            except OSError:
                # If the model isn't already downloaded, download it and try loading again
                spacy.cli.download(self.config.language)
                self._spacy = spacy.load(self.config.language)

    def operation(self, data: EntsInput, config: EntsConfig=None) -> EntsOutput:
        """Extract entities from the supplied text."""
        cfg = config if config is not None else self.config
        if self._spacy is None:
            self.warmup()

        # Use spacy NLP to extract entities, then deduplicate and limit to top_n
        entities = {entity.text.strip() for entity in self._spacy(data.content).ents}

        return EntsOutput(entities=list(entities)[:cfg.top_n])
