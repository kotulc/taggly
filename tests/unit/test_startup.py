"""Unit tests for the startup model probe and LLM configuration checks."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from taggly.main import _check_llm, _probe


class _OkCommand:
    """Stub command whose model loads successfully."""
    def warmup(self):
        pass


class _BadCommand:
    """Stub command whose model fails to load."""
    def warmup(self):
        raise RuntimeError("model unavailable")


class _LlmCommand:
    """Stub generative command requiring an LLM source (gated model by default)."""
    requires_llm = True

    def __init__(self, model="gemma-2b"):
        self._config = SimpleNamespace(model=model)

    def warmup(self):
        pass


def _config(**kwargs):
    """Build a stub AppConfig with empty LLM settings unless overridden."""
    defaults = dict(warmup=["gen"], llm_endpoint="", llm_model="", hf_token="")
    return SimpleNamespace(**{**defaults, **kwargs})


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


def test_probe_warns_on_unknown_names(capsys):
    """_probe prints a warning naming warmup entries that are not registered commands."""
    _probe({}, ["missing"])
    err = capsys.readouterr().err
    assert "warning" in err and "missing" in err


def test_check_llm_ignores_non_llm_warmup():
    """_check_llm returns when no warmup command requires an LLM."""
    _check_llm({"a": _OkCommand()}, _config(warmup=["a"]))


def test_check_llm_aborts_without_llm_source(capsys):
    """_check_llm exits 1 when a gated-model command has no endpoint, model, or HF token."""
    with pytest.raises(SystemExit) as exc:
        _check_llm({"gen": _LlmCommand()}, _config())
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "LLM_ENDPOINT" in err and "HF_TOKEN" in err


def test_check_llm_passes_with_ungated_model():
    """_check_llm returns without a token when the configured model is not gated."""
    _check_llm({"gen": _LlmCommand(model="smollm-135m")}, _config())


def test_check_llm_requires_model_with_endpoint(capsys):
    """_check_llm exits 1 when LLM_ENDPOINT is set but LLM_MODEL is empty."""
    with pytest.raises(SystemExit) as exc:
        _check_llm({"gen": _LlmCommand()}, _config(llm_endpoint="http://localhost:1234"))
    assert exc.value.code == 1
    assert "LLM_MODEL" in capsys.readouterr().err


def test_check_llm_passes_with_endpoint_and_model():
    """_check_llm returns when both LLM_ENDPOINT and LLM_MODEL are configured."""
    _check_llm({"gen": _LlmCommand()}, _config(llm_endpoint="http://localhost:1234", llm_model="m"))


def test_check_llm_accepts_valid_hf_token():
    """_check_llm allows local model fallback when the HF token validates."""
    with patch("huggingface_hub.whoami", return_value={"name": "user"}):
        _check_llm({"gen": _LlmCommand()}, _config(hf_token="hf_valid"))


def test_check_llm_aborts_on_rejected_hf_token(capsys):
    """_check_llm exits 1 when huggingface.co rejects the HF token."""
    import httpx
    from huggingface_hub.errors import HfHubHTTPError
    response = httpx.Response(401, request=httpx.Request("GET", "https://huggingface.co"))
    error = HfHubHTTPError("401 Unauthorized", response=response)
    with patch("huggingface_hub.whoami", side_effect=error):
        with pytest.raises(SystemExit) as exc:
            _check_llm({"gen": _LlmCommand()}, _config(hf_token="hf_bogus"))
    assert exc.value.code == 1
    assert "HF_TOKEN" in capsys.readouterr().err


def test_check_llm_defers_token_check_when_offline():
    """_check_llm passes on network errors so cached models still work offline."""
    with patch("huggingface_hub.whoami", side_effect=ConnectionError("offline")):
        _check_llm({"gen": _LlmCommand()}, _config(hf_token="hf_valid"))
