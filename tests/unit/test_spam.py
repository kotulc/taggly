"""Unit tests for the spam command."""

import math
from types import SimpleNamespace

import pytest

from taggly.commands.spam import SpamCommand, SpamInput, SpamParams


class _WordTokenizer:
    """Each word is one token; __call__ forwards the window text to the classifier stub."""

    def encode(self, text, add_special_tokens=False):
        return text.split()

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(ids)

    def __call__(self, text, **kwargs):
        return {"text": text}


def _logits_for(score):
    """Build 2-class logits whose softmax second element equals `score`."""
    import torch
    return torch.tensor([[0.0, math.log(score / (1 - score))]])


def _cmd(score_by_marker):
    """SpamCommand whose classifier scores a window by a marker substring."""
    cmd = SpamCommand()
    cmd._tokenizer = _WordTokenizer()
    calls = []

    def classifier(text=None, **kwargs):
        calls.append(text)
        score = next((s for marker, s in score_by_marker.items() if marker in text), 0.1)
        return SimpleNamespace(logits=_logits_for(score))

    cmd._classifier = classifier
    return cmd, calls


def test_short_input_scored_in_one_window():
    """Short text runs a single classifier call and returns its score."""
    cmd, calls = _cmd({"hello": 0.8})
    out = cmd.operation(SpamInput(content="hello world"))
    assert len(calls) == 1
    assert out.score == pytest.approx(0.8)
    assert out.tags == ["spam"]


def test_long_input_takes_max_score_across_windows():
    """Long text is chunked; the highest window score wins even if late in the text."""
    # >510 tokens forces multiple windows; the spam marker sits in the tail.
    words = [f"w{i}" for i in range(600)]
    words[595] = "SPAMMY"
    cmd, calls = _cmd({"SPAMMY": 0.97})
    out = cmd.operation(SpamInput(content=" ".join(words)), SpamParams(threshold=0.5))
    assert len(calls) >= 2  # did not crash / truncate to one window
    assert out.score == pytest.approx(0.97)
    assert out.tags == ["spam"]


def test_below_threshold_returns_no_tag():
    """Score under the threshold yields an empty tag list."""
    cmd, _ = _cmd({"hello": 0.2})
    out = cmd.operation(SpamInput(content="hello"), SpamParams(threshold=0.5))
    assert out.tags == []
