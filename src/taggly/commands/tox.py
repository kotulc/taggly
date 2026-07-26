"""tox command: Toxicity scoring for the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import from_hub, token_windows
from taggly.models.base import AbstractBaseCommand

_MAX_TOKENS = 512  # toxic-bert position-embedding limit


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
        self._tokenizer = None

    def warmup(self) -> None:
        """Pre-load the toxic-bert pipeline."""
        if self._pipe is None:
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            model = from_hub(AutoModelForSequenceClassification.from_pretrained, "unitary/toxic-bert")
            self._tokenizer = from_hub(AutoTokenizer.from_pretrained, "unitary/toxic-bert")
            self._pipe = pipeline("text-classification", model=model, tokenizer=self._tokenizer)

    def operation(self, data: ToxInput, params: ToxParams=None) -> ToxOutput:
        """Compute toxicity score for the supplied text."""
        # Long input is scored in <=512-token windows; the highest window score wins so
        # toxicity anywhere in the text is flagged without overflowing the model.
        if self._pipe is None:
            self.warmup()
        p = params or ToxParams()
        score = 0.0
        for window in token_windows(self._tokenizer, data.content, _MAX_TOKENS):
            score = max(score, self._pipe(window, truncation=True, max_length=_MAX_TOKENS)[0]["score"])
        return ToxOutput(tags=["toxic"] if score >= p.threshold else [], score=score)
