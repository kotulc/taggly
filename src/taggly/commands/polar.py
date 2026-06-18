"""polar command: Positive/neutral/negative polarity sentiment analysis."""

from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand

VADER_MAP = {'neg': 'negative', 'neu': 'neutral', 'pos': 'positive'}


class PolarConfig(BaseModel):
    model: str = Field("vader", description="Sentiment model: 'vader' or 'blob'")


class PolarInput(BaseModel):
    content: str = Field(..., description="A text string to compute polarity sentiment for.")


class PolarOutput(BaseModel):
    tags: list[str] = Field(..., description="The dominant polarity label(s): 'positive', 'neutral', or 'negative'.")
    scores: dict[str, float] = Field(..., description="Polarity scores keyed by label.")


class PolarCommand(AbstractBaseCommand):
    name = "polar"
    Config = PolarConfig
    Input = PolarInput
    Output = PolarOutput

    def __init__(self, config: PolarConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else PolarConfig()
        self._vader = None  # cached VADER analyzer — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the configured polarity model."""
        if self._config.model.lower() != "blob" and self._vader is None:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()

    def operation(self, data: PolarInput, params: BaseModel=None) -> PolarOutput:
        """Compute positive/neutral/negative polarity for the supplied text."""
        scores = self._analyze(data.content)
        return PolarOutput(tags=[max(scores, key=scores.get)], scores=scores)

    def _analyze(self, text: str) -> dict:
        """Compute scores using the system-configured model."""
        if self._config.model.lower() == "blob":
            from textblob import TextBlob
            p = TextBlob(text).sentiment.polarity
            return {"negative": max(-p, 0), "positive": max(p, 0)}
        if self._vader is None:
            self.warmup()
        s = self._vader.polarity_scores(text)
        return {v: s[k] for k, v in VADER_MAP.items()}
