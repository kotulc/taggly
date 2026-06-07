"""sent command: Positive/neutral/negative sentiment analysis."""

from pydantic import BaseModel, Field

from taggly.base import AbstractBaseCommand


class SentConfig(BaseModel):
    model: str = Field("vader", description="Sentiment analysis model to use: 'vader' or 'blob'")


class SentInput(BaseModel):
    content: str


class SentOutput(BaseModel):
    tag: str
    scores: dict[str, float]


class SentCommand(AbstractBaseCommand):
    name = "sent"
    Input = SentInput
    Output = SentOutput
    Config = SentConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else SentConfig()
        super().__init__(api_url, cfg)
        self._analyzer = None  # cached callable(text) -> scores dict

    def warmup(self) -> None:
        """Pre-load the configured sentiment model."""
        if self._analyzer is None:
            if self.config.model.lower() == "blob":
                from textblob import TextBlob
                def analyze(text):
                    p = TextBlob(text).sentiment.polarity
                    return {"neg": max(0.0, -p), "neu": round(1.0 - abs(p), 4), "pos": max(0.0, p)}
                self._analyzer = analyze
            else:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                sia = SentimentIntensityAnalyzer()
                self._analyzer = lambda text: {k: sia.polarity_scores(text)[k] for k in ('neg', 'neu', 'pos')}

    def operation(self, data: SentInput, config: SentConfig=None) -> SentOutput:
        """Compute positive/neutral/negative sentiment for the supplied text."""
        if self._analyzer is None:
            self.warmup()
            
        scores = self._analyzer(data.content)
        return SentOutput(tag=max(scores, key=scores.get), scores=scores)
