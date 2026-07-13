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
