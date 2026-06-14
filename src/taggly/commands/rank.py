"""rank command: Rank candidate strings by Maximal Marginal Relevance (MMR)."""

from typing import List
from pydantic import BaseModel, Field

from taggly.loaders import load_embedder
from taggly.models.base import AbstractBaseCommand


class RankConfig(BaseModel):
    model: str = Field("all-minilm", description="Embedding model: 'all-minilm', 'bge-base', or 'bge-large'")
    diversity: float = Field(0.5, description="MMR diversity weight (0=pure relevance, 1=pure diversity)")
    top_n: int = Field(10, description="Number of candidates to return")


class RankInput(BaseModel):
    query: str
    candidates: List[str]


class RankOutput(BaseModel):
    ranked: List[str]


class RankCommand(AbstractBaseCommand):
    name = "rank"
    Input = RankInput
    Output = RankOutput
    Config = RankConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else RankConfig()
        super().__init__(api_url, cfg)

    def warmup(self) -> None:
        """Pre-load the configured embedding model."""
        load_embedder((self.config or RankConfig()).model)

    def operation(self, data: RankInput, config: RankConfig=None) -> RankOutput:
        """Rank candidates by relevance to the query while maximizing diversity."""
        cfg = config or self.config or RankConfig()
        model = load_embedder(cfg.model)
        query = model.encode(data.query)
        candidates = model.encode(data.candidates)
        order = self._mmr(query, candidates, cfg.diversity, cfg.top_n)
        return RankOutput(ranked=[data.candidates[i] for i in order])

    def _mmr(self, query, candidates, diversity: float, top_n: int) -> List[int]:
        """Select candidate indices by Maximal Marginal Relevance."""
        from sentence_transformers.util import cos_sim
        relevance = cos_sim(query, candidates).flatten()
        pairwise = cos_sim(candidates, candidates)
        selected, remaining = [], list(range(len(candidates)))

        while remaining and len(selected) < top_n:
            def mmr_score(i):
                novelty = max((pairwise[i][j] for j in selected), default=0)
                return (1 - diversity) * relevance[i] - diversity * novelty

            best = max(remaining, key=mmr_score)
            selected.append(best)
            remaining.remove(best)

        return selected
