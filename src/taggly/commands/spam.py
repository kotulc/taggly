"""spam command: Spam detection scoring for the supplied text."""

from pydantic import BaseModel

from taggly.base import AbstractBaseCommand


class SpamInput(BaseModel):
    content: str


class SpamOutput(BaseModel):
    score: float


class SpamCommand(AbstractBaseCommand):
    name = "spam"
    Input = SpamInput
    Output = SpamOutput

    def __init__(self, api_url: str=None, config: BaseModel=None):
        super().__init__(api_url, config)
        self._tokenizer = None  # BERT tokenizer — only loaded on first local use
        self._classifier = None  # BERT classifier — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the spam-detector BERT model and tokenizer."""
        if self._tokenizer is None:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            model_id = "AntiSpamInstitute/spam-detector-bert-MoE-v2.2"
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)
            self._classifier = AutoModelForSequenceClassification.from_pretrained(model_id)

    def operation(self, data: SpamInput, config: BaseModel=None) -> SpamOutput:
        """Compute spam score for the supplied text."""
        import torch
        
        if self._tokenizer is None:
            self.warmup()
        inputs = self._tokenizer(data.content, return_tensors="pt")

        with torch.no_grad():
            logits = self._classifier(**inputs).logits

        return SpamOutput(score=torch.softmax(logits, dim=1).flatten()[1].item())
