"""Builds a Typer CLI app from a command registry."""

import inspect
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

_PID_FILE = Path(".taggly.pid")


def _kill(pid: int) -> None:
    """Terminate a process by PID — taskkill on Windows (works for detached), SIGTERM elsewhere."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.kill(pid, signal.SIGTERM)


def _spawn(cmd: list, env: dict) -> subprocess.Popen:
    """Spawn a detached background process — platform-specific flags are isolated here."""
    kwargs = (
        {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    return subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)


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


def _add_reserved(app: typer.Typer, registry, config) -> None:
    """Register the built-in docs, start, and stop commands."""

    @app.command("docs")
    def _docs():
        """Generate markdown reference docs to docs/ for each registered command."""
        from taggly.docs import generate_docs
        print("Generating docs...")
        generate_docs(registry, app)

    @app.command("start")
    def _start():
        """Start the taggly API server in the background."""
        if _PID_FILE.exists():
            typer.echo("Server already running. Run 'taggly stop' first.")
            raise typer.Exit(1)
        proc = _spawn([sys.executable, "-m", "taggly.main"], {**os.environ, "MODE": "api"})
        _PID_FILE.write_text(str(proc.pid))
        host = config.host if config else "127.0.0.1"
        port = config.port if config else 8000
        typer.echo(f"API server started (pid {proc.pid}) → http://{host}:{port}")

    @app.command("stop")
    def _stop():
        """Stop the running taggly API server."""
        if not _PID_FILE.exists():
            typer.echo("No running server found (.taggly.pid missing).")
            raise typer.Exit(1)
        pid = int(_PID_FILE.read_text().strip())
        try:
            _kill(pid)
            typer.echo(f"API server (pid {pid}) stopped.")
        except (OSError, subprocess.CalledProcessError):
            typer.echo(f"Process {pid} not found — cleaned up stale .taggly.pid.")
        finally:
            _PID_FILE.unlink(missing_ok=True)
