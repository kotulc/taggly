"""tox command: Toxicity scoring for the supplied text."""

from pydantic import BaseModel

from taggly.base import AbstractBaseCommand


class ToxInput(BaseModel):
    content: str


class ToxOutput(BaseModel):
    score: float


class ToxCommand(AbstractBaseCommand):
    name = "tox"
    Input = ToxInput
    Output = ToxOutput

    def __init__(self, api_url: str=None, config: BaseModel=None):
        super().__init__(api_url, config)
        self._pipe = None  # toxic-bert pipeline — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the toxic-bert pipeline."""
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline("text-classification", model="unitary/toxic-bert")

    def operation(self, data: ToxInput, config: BaseModel=None) -> ToxOutput:
        """Compute toxicity score for the supplied text."""
        if self._pipe is None:
            self.warmup()
        return ToxOutput(score=self._pipe(data.content)[0]['score'])
