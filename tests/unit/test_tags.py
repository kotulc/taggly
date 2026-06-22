"""Unit tests for the tags command."""

from taggly.commands.tags import TagsCommand, TagsInput, TagsParams
from taggly.commands.keys import KeysOutput
from taggly.commands.ents import EntsOutput
from taggly.commands.ext import ExtOutput
from taggly.commands.rank import RankOutput, RankParams
from taggly.commands.score import ScoreOutput

_SAMPLE = "Machine learning models process natural language and extract meaningful patterns."


class _StubKeys:
    def operation(self, data, params=None):
        return KeysOutput(keywords=["machine learning", "natural language", "patterns"])


class _StubEnts:
    def operation(self, data, params=None):
        return EntsOutput(entities=["Python", "machine learning"])


class _StubExt:
    def operation(self, data, params=None):
        return ExtOutput(concepts={"entities": ["Python"], "topics": ["NLP"], "concepts": []})


class _StubRank:
    def operation(self, data, params=None):
        p = params or RankParams()
        return RankOutput(ranked=list(data.candidates)[:p.top_n])


class _StubScore:
    def operation(self, data, params=None):
        return ScoreOutput(scores=[0.9 - i * 0.1 for i in range(len(data.candidates))])


def _cmd():
    cmd = TagsCommand()
    cmd._keys = _StubKeys()
    cmd._ents = _StubEnts()
    cmd._ext = _StubExt()
    cmd._rank = _StubRank()
    cmd._score = _StubScore()
    return cmd


def test_tags_returns_typed_groups():
    """tags output contains typed groups: keywords, entities, topics, and scored."""
    result = _cmd().operation(TagsInput(content=_SAMPLE))
    assert "keywords" in result.tags
    assert "entities" in result.tags
    assert "topics" in result.tags
    assert "scored" in result.tags


def test_tags_keywords_populated():
    """keywords group is populated from the keys command."""
    result = _cmd().operation(TagsInput(content=_SAMPLE))
    assert "machine learning" in result.tags["keywords"]


def test_tags_entities_merged():
    """entities from ents and ext are merged and deduplicated."""
    result = _cmd().operation(TagsInput(content=_SAMPLE))
    entities = result.tags["entities"]
    assert "Python" in entities
    assert entities.count("Python") == 1  # deduplicated


def test_tags_scored_is_combined_sorted_list():
    """scored contains all unique tags sorted by relevance score."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=20))
    assert isinstance(result.tags["scored"], list)
    assert len(result.tags["scored"]) > 0
    assert "ranked" not in result.tags


def test_tags_rank_produces_ranked_not_scored():
    """rank=True produces a 'ranked' key via MMR, not 'scored'."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=3, rank=True))
    assert "ranked" in result.tags
    assert "scored" not in result.tags
    assert len(result.tags["ranked"]) <= 3


def test_tags_top_n_limits_scored():
    """top_n caps the combined scored list."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=2))
    assert len(result.tags["scored"]) <= 2
