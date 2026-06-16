"""polar command: Positive/neutral/negative polarity sentiment analysis."""

from pydantic import BaseModel, Field

from taggly.models.base import AbstractBaseCommand

# Map VADER's 'neg', 'neu', 'pos' keys to more intuitive output keys
VADER_MAP = {'neg': 'negative', 'neu': 'neutral', 'pos': 'positive'}


class PolarConfig(BaseModel):
    model: str = Field("vader", description="Sentiment analysis model to use: 'vader' or 'blob'")


class PolarInput(BaseModel):
    content: str = Field(..., description="A text string to compute polarity sentiment for.")


class PolarOutput(BaseModel):
    tags: list[str] = Field(..., description="The dominant polarity label(s): 'positive', 'neutral', or 'negative'.")
    scores: dict[str, float] = Field(..., description="Polarity scores keyed by label.")


class PolarCommand(AbstractBaseCommand):
    name = "polar"
    Input = PolarInput
    Output = PolarOutput
    Config = PolarConfig

    def __init__(self, api_url: str=None, config: BaseModel=None, **kwargs):
        super().__init__(api_url, config, **kwargs)
        self._vader = None  # cached VADER analyzer — only loaded on first local use

    def warmup(self) -> None:
        """Pre-load the default polarity model."""
        if self.config.model.lower() != "blob" and self._vader is None:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()

    def operation(self, data: PolarInput, config: PolarConfig=None) -> PolarOutput:
        """Compute positive/neutral/negative polarity for the supplied text."""
        cfg = config or self.config or PolarConfig()
        scores = self._analyze(data.content, cfg)
        return PolarOutput(tags=[max(scores, key=scores.get)], scores=scores)

    def _analyze(self, text: str, cfg: PolarConfig) -> dict:
        """Compute scores dict using the model from the effective config."""
        if cfg.model.lower() == "blob":
            # Compute polarity score using TextBlob (pos/neg labels)
            from textblob import TextBlob
            p = TextBlob(text).sentiment.polarity
            return {"negative": max(-p, 0), "positive": max(p, 0)}
        
        # Compute polarity scores using VADER (pos/neu/neg labels)
        if self._vader is None:
            self.warmup()

        s = self._vader.polarity_scores(text)
        return {v: s[k] for k, v in VADER_MAP.items()}
