"""Discovers and registers command classes from the commands directory."""

import importlib
import inspect
import sys
from pathlib import Path
from typing import Dict

import httpx

from taggly.models.base import AbstractBaseCommand

# Root of the src/ layout — used to build dotted module paths.
_SRC_ROOT = Path(__file__).parent.parent

# Names reserved for built-in CLI commands; user commands with these names are skipped.
_RESERVED = {"docs", "start"}


def discover_commands(commands_dir: Path=None, app_config=None) -> Dict[str, AbstractBaseCommand]:
    """Scan commands_dir for AbstractBaseCommand subclasses and return a name→instance map.

    Per-command defaults are read from config.yaml in the working directory. In CLI mode,
    each command is given an api_url if the API server is already running.
    """
    if commands_dir is None:
        commands_dir = Path(__file__).parent / "commands"

    if not commands_dir.exists():
        return {}

    api_base = _check_api(app_config)
    cmd_defaults = _load_config()
    registry = {}

    for file in commands_dir.rglob("*.py"):
        if file.name.startswith("_"):
            continue

        module_path = ".".join(file.relative_to(_SRC_ROOT).with_suffix("").parts)
        module = importlib.import_module(module_path)

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if not (issubclass(obj, AbstractBaseCommand) and obj is not AbstractBaseCommand):
                continue

            cmd_name = getattr(obj, "name", None)
            if cmd_name in _RESERVED:
                print(f"warning: '{cmd_name}' is a reserved command name, skipping.", file=sys.stderr)
                continue
            raw = cmd_defaults.get(cmd_name, {}) if cmd_name else {}
            cmd_config = obj.Config(**raw) if obj.Config is not None else None
            api_url = f"{api_base}/{cmd_name}" if (api_base and cmd_name) else None
            instance = obj(
                api_url=api_url,
                config=cmd_config,
                api_timeout=app_config.api_timeout if app_config else 300.0,
                connect_timeout=app_config.connect_timeout if app_config else 2.0,
            )
            registry[instance.name] = instance

    return registry


def _load_config() -> dict:
    """Load per-command defaults from config.yaml in the working directory."""
    import yaml
    path = Path("config.yaml")
    if not path.exists():
        return {}
    with path.open() as f:
        return yaml.safe_load(f) or {}


def _check_api(app_config) -> str | None:
    """Return the API base URL if it is reachable and this process is not the API server."""
    if not app_config or app_config.mode == "api":
        return None
    base = f"http://{app_config.host}:{app_config.port}"
    try:
        httpx.get(f"{base}/", timeout=1.0)
        return base
    except Exception:
        return None
