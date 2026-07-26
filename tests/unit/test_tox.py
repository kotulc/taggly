"""Unit tests for the tox command."""

import pytest

from taggly.commands.tox import ToxCommand, ToxInput, ToxParams


class _WordTokenizer:
    """Each word is one token for deterministic window boundaries."""

    def encode(self, text, add_special_tokens=False):
        return text.split()

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(ids)


def _cmd(score_by_marker):
    """ToxCommand whose pipeline scores a window by a marker substring."""
    cmd = ToxCommand()
    cmd._tokenizer = _WordTokenizer()
    calls = []

    def pipe(text, **kwargs):
        calls.append((text, kwargs))
        score = next((s for marker, s in score_by_marker.items() if marker in text), 0.1)
        return [{"label": "toxic", "score": score}]

    cmd._pipe = pipe
    return cmd, calls


def test_short_input_scored_in_one_window():
    """Short text runs a single pipeline call and returns its score."""
    cmd, calls = _cmd({"hello": 0.9})
    out = cmd.operation(ToxInput(content="hello world"))
    assert len(calls) == 1
    assert out.score == pytest.approx(0.9)
    assert out.tags == ["toxic"]


def test_pipeline_called_with_truncation():
    """Each window is scored with truncation enabled as a crash safety net."""
    cmd, calls = _cmd({"hello": 0.9})
    cmd.operation(ToxInput(content="hello"))
    _, kwargs = calls[0]
    assert kwargs.get("truncation") is True
    assert kwargs.get("max_length") == 512


def test_long_input_takes_max_score_across_windows():
    """Long text is chunked; toxicity in the tail still flags the whole input."""
    words = [f"w{i}" for i in range(600)]
    words[595] = "TOXIC"
    cmd, calls = _cmd({"TOXIC": 0.95})
    out = cmd.operation(ToxInput(content=" ".join(words)), ToxParams(threshold=0.5))
    assert len(calls) >= 2  # did not crash / truncate to one window
    assert out.score == pytest.approx(0.95)
    assert out.tags == ["toxic"]


def test_below_threshold_returns_no_tag():
    """Score under the threshold yields an empty tag list."""
    cmd, _ = _cmd({"hello": 0.2})
    out = cmd.operation(ToxInput(content="hello"), ToxParams(threshold=0.5))
    assert out.tags == []
