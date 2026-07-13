"""spam command: Spam detection scoring for the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import from_hub
from taggly.models.base import AbstractBaseCommand


class SpamParams(BaseModel):
    threshold: float = Field(0.5, description="Spam probability threshold for assigning a 'spam' label")


class SpamInput(BaseModel):
    content: str = Field(..., description="A text string to score for spam.")


class SpamOutput(BaseModel):
    tags: list[str] = Field(..., description="Label list — contains 'spam' if the threshold is exceeded.")
    score: float = Field(..., description="Spam probability score from 0 to 1.")


class SpamCommand(AbstractBaseCommand):
    name = "spam"
    Params = SpamParams
    Input = SpamInput
    Output = SpamOutput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tokenizer = None
        self._classifier = None

    def warmup(self) -> None:
        """Pre-load the spam-detector BERT model and tokenizer."""
        if self._tokenizer is None:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            model_id = "AntiSpamInstitute/spam-detector-bert-MoE-v2.2"
            self._tokenizer = from_hub(AutoTokenizer.from_pretrained, model_id)
            self._classifier = from_hub(AutoModelForSequenceClassification.from_pretrained, model_id)

    def operation(self, data: SpamInput, params: SpamParams=None) -> SpamOutput:
        """Compute spam score for the supplied text."""
        import torch
        if self._tokenizer is None:
            self.warmup()
        p = params or SpamParams()
        inputs = self._tokenizer(data.content, return_tensors="pt")
        with torch.no_grad():
            logits = self._classifier(**inputs).logits
        score = torch.softmax(logits, dim=1).flatten()[1].item()
        return SpamOutput(tags=["spam"] if score >= p.threshold else [], score=score)
