"""topics command: Discover latent topics in the supplied text via BERTopic."""

import re
from typing import List
from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand


class TopicsConfig(BaseModel):
    model: str = Field("all-minilm", description="Embedding model: 'all-minilm', 'bge-base', or 'bge-large'")
    top_n: int = Field(10, description="Number of topic keywords to return")


class TopicsInput(BaseModel):
    content: str


class TopicsOutput(BaseModel):
    topics: List[str]


class TopicsCommand(AbstractBaseCommand):
    name = "topics"
    Input = TopicsInput
    Output = TopicsOutput
    Config = TopicsConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else TopicsConfig()
        super().__init__(api_url, cfg)

    def warmup(self) -> None:
        """Pre-load the configured embedding model."""
        load_embedder((self.config or TopicsConfig()).model)

    def operation(self, data: TopicsInput, config: TopicsConfig=None) -> TopicsOutput:
        """Discover topic keywords across the sentences of the supplied text."""
        cfg = config or self.config or TopicsConfig()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", data.content) if s.strip()]
        return TopicsOutput(topics=self._topics(sentences, cfg))

    def _topics(self, sentences: List[str], cfg: TopicsConfig) -> List[str]:
        """Fit BERTopic and return de-duplicated keywords across discovered topics."""
        from bertopic import BERTopic
        model = BERTopic(embedding_model=load_embedder(cfg.model))
        model.fit_transform(sentences)
        words = [word for topic in model.get_topics().values() for word, _ in topic]
        return [w for w in dict.fromkeys(words) if w][:cfg.top_n]
