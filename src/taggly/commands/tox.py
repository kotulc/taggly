"""tox command: Toxicity scoring for the supplied text."""

from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class ToxParams(BaseModel):
    threshold: float = Field(0.5, description="Toxicity probability threshold for assigning a 'toxic' label")


class ToxInput(BaseModel):
    content: str = Field(..., description="A text string to score for toxicity.")


class ToxOutput(BaseModel):
    tags: list[str] = Field(..., description="Label list — contains 'toxic' if the threshold is exceeded.")
    score: float = Field(..., description="Toxicity probability score from 0 to 1.")


class ToxCommand(AbstractBaseCommand):
    name = "tox"
    Params = ToxParams
    Input = ToxInput
    Output = ToxOutput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pipe = None

    def warmup(self) -> None:
        """Pre-load the toxic-bert pipeline."""
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline("text-classification", model="unitary/toxic-bert")

    def operation(self, data: ToxInput, params: ToxParams=None) -> ToxOutput:
        """Compute toxicity score for the supplied text."""
        if self._pipe is None:
            self.warmup()
        p = params or ToxParams()
        score = self._pipe(data.content)[0]["score"]
        return ToxOutput(tags=["toxic"] if score >= p.threshold else [], score=score)
