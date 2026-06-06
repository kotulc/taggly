# taggly

A CLI-first, config-driven command framework. Drop a module into `src/taggly/commands/` and it auto-registers as a CLI sub-command and (optionally) an API endpoint.

## Installation

```bash
pip install -e .
```

## Running as CLI

```bash
taggly --help
taggly add --help

taggly add 1.5 2.5
# {"result": 4.0}

taggly stats 1.0 2.0 3.0 4.0
# {"count": 4, "mean": 2.5, "min": 1.0, "max": 4.0}
```

## Running as API

Set `MODE=api` in your environment (or a `.env` file) and run `taggly`:

**Linux / macOS**
```bash
MODE=api taggly
```

**Windows (PowerShell)**
```powershell
$env:MODE = "api"
taggly
```

The server starts at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`

Call endpoints with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/add \
  -H "Content-Type: application/json" \
  -d '{"a": 1.5, "b": 2.5}'
# {"result": 4.0}

curl -X POST http://127.0.0.1:8000/stats \
  -H "Content-Type: application/json" \
  -d '{"values": [1.0, 2.0, 3.0, 4.0]}'
# {"count": 4, "mean": 2.5, "min": 1.0, "max": 4.0}
```

## Configuration

All settings are read from environment variables or a `.env` file in the project root.

| Variable   | Default       | Description                              |
|------------|---------------|------------------------------------------|
| `MODE`     | `cli`         | `cli` or `api`                           |
| `HOST`     | `127.0.0.1`   | API server bind address                  |
| `PORT`     | `8000`        | API server port                          |
| `COMMANDS` | `{}`          | Per-command config as JSON (see below)   |

### Configuration priority

Config values are resolved in this order — higher wins:

```
CLI --flag / API ?query_param  >  COMMANDS env var  >  Config field default
```

**Example using `add --precision`:**

```bash
# 1. Config field default (precision=2):
taggly add 1.1 2.22222
# {"result": 3.32}

# 2. COMMANDS env var overrides the default (precision=4):
COMMANDS='{"add": {"precision": 4}}' taggly add 1.1 2.22222
# {"result": 3.3222}

# 3. Per-call --flag overrides the env var (precision=1):
COMMANDS='{"add": {"precision": 4}}' taggly add 1.1 2.22222 --precision 1
# {"result": 3.3}
```

The same priority applies to the API — query params override the env-var defaults:

```bash
# COMMANDS env var sets precision=4, query param overrides to precision=1:
curl -X POST "http://127.0.0.1:8000/add?precision=1" \
  -H "Content-Type: application/json" \
  -d '{"a": 1.1, "b": 2.22222}'
# {"result": 3.3}
```

Config field descriptions are shown in `--help` output and in the interactive API docs at `/docs`.

### Setting env-var defaults

Pass per-command config via the `COMMANDS` env var as a JSON object keyed by command name:

```bash
COMMANDS='{"add": {"precision": 4}, "stats": {"round_digits": 3}}' taggly add 1.1 2.22222
# {"result": 3.3222}
```

**Windows (PowerShell)**
```powershell
$env:COMMANDS = '{"add": {"precision": 4}}'
taggly add 1.1 2.22222
```

## Adding commands

Create a module in `src/taggly/commands/` — it is auto-discovered on next run.

```python
from pydantic import BaseModel, Field
from taggly.base import AbstractBaseCommand


class GreetInput(BaseModel):
    name: str


class GreetOutput(BaseModel):
    message: str


class GreetConfig(BaseModel):
    # Each field needs a Field(description=...) — shown in --help and /docs.
    greeting: str = Field("Hello", description="Greeting word to prepend to the name")


class GreetCommand(AbstractBaseCommand):
    name = "greet"
    Input = GreetInput
    Output = GreetOutput
    Config = GreetConfig  # omit entirely if the command needs no config

    def run(self, data: GreetInput, config: GreetConfig | None = None) -> GreetOutput:
        """Greet someone by name."""
        cfg = config or self.config or GreetConfig()
        return GreetOutput(message=f"{cfg.greeting}, {data.name}!")
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
