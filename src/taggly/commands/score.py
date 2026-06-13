"""score command: Semantic similarity scores between a query and candidate strings."""

from typing import List
from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand


class ScoreConfig(BaseModel):
    model: str = Field("all-minilm", description="Embedding model: 'all-minilm', 'bge-base', or 'bge-large'")
    metric: str = Field("cosine", description="Similarity metric: 'cosine' or 'dot'")


class ScoreInput(BaseModel):
    query: str
    candidates: List[str]


class ScoreOutput(BaseModel):
    scores: List[float]


class ScoreCommand(AbstractBaseCommand):
    name = "score"
    Input = ScoreInput
    Output = ScoreOutput
    Config = ScoreConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else ScoreConfig()
        super().__init__(api_url, cfg)

    def warmup(self) -> None:
        """Pre-load the configured embedding model."""
        load_embedder((self.config or ScoreConfig()).model)

    def operation(self, data: ScoreInput, config: ScoreConfig=None) -> ScoreOutput:
        """Score each candidate's semantic similarity to the query."""
        cfg = config or self.config or ScoreConfig()
        model = load_embedder(cfg.model)
        query = model.encode(data.query)
        candidates = model.encode(data.candidates)
        return ScoreOutput(scores=self._similarity(query, candidates, cfg.metric))

    def _similarity(self, query, candidates, metric: str) -> List[float]:
        """Return similarity of the query embedding to each candidate embedding."""
        if metric == "dot":
            import numpy as np
            return [float(np.dot(query, c)) for c in candidates]

        from sentence_transformers.util import cos_sim
        return cos_sim(query, candidates).flatten().tolist()
