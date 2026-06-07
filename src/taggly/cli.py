"""Builds a Typer CLI app from a command registry."""

import inspect
from typing import Annotated

import typer


def build_cli(registry) -> typer.Typer:
    """Create a Typer app with one sub-command per registry entry."""
    app = typer.Typer(name="taggly")

    for name, command in registry.items():
        app.command(name=name)(_make_command_func(command))

    return app


def _make_command_func(cmd):
    """
    Return a function whose signature Typer can introspect.

    Input fields  → positional arguments (typer.Argument).
    Config fields → --flag options (typer.Option) defaulting to env-resolved values.
    """
    params = []
    input_fields = set(cmd.Input.model_fields)
    config_fields = set(cmd.Config.model_fields) if cmd.Config is not None else set()

    for fname, field in cmd.Input.model_fields.items():
        default = inspect.Parameter.empty if field.is_required() else field.default
        params.append(inspect.Parameter(
            fname,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[field.annotation, typer.Argument()],
            default=default,
        ))

    if cmd.Config is not None:
        for fname, field in cmd.Config.model_fields.items():
            params.append(inspect.Parameter(
                fname,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Annotated[field.annotation, typer.Option(help=field.description or "")],
                default=getattr(cmd.config, fname),
            ))

    def wrapper(**kwargs):
        input_data = cmd.Input(**{k: v for k, v in kwargs.items() if k in input_fields})
        if cmd.Config is not None:
            config_data = cmd.config.model_copy(
                update={k: v for k, v in kwargs.items() if k in config_fields}
            )
            result = cmd.run(input_data, config_data)
        else:
            result = cmd.run(input_data)
        print(result)

    wrapper.__signature__ = inspect.Signature(params)
    wrapper.__doc__ = cmd.operation.__doc__
    return wrapper
