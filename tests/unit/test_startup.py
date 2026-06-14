"""Unit tests for the startup model probe."""

import pytest

from taggly.main import _probe


class _OkCommand:
    """Stub command whose model loads successfully."""
    def warmup(self):
        pass


class _BadCommand:
    """Stub command whose model fails to load."""
    def warmup(self):
        raise RuntimeError("model unavailable")


def test_probe_passes_when_models_load():
    """_probe returns normally when every warmup command loads."""
    _probe({"a": _OkCommand()}, ["a"])


def test_probe_aborts_when_model_fails(capsys):
    """_probe exits with code 1 and a friendly message when a model fails to load."""
    with pytest.raises(SystemExit) as exc:
        _probe({"a": _OkCommand(), "b": _BadCommand()}, ["a", "b"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "Startup aborted" in err
    assert "b: model unavailable" in err


def test_probe_skips_unknown_names():
    """_probe ignores warmup names that are not registered commands."""
    _probe({}, ["missing"])
