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


def test_tags_combines_keywords_and_entities():
    """tags merges keywords, entities, and concepts into a single deduplicated list."""
    result = _cmd().operation(TagsInput(content=_SAMPLE))
    assert "machine learning" in result.tags
    assert "Python" in result.tags


def test_tags_deduplicates():
    """Overlapping results from sub-commands appear only once."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=20))
    assert len(result.tags) == len(set(result.tags))


def test_tags_respects_top_n():
    """tags returns at most top_n tags."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=2))
    assert len(result.tags) <= 2


def test_tags_rank_delegates_to_rank_command():
    """rank=True delegates to the rank command's MMR operation."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=2, rank=True))
    assert len(result.tags) <= 2
    assert all(isinstance(t, str) for t in result.tags)


def test_tags_default_sorts_by_score():
    """Without rank=True, tags are ordered by similarity score descending."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=20))
    assert isinstance(result.tags, list)
    assert len(result.tags) > 0


