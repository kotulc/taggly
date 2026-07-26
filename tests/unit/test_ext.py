"""Unit tests for ext command concept generation and parsing."""

import pytest

import taggly.commands.ext as ext_mod
from taggly.commands.ext import ExtCommand, ExtInput, ExtParams, _CHUNK_CHARS


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
    # Brace noise before the real object used to make index/rindex parsing fail.
    ('Here is {\"foo\": 1} then {"entities": ["Alice"], "topics": []}', {"entities": ["Alice"], "topics": []}),
    ('<think>why {braces}?</think>\n{"entities": ["Alice"], "topics": []}', {"entities": ["Alice"], "topics": []}),
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


def test_chunks_keeps_short_text_whole(cmd):
    """Text under the chunk limit is a single chunk."""
    assert cmd._chunks("short text") == ["short text"]


def test_chunks_splits_long_text(cmd):
    """Text above the chunk limit is split into bounded pieces."""
    # Build ~2.5 chunks of plain words so splits land on spaces.
    words = [f"word{i}" for i in range(500)]
    text = " ".join(words)
    assert len(text) > _CHUNK_CHARS
    chunks = cmd._chunks(text)
    assert len(chunks) >= 2
    assert all(len(c) <= _CHUNK_CHARS for c in chunks)
    assert "".join(chunks).replace(" ", "") == text.replace(" ", "")


def test_operation_chunks_long_input_and_merges(cmd, monkeypatch):
    """Long content is processed per chunk and results are merged across calls."""
    calls = []

    def fake_generate(model, messages, max_tokens):
        content = messages[0]["content"]
        calls.append(content)
        # Pull a marker embedded in each chunk's text.
        if "CHUNK_A" in content:
            return '{"entities": ["Alice"], "topics": ["alpha"]}'
        if "CHUNK_B" in content:
            return '{"entities": ["Bob"], "topics": ["beta"]}'
        return '{"entities": [], "topics": []}'

    monkeypatch.setattr(ext_mod, "generate", fake_generate)
    # Two chunks: pad so the break falls between the markers.
    pad = "x " * (_CHUNK_CHARS // 2)
    content = f"CHUNK_A start. {pad} CHUNK_B end."
    assert len(content) > _CHUNK_CHARS

    out = cmd.operation(ExtInput(content=content), ExtParams(concepts="entities, topics"))
    assert len(calls) >= 2
    assert "Alice" in out.concepts["entities"]
    assert "Bob" in out.concepts["entities"]
    assert "alpha" in out.concepts["topics"]
    assert "beta" in out.concepts["topics"]
