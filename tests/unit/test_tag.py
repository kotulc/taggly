"""Unit tests for the tag command."""

from taggly.commands.tag import TagCommand, TagInput, TagParams
from taggly.commands.key import KeyOutput
from taggly.commands.ent import EntOutput
from taggly.commands.ext import ExtOutput
from taggly.commands.rank import RankOutput, RankParams
from taggly.commands.score import ScoreOutput

_SAMPLE = "Machine learning models process natural language and extract meaningful patterns."


class _StubKey:
    def operation(self, data, params=None):
        return KeyOutput(keywords=["machine learning", "natural language", "patterns"])


class _StubEnt:
    def operation(self, data, params=None):
        return EntOutput(entities=["Python", "machine learning"])


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
    cmd = TagCommand()
    cmd._key = _StubKey()
    cmd._ent = _StubEnt()
    cmd._ext = _StubExt()
    cmd._rank = _StubRank()
    cmd._score = _StubScore()
    return cmd


def test_tag_returns_typed_groups():
    """tag output contains typed groups: keywords, entities, and topics."""
    result = _cmd().operation(TagInput(content=_SAMPLE))
    assert "keywords" in result.tags
    assert "entities" in result.tags
    assert "topics" in result.tags


def test_tag_omits_scored_and_ranked_by_default():
    """scored and ranked are opt-in — neither appears unless requested."""
    result = _cmd().operation(TagInput(content=_SAMPLE))
    assert "scored" not in result.tags
    assert "ranked" not in result.tags


def test_tag_keywords_populated():
    """keywords group is populated from the key command."""
    result = _cmd().operation(TagInput(content=_SAMPLE))
    assert "machine learning" in result.tags["keywords"]


def test_tag_entities_merged():
    """entities from ent and ext are merged and deduplicated."""
    result = _cmd().operation(TagInput(content=_SAMPLE))
    entities = result.tags["entities"]
    assert "Python" in entities
    assert entities.count("Python") == 1  # deduplicated


def test_tag_score_produces_scored():
    """score=True produces a 'scored' key with all unique tags sorted by relevance."""
    result = _cmd().operation(TagInput(content=_SAMPLE), TagParams(top_n=20, score=True))
    assert isinstance(result.tags["scored"], list)
    assert len(result.tags["scored"]) > 0
    assert "ranked" not in result.tags


def test_tag_rank_produces_ranked():
    """rank=True produces a 'ranked' key via MMR."""
    result = _cmd().operation(TagInput(content=_SAMPLE), TagParams(top_n=3, rank=True))
    assert "ranked" in result.tags
    assert "scored" not in result.tags
    assert len(result.tags["ranked"]) <= 3


def test_tag_rank_and_score_coexist():
    """rank=True and score=True together produce both 'ranked' and 'scored'."""
    result = _cmd().operation(TagInput(content=_SAMPLE), TagParams(rank=True, score=True))
    assert "ranked" in result.tags
    assert "scored" in result.tags


def test_tag_top_n_limits_scored():
    """top_n caps the combined scored list."""
    result = _cmd().operation(TagInput(content=_SAMPLE), TagParams(top_n=2, score=True))
    assert len(result.tags["scored"]) <= 2
