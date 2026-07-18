"""Unit tests for ext command concept generation and parsing."""

import pytest

import taggly.commands.ext as ext_mod
from taggly.commands.ext import ExtCommand, ExtInput, ExtParams


@pytest.fixture
def cmd():
    return ExtCommand()


def test_operation_parses_generated_json(cmd, monkeypatch):
    """operation returns the parsed JSON groups for each requested concept."""
    monkeypatch.setattr(ext_mod, "generate", lambda *a: '{"entities": ["Alice"], "topics": []}')
    out = cmd.operation(ExtInput(content="Alice."), ExtParams(concepts="entities, topics"))
    assert out.concepts == {"entities": ["Alice"], "topics": []}


@pytest.mark.parametrize("text,expected", [
    ('{"entities": ["Alice"]}', {"entities": ["Alice"], "topics": []}),
    ('prefix {"entities": ["Alice"]} suffix', {"entities": ["Alice"], "topics": []}),
    ("not json at all", {"entities": [], "topics": []}),
    ('{"entities": [{"name": "Alice"}], "topics": "misc"}', {"entities": [], "topics": []}),
])
def test_parse_json(cmd, text, expected):
    """_parse extracts requested keys from model output, defaulting to empty lists."""
    assert cmd._parse(text, ["entities", "topics"]) == expected


@pytest.mark.parametrize("max_ngram,expected", [
    (1, {"Alice", "New", "United"}),
    (2, {"Alice", "New York", "United States"}),
    (3, {"Alice", "New York", "United States of"}),
])
def test_operation_truncates_candidates_over_max_ngram(cmd, monkeypatch, max_ngram, expected):
    """operation trims candidates longer than max_ngram words instead of dropping them."""
    generated = '{"entities": ["Alice", "New York", "United States of"]}'
    monkeypatch.setattr(ext_mod, "generate", lambda *a: generated)
    out = cmd.operation(ExtInput(content="..."), ExtParams(concepts="entities", max_ngram=max_ngram))
    assert set(out.concepts["entities"]) == expected


def test_operation_dedupes_after_truncation(cmd, monkeypatch):
    """candidates that collide after truncation are merged into one entry."""
    generated = '{"entities": ["New York", "New York City"]}'
    monkeypatch.setattr(ext_mod, "generate", lambda *a: generated)
    out = cmd.operation(ExtInput(content="..."), ExtParams(concepts="entities", max_ngram=2))
    assert out.concepts["entities"] == ["New York"]
