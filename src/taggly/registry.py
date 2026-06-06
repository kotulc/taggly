"""Discovers and registers command classes from the commands directory."""

import importlib
import inspect
from pathlib import Path
from typing import Dict

from taggly.base import AbstractBaseCommand

# Root of the src/ layout — used to build dotted module paths.
_SRC_ROOT = Path(__file__).parent.parent


def discover_commands(commands_dir: Path | None = None, app_config=None) -> Dict[str, AbstractBaseCommand]:
    """
    Scan commands_dir for AbstractBaseCommand subclasses and return a name→instance map.

    If app_config is provided, each command's Config class is instantiated from
    app_config.commands[command.name] and passed to the command's __init__.
    """
    if commands_dir is None:
        commands_dir = Path(__file__).parent / "commands"

    if not commands_dir.exists():
        return {}

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
            raw = app_config.commands.get(cmd_name, {}) if (app_config and cmd_name) else {}
            cmd_config = obj.Config(**raw) if obj.Config is not None else None
            instance = obj(config=cmd_config)
            registry[instance.name] = instance

    return registry
