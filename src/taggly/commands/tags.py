"""tags command: Extract a list of tags from the supplied text sorted by relevance."""

from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.commands.ents import EntsCommand, EntsInput, EntsParams
from taggly.commands.ext import ExtCommand, ExtInput
from taggly.commands.keys import KeysCommand, KeysConfig, KeysInput, KeysParams
from taggly.commands.rank import RankCommand, RankInput, RankParams
from taggly.commands.score import ScoreCommand, ScoreInput
from taggly.models.base import AbstractBaseCommand


class TagsParams(BaseModel):
    max_ngram: int = Field(2, description="Maximum candidate tag word length")
    top_n: int = Field(10, description="Maximum number of tags to return per type")
    rank: bool = Field(False, description="Rank candidates by MMR for relevance and diversity")


class TagsInput(BaseModel):
    content: str = Field(..., description="A text string to extract tags from")


class TagsOutput(BaseModel):
    tags: Dict[str, List[str]] = Field(
        ..., description="Typed tag groups from each source plus a combined 'scored' or 'ranked' list"
    )


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
        """Extract typed tag groups and a combined relevance-sorted list."""
        p = params or TagsParams()

        # Start with ext concepts dict (entities, topics, concepts, …)
        output: Dict[str, List[str]] = dict(self._ext.operation(ExtInput(content=data.content)).concepts)

        # Merge ents named entities into the entities group, deduplicated
        ents = self._ents.operation(EntsInput(content=data.content), EntsParams(top_n=p.top_n)).entities
        output["entities"] = list(dict.fromkeys(output.get("entities", []) + ents))

        # Add keyword group
        output["keywords"] = self._keys.operation(
            KeysInput(content=data.content), KeysParams(top_n=p.top_n, ngram_max=p.max_ngram)
        ).keywords

        # Combine all unique values for scoring or ranking
        all_tags = list(dict.fromkeys(v for vals in output.values() for v in vals))

        if p.rank and all_tags:
            output["ranked"] = self._rank.operation(
                RankInput(query=data.content, candidates=all_tags), RankParams(top_n=p.top_n)
            ).ranked
        elif all_tags:
            scores = self._score.operation(ScoreInput(query=data.content, candidates=all_tags)).scores
            output["scored"] = [t for _, t in sorted(zip(scores, all_tags), reverse=True)][:p.top_n]

        return TagsOutput(tags=output)
