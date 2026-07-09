"""Generate markdown command reference docs to the /docs folder."""

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

_SAMPLE = "Language models are transforming how we interact with text and data."


def generate_docs(registry, cli_app, output_dir: Path = None) -> None:
    """Write one .md file per registered command to output_dir."""
    out = Path(output_dir or "docs")
    out.mkdir(exist_ok=True)
    runner = CliRunner()

    readme = Path("README.md")
    if readme.exists():
        shutil.copy2(readme, out / "about.md")
        print("  docs/about.md")

    cmds_dir = out / "commands"
    cmds_dir.mkdir(exist_ok=True)
    for name, cmd in registry.items():
        path = cmds_dir / f"{name}.md"
        path.write_text(_doc(name, cmd, runner, cli_app), encoding="utf-8")
        print(f"  docs/commands/{name}.md")


def _doc(name: str, cmd, runner: CliRunner, cli_app) -> str:
    """Build the full markdown document for one command."""
    config_cls = getattr(cmd, "Config", None)
    params_cls = getattr(cmd, "Params", None)
    parts = [
        f"# '{name}' Command\n",
        f"{cmd.operation.__doc__.strip()}\n",
        _examples_section(name, cmd, params_cls),
        _cli_section(name, runner, cli_app),
        _api_section(name, cmd, params_cls),
        _schema_section("Input", cmd.Input),
        _schema_section("Output", cmd.Output),
    ]
    if config_cls is not None:
        parts.append(_schema_section("Config", config_cls))
    if params_cls is not None:
        parts.append(_schema_section("Params", params_cls))
    return "\n".join(parts)


def _examples_section(name: str, cmd, params_cls) -> str:
    """One CLI invocation and one curl call, using the first Params field as example."""
    cli_args = " ".join(
        f'"{_SAMPLE}"' if f.annotation is str else str(_example_val(s))
        for f, s in zip(
            cmd.Input.model_fields.values(),
            cmd.Input.model_json_schema().get("properties", {}).values(),
        )
    )
    body = json.dumps({
        k: (_SAMPLE if f.annotation is str else _example_val(s))
        for (k, f), s in zip(
            cmd.Input.model_fields.items(),
            cmd.Input.model_json_schema().get("properties", {}).values(),
        )
    })

    opt, param = "", ""
    if params_cls is not None:
        fname, field = next(iter(params_cls.model_fields.items()))
        val = field.default
        flag = f"--{fname.replace('_', '-')}"
        opt = f" --no-{fname.replace('_', '-')}" if val is False else f" {flag} {val}"
        param = f"?{fname}={str(val).lower() if isinstance(val, bool) else val}"

    return "\n".join([
        "## Examples\n",
        "**CLI**\n",
        f"```\ntaggly {name} {cli_args}{opt}\n```\n",
        "**API**\n",
        f"```bash\ncurl -X POST \"http://localhost:8000/{name}{param}\" \\\n"
        f"  -H \"Content-Type: application/json\" \\\n"
        f"  -d '{body}'\n```\n",
    ])


def _cli_section(name: str, runner: CliRunner, cli_app) -> str:
    """Capture the exact --help output from Typer for the CLI reference."""
    result = runner.invoke(cli_app, [name, "--help"])
    return f"## CLI\n\n```\n{result.output.strip()}\n```\n"


def _api_section(name: str, cmd, params_cls) -> str:
    """Build the API reference with example request and response JSON."""
    req = json.dumps(_example(cmd.Input), indent=2)
    res = json.dumps(_example(cmd.Output), indent=2)

    parts = [f"## API\n", f"`POST /{name}`\n", f"**Request**\n\n```json\n{req}\n```\n"]

    if params_cls is not None:
        param_names = ", ".join(f"`{k}`" for k in params_cls.model_fields)
        parts.append(f"**Query parameters**: {param_names}\n")

    parts.append(f"**Response**\n\n```json\n{res}\n```\n")
    return "\n".join(parts)


def _schema_section(title: str, model) -> str:
    """Build a field reference table from a Pydantic model's JSON schema."""
    schema = model.model_json_schema()
    props = schema.get("properties", {})
    required = set(schema.get("required", []))

    rows = [
        f"| `{k}` | {_type(v)} | {'yes' if k in required else 'no'}"
        f" | {v.get('default', '—')} | {v.get('description', '—')} |"
        for k, v in props.items()
    ]
    header = (
        f"## {title}\n\n"
        "| Field | Type | Required | Default | Description |\n"
        "|-------|------|----------|---------|-------------|"
    )
    return header + "\n" + "\n".join(rows) + "\n"


def _example(model) -> dict:
    """Generate a minimal example dict for a Pydantic model using schema defaults."""
    schema = model.model_json_schema()
    return {k: _example_val(v) for k, v in schema.get("properties", {}).items()}


def _example_val(fschema: dict):
    """Return a representative example value for a single field schema."""
    if "default" in fschema:
        return fschema["default"]
    t = fschema.get("type")
    if t == "string":  return "..."
    if t == "integer": return 0
    if t == "number":  return 0.0
    if t == "boolean": return False
    if t == "array":
        return [_example_val(fschema["items"])] if "items" in fschema else []
    return {}


def _type(fschema: dict) -> str:
    """Convert a JSON schema type entry to a concise readable string."""
    t = fschema.get("type")
    if t == "array":
        inner = fschema.get("items", {})
        return f"array[{_type(inner)}]" if inner else "array"
    if t == "object":
        extra = fschema.get("additionalProperties")
        if extra and extra is not True:
            return f"dict[str, {_type(extra)}]"
        return "dict"
    if t:
        return t
    if "anyOf" in fschema:
        non_null = [s for s in fschema["anyOf"] if s != {"type": "null"}]
        return " | ".join(_type(s) for s in non_null)
    if "$ref" in fschema:
        return fschema["$ref"].split("/")[-1]
    return "any"
