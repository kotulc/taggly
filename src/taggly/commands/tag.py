"""tag command: Extract a list of tags from the supplied text sorted by relevance."""

from typing import Dict, List
from pydantic import BaseModel, Field

from taggly.commands.ent import EntCommand, EntInput, EntParams
from taggly.commands.ext import ExtCommand, ExtInput, ExtParams
from taggly.commands.key import KeyCommand, KeyConfig, KeyInput, KeyParams
from taggly.commands.rank import RankCommand, RankInput, RankParams
from taggly.commands.score import ScoreCommand, ScoreInput
from taggly.models.base import AbstractBaseCommand


class TagParams(BaseModel):
    concepts: str = Field("concepts, entities, topics", description="Comma-separated tag groups to extract")
    max_ngram: int = Field(2, description="Maximum candidate tag word length")
    top_n: int = Field(10, description="Maximum number of tags to return per concept tag group")
    rank: bool = Field(False, description="Include a 'ranked' tag group listing all tags ranked with MMR")
    score: bool = Field(False, description="Include a 'scored' tag group listing all tags by relevance (descending)")
    normalize: bool = Field(True, description="Normalize candidates to lowercase")


class TagInput(BaseModel):
    content: str = Field(..., description="A text string to extract tags from")


class TagOutput(BaseModel):
    tags: Dict[str, List[str]] = Field(
        ..., description="Typed tag groups from each source plus a combined 'scored' or 'ranked' list"
    )


class TagCommand(AbstractBaseCommand):
    name = "tag"
    Params = TagParams
    Input = TagInput
    Output = TagOutput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._key = KeyCommand(config=KeyConfig(model="yake"))
        self._ent = EntCommand()
        self._ext = ExtCommand()
        self._rank = RankCommand()
        self._score = ScoreCommand()

    def operation(self, data: TagInput, params: TagParams=None) -> TagOutput:
        """Extract typed tag groups and a combined relevance-sorted list."""
        p = params or TagParams()

        # Start with ext concepts dict (entities, topics, concepts, …)
        ext_params = ExtParams(concepts=p.concepts, max_ngram=p.max_ngram, normalize=p.normalize)
        output = dict(self._ext.operation(ExtInput(content=data.content), ext_params).concepts)

        # Merge ent named entities into the entities group, deduplicated
        ent_params = EntParams(top_n=p.top_n, max_ngram=p.max_ngram, normalize=p.normalize)
        ent = self._ent.operation(EntInput(content=data.content), ent_params).entities
        output["entities"] = list(dict.fromkeys(output.get("entities", []) + ent))

        # Add keyword group
        key_params = KeyParams(top_n=p.top_n, ngram_max=p.max_ngram, normalize=p.normalize)
        output["keywords"] = self._key.operation(KeyInput(content=data.content), key_params).keywords

        # Combine all unique values for scoring or ranking
        all_tags = list(dict.fromkeys(v for vals in output.values() for v in vals))

        if p.rank and all_tags:
            rank_params = RankParams(top_n=p.top_n)
            output["ranked"] = self._rank.operation(RankInput(query=data.content, candidates=all_tags), rank_params).ranked

        if p.score and all_tags:
            scores = self._score.operation(ScoreInput(query=data.content, candidates=all_tags)).scores
            output["scored"] = [t for _, t in sorted(zip(scores, all_tags), reverse=True)][:p.top_n]

        return TagOutput(tags=output)
