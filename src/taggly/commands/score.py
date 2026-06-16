"""score command: Semantic similarity scores between a query and candidate strings."""

from typing import List
from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand


class ScoreConfig(BaseModel):
    model: str = Field("all-minilm", description="Embedding model: 'all-minilm', 'bge-base', or 'bge-large'")


class ScoreInput(BaseModel):
    query: str = Field(..., description="The reference text to compare candidates against.")
    candidates: List[str] = Field(..., description="A list of candidate strings to score.")


class ScoreOutput(BaseModel):
    scores: List[float] = Field(..., description="Cosine similarity scores in the same order as candidates.")


class ScoreCommand(AbstractBaseCommand):
    name = "score"
    Input = ScoreInput
    Output = ScoreOutput
    Config = ScoreConfig

    def warmup(self) -> None:
        """Pre-load the configured embedding model."""
        load_embedder((self.config or ScoreConfig()).model)

    def operation(self, data: ScoreInput, config: ScoreConfig=None) -> ScoreOutput:
        """Score each candidate's semantic similarity to the query."""
        cfg = config or self.config or ScoreConfig()
        model = load_embedder(cfg.model)
        query = model.encode(data.query)
        candidates = model.encode(data.candidates)
        return ScoreOutput(scores=self._similarity(query, candidates))

    def _similarity(self, query, candidates) -> List[float]:
        """Return similarity of the query embedding to each candidate embedding."""
        from sentence_transformers.util import cos_sim
        return cos_sim(query, candidates).flatten().tolist()
