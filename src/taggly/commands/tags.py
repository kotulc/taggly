"""tags command: Extract a list of tags from the supplied text sorted by relevance."""

from typing import List
from pydantic import BaseModel, Field

from taggly.commands.ents import EntsCommand, EntsInput, EntsParams
from taggly.commands.ext import ExtCommand, ExtInput
from taggly.commands.keys import KeysCommand, KeysConfig, KeysInput, KeysParams
from taggly.commands.rank import RankCommand, RankInput, RankParams
from taggly.commands.score import ScoreCommand, ScoreInput
from taggly.models.base import AbstractBaseCommand


class TagsParams(BaseModel):
    max_ngram: int = Field(2, description="Maximum candidate tag word length")
    top_n: int = Field(10, description="Maximum number of tags to return")
    rank: bool = Field(False, description="Rank candidates by MMR for relevance and diversity")


class TagsInput(BaseModel):
    content: str = Field(..., description="A text string to extract tags from")


class TagsOutput(BaseModel):
    tags: List[str] = Field(..., description="Extracted tags in ranked order")


class TagsCommand(AbstractBaseCommand):
    name = "tags"
    Params = TagsParams
    Input = TagsInput
    Output = TagsOutput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keys = KeysCommand(config=KeysConfig(model="yake"))
        self._ents = EntsCommand()
        self._ext = ExtCommand()
        self._rank = RankCommand()
        self._score = ScoreCommand()

    def operation(self, data: TagsInput, params: TagsParams=None) -> TagsOutput:
        """Extract a unified ranked list of tags combining keywords and named entities."""
        p = params or TagsParams()

        # Extract candidate tags from each command class
        candidates = self._keys.operation(
            KeysInput(content=data.content), 
            KeysParams(top_n=p.top_n * 2, ngram_max=p.max_ngram)
        ).keywords

        candidates += self._ents.operation(
            EntsInput(content=data.content), 
            EntsParams(top_n=p.top_n * 2)
        ).entities

        concepts = self._ext.operation(ExtInput(content=data.content)).concepts
        for concept_list in concepts.values():
            candidates.extend(concept_list)

        # Filter candidates to unique results only
        candidates = list(set(candidates))

        # Optionally rank candidates via MMR
        if p.rank and candidates:
            return TagsOutput(tags=self._rank.operation(
                RankInput(query=data.content, candidates=candidates),
                RankParams(top_n=p.top_n),
            ).ranked)
        else:
            scores = self._score.operation(
                ScoreInput(query=data.content, candidates=candidates)
            ).scores
            return TagsOutput(
                tags=[t for _, t in sorted(zip(scores, candidates), reverse=True)][:p.top_n]
            )
