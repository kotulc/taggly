"""Integration tests: verify all registered commands are valid, documented, CLI-callable, and API-reachable."""

from typing import get_args, get_origin

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from taggly.api import build_api
from taggly.base import AbstractBaseCommand
from taggly.cli import build_cli
from taggly.registry import discover_commands

REGISTRY = discover_commands()
CLI_RUNNER = CliRunner()
CLI_APP = build_cli(REGISTRY)
API_CLIENT = TestClient(build_api(REGISTRY))

COMMANDS = list(REGISTRY.items())

_DEFAULTS = {float: 1.0, int: 1, str: "x", bool: True}


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


@pytest.mark.parametrize("name,cmd", COMMANDS)
def test_api_endpoint(name, cmd):
    """POST /{name} returns 200 with valid body and Config fields as query params."""
    payload = _sample_input(cmd.Input)
    params = _sample_input(cmd.Config) if cmd.Config is not None else None
    response = API_CLIENT.post(f"/{name}", json=payload, params=params)
    assert response.status_code == 200, response.text
