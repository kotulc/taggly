"""spam command: Spam detection scoring for the supplied text."""

from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand


class SpamConfig(BaseModel):
    threshold: float = Field(0.5, description="The spam score threshold to assign a 'spam' label")


class SpamInput(BaseModel):
    content: str


class SpamOutput(BaseModel):
    tags: list[str]
    score: float


class SpamCommand(AbstractBaseCommand):
    name = "spam"
    Input = SpamInput
    Output = SpamOutput
    Config = SpamConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else SpamConfig()
        super().__init__(api_url, cfg)
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

        # Compute spam score and assign "spam" tag if threshold is achieved
        cfg = config or self.config or SpamConfig()
        score = torch.softmax(logits, dim=1).flatten()[1].item()
        tags = ["spam"] if score >= cfg.threshold else []

        return SpamOutput(tags=tags, score=score)
