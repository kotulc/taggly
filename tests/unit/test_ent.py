"""Unit tests for the ent command."""

from types import SimpleNamespace

import pytest

from taggly.commands.ent import EntCommand, EntInput, EntParams


def _stub_spacy(texts):
    """Return a fake spaCy pipeline callable yielding entities with the given texts."""
    def spacy(content):
        return SimpleNamespace(ents=[SimpleNamespace(text=t) for t in texts])
    return spacy


@pytest.fixture
def cmd():
    command = EntCommand()
    command._spacy = _stub_spacy(["Alice", "New York", "United States of America"])
    return command


@pytest.mark.parametrize("max_ngram,expected", [
    (1, {"Alice", "New", "United"}),
    (2, {"Alice", "New York", "United States"}),
    (4, {"Alice", "New York", "United States of America"}),
])
def test_operation_truncates_entities_over_max_ngram(cmd, max_ngram, expected):
    """operation trims entities longer than max_ngram words instead of dropping them."""
    out = cmd.operation(EntInput(content="..."), EntParams(max_ngram=max_ngram, top_n=10))
    assert set(out.entities) == expected


def test_operation_dedupes_after_truncation():
    """entities that collide after truncation are merged into one entry."""
    cmd = EntCommand()
    cmd._spacy = _stub_spacy(["New York", "New York City"])
    out = cmd.operation(EntInput(content="..."), EntParams(max_ngram=2))
    assert out.entities == ["New York"]
