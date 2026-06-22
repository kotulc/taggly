"""Unit tests for the tags command."""

from taggly.commands.tags import TagsCommand, TagsInput, TagsParams
from taggly.commands.keys import KeysOutput
from taggly.commands.ents import EntsOutput
from taggly.commands.rank import RankOutput, RankParams

_SAMPLE = "Machine learning models process natural language and extract meaningful patterns."


class _StubKeys:
    def operation(self, data, params=None):
        return KeysOutput(keywords=["machine learning", "natural language", "patterns"])


class _StubEnts:
    def operation(self, data, params=None):
        return EntsOutput(entities=["Python", "machine learning"])


class _StubRank:
    def operation(self, data, params=None):
        p = params or RankParams()
        return RankOutput(ranked=list(data.candidates)[:p.top_n])


def _cmd():
    cmd = TagsCommand()
    cmd._keys, cmd._ents, cmd._rank = _StubKeys(), _StubEnts(), _StubRank()
    return cmd


def test_tags_combines_keywords_and_entities():
    """tags merges keywords and entities into a single deduplicated list."""
    result = _cmd().operation(TagsInput(content=_SAMPLE))
    assert "machine learning" in result.tags
    assert "Python" in result.tags


def test_tags_deduplicates():
    """Overlapping results from keys and ents appear only once."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=20))
    assert len(result.tags) == len(set(result.tags))


def test_tags_respects_top_n():
    """tags returns at most top_n tags."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=2))
    assert len(result.tags) <= 2


def test_tags_rank_delegates_to_rank_command():
    """rank=True delegates to the rank command and returns its ordered results."""
    result = _cmd().operation(TagsInput(content=_SAMPLE), TagsParams(top_n=2, rank=True))
    assert len(result.tags) <= 2
    assert all(isinstance(t, str) for t in result.tags)


def test_tags_ents_failure_is_silent():
    """An exception from ents is swallowed — tags still returns keywords."""
    class _BrokenEnts:
        def operation(self, data, params=None):
            raise RuntimeError("spaCy model not found")

    cmd = _cmd()
    cmd._ents = _BrokenEnts()
    result = cmd.operation(TagsInput(content=_SAMPLE))
    assert "machine learning" in result.tags
