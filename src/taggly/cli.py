"""Builds a Typer CLI app from a command registry."""

import inspect
import os
import sys
from typing import Annotated

import typer


def build_cli(registry, config=None) -> typer.Typer:
    """Create a Typer app with one sub-command per registry entry plus reserved commands."""
    app = typer.Typer(name="taggly")

    for name, command in registry.items():
        app.command(name=name)(_make_command_func(command))

    _add_reserved(app, registry, config)
    return app


def _make_command_func(cmd):
    """
    Return a function whose signature Typer can introspect.

    Input fields  → positional arguments (typer.Argument).
    Params fields → --flag options (typer.Option) with class-level defaults.
    Config is system-level and not exposed as CLI flags.
    """
    params_cls = getattr(cmd, "Params", None)
    input_fields = set(cmd.Input.model_fields)
    param_fields = set(params_cls.model_fields) if params_cls else set()
    default_params = params_cls() if params_cls else None

    sig_params = []

    for fname, field in cmd.Input.model_fields.items():
        default = inspect.Parameter.empty if field.is_required() else field.default
        sig_params.append(inspect.Parameter(
            fname,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Annotated[field.annotation, typer.Argument()],
            default=default,
        ))

    if params_cls is not None:
        for fname, field in params_cls.model_fields.items():
            sig_params.append(inspect.Parameter(
                fname,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=Annotated[field.annotation, typer.Option(help=field.description or "")],
                default=getattr(default_params, fname),
            ))

    def wrapper(**kwargs):
        input_data = cmd.Input(**{k: v for k, v in kwargs.items() if k in input_fields})
        params_data = params_cls(**{k: v for k, v in kwargs.items() if k in param_fields}) if params_cls else None
        try:
            result = cmd.run(input_data, params_data)
        except Exception as e:
            typer.echo(f"Error: {cmd.name} failed: {e}", err=True)
            raise typer.Exit(1)
        print(result)

    wrapper.__signature__ = inspect.Signature(sig_params)
    wrapper.__doc__ = cmd.operation.__doc__
    return wrapper


def _add_reserved(app: typer.Typer, registry, config) -> None:
    """Register the built-in docs and start commands."""

    @app.command("docs")
    def _docs():
        """Generate markdown reference docs to docs/ for each registered command."""
        from taggly.docs import generate_docs
        print("Generating docs...")
        generate_docs(registry, app)

    @app.command("start")
    def _start():
        """Start the taggly API server (foreground — press Ctrl+C to stop)."""
        import uvicorn
        from taggly.api import build_api
        from taggly.main import _probe

        host = config.host if config else "127.0.0.1"
        port = config.port if config else 8000
        warmup = config.warmup if config else []

        if config and config.hf_token:
            os.environ["HF_TOKEN"] = config.hf_token

        api = build_api(registry)
        _probe(registry, warmup)
        typer.echo(f"Starting API server → http://{host}:{port}  (Ctrl+C to stop)")
        uvicorn.run(api, host=host, port=port)
