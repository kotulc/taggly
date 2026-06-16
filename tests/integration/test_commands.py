"""Integration tests: verify all registered commands are valid, documented, CLI-callable, and API-reachable."""

import re
from typing import get_args, get_origin

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from taggly.api import build_api
from taggly.models.base import AbstractBaseCommand
from taggly.cli import build_cli
from taggly.registry import discover_commands

REGISTRY = discover_commands()
CLI_RUNNER = CliRunner()
CLI_APP = build_cli(REGISTRY)
API_CLIENT = TestClient(build_api(REGISTRY))

COMMANDS = list(REGISTRY.items())

_DEFAULTS = {float: 1.0, int: 1, str: "x", bool: True}
_SAMPLE = "This product is absolutely fantastic and works perfectly in every situation."
_PAIRS = ["language models are transforming AI", "neural networks learn rich representations"]


def _model_choices(cmd) -> list:
    """Extract quoted model names from the 'model' Config field description."""
    if cmd.Config is None or "model" not in cmd.Config.model_fields:
        return []
    desc = cmd.Config.model_fields["model"].description or ""
    return re.findall(r"'([^']+)'", desc)


MODEL_COMMANDS = [(n, c) for n, c in COMMANDS if len(_model_choices(c)) >= 2]


def _sample_input(model_class) -> dict:
    """Generate minimal valid input for a Pydantic model by field type."""
    data = {}
    for fname, field in model_class.model_fields.items():
        origin = get_origin(field.annotation)
        if origin is list:
            inner = get_args(field.annotation)[0]
            if inner in _DEFAULTS:
                data[fname] = [_DEFAULTS[inner]]
        elif field.annotation in _DEFAULTS:
            data[fname] = _DEFAULTS[field.annotation]
    return data


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_implements_base(name, cmd):
    """Command is a subclass of AbstractBaseCommand."""
    assert isinstance(cmd, AbstractBaseCommand)


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_has_docstring(name, cmd):
    """Command run method has a non-empty docstring."""
    doc = cmd.operation.__doc__
    assert doc and doc.strip(), f"{name}.run() is missing a docstring"


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_config_fields_have_descriptions(name, cmd):
    """Every Config field has a non-empty description for CLI help and API docs."""
    if cmd.Config is None:
        pytest.skip(f"{name} has no Config")
    for fname, field in cmd.Config.model_fields.items():
        assert field.description and field.description.strip(), (
            f"{name}.Config.{fname} is missing a Field description"
        )


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_cli_help(name, cmd):
    """CLI help contains the run docstring and Config fields as documented --options."""
    result = CLI_RUNNER.invoke(CLI_APP, [name, "--help"])
    assert result.exit_code == 0, result.output
    assert cmd.operation.__doc__.strip() in result.output

    if cmd.Config is not None:
        for fname in cmd.Config.model_fields:
            assert f"--{fname.replace('_', '-')}" in result.output


def _model_payload(cmd) -> dict:
    """Build a valid payload for test_model_config_respected, handling List[str] fields."""
    payload = {}
    for k, f in cmd.Input.model_fields.items():
        origin = get_origin(f.annotation)
        if f.annotation is str:
            payload[k] = _SAMPLE
        elif origin is list and get_args(f.annotation)[0] is str:
            payload[k] = _PAIRS  # two distinct strings so embeddings and topics can differ by model
        else:
            payload[k] = _DEFAULTS.get(f.annotation, 1)
    return payload


@pytest.mark.parametrize("name,cmd", MODEL_COMMANDS)
def test_model_config_respected(name, cmd):
    """Commands with a model config option return different output for different models."""
    choices = _model_choices(cmd)
    results = [
        API_CLIENT.post(f"/{name}", json=_model_payload(cmd), params={"model": m}).json()
        for m in choices[:2]
    ]
    assert results[0] != results[1], (
        f"{name}: model config ignored — '{choices[0]}' and '{choices[1]}' both returned {results[0]}"
    )


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_api_endpoint(name, cmd):
    """POST /{name} returns 200 with valid body and Config fields as query params."""
    payload = _sample_input(cmd.Input)
    params = _sample_input(cmd.Config) if cmd.Config is not None else None
    response = API_CLIENT.post(f"/{name}", json=payload, params=params)
    assert response.status_code == 200, response.text
