"""tox command: Toxicity scoring for the supplied text."""

from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class ToxConfig(BaseModel):
    threshold: float = Field(0.5, description="The toxicity score threshold to assign a 'toxic' label")


class ToxInput(BaseModel):
    content: str = Field(..., description="A text string to score for toxicity.")


class ToxOutput(BaseModel):
    tags: list[str] = Field(..., description="Label list — contains 'toxic' if the threshold is exceeded.")
    score: float = Field(..., description="Toxicity probability score from 0 to 1.")


class ToxCommand(AbstractBaseCommand):
    name = "tox"
    Input = ToxInput
    Output = ToxOutput
    Config = ToxConfig

    def __init__(self, api_url: str=None, config: BaseModel=None, **kwargs):
        super().__init__(api_url, config, **kwargs)
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
        
        score = self._pipe(data.content)[0]['score']
        cfg = config if config is not None else ToxConfig()
        tags = ["toxic"] if score >= cfg.threshold else []

        return ToxOutput(tags=tags, score=score)
