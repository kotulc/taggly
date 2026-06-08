# taggly

Taggly is a hyper extensible CLI-first config-driven NLP based tag extraction utility and application framework.

The intelligent application framework facilitates quickly adding and removing commands without any additional wiring or registration beyond simply implementing the `AbstractBaseCommand` class.

### Features
- Auto command registration and docs generation
- Commands are automatically included as endpoints in the API
- Commands check for their active endpoints or fallback to local operations
- The application can be run in both CLI or API mode with 0 additional logic


## Installation

```bash
pip install -e .
```

## Commands

| Command | Description | Config options |
|---------|-------------|----------------|
| `keys` | Keyword extraction | `model`, `top_n`, `ngram_max`, `language`, `dedup_lim`, `dedup_func`, `stop_words`, `use_mmr` |
| `ents` | Named entity extraction | `top_n`, `language` |
| `sent` | Sentiment analysis | `model` |
| `spam` | Spam detection scoring | — |
| `tox`  | Toxicity scoring | — |

Per-command reference docs are in [`docs/`](docs/).

## Running as CLI

```bash
taggly --help
taggly keys --help

taggly keys "natural language processing is a subfield of AI"
# {"keywords": ["natural language processing", "subfield", "AI"]}

taggly keys "natural language processing" --model yake --top-n 5
# {"keywords": [...]}

taggly sent "I love this product!"
# {"tag": "pos", "scores": {"neg": 0.0, "neu": 0.1, "pos": 0.9}}

taggly tox "You are amazing!"
# {"score": 0.02}
```

## Running as API

Set `MODE=api` and run `taggly`:

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

```bash
curl -X POST http://127.0.0.1:8000/keys \
  -H "Content-Type: application/json" \
  -d '{"content": "natural language processing is a subfield of AI"}'
# {"keywords": ["natural language processing", "subfield", "AI"]}

# Override config per-request via query params:
curl -X POST "http://127.0.0.1:8000/keys?model=yake&top_n=5" \
  -H "Content-Type: application/json" \
  -d '{"content": "natural language processing is a subfield of AI"}'
```

## API delegation

When a taggly API server is already running, CLI commands automatically delegate to it instead of loading models locally. This avoids slow initialization on every CLI invocation.

```bash
# Terminal 1 — start the API
MODE=api taggly

# Terminal 2 — CLI auto-delegates; no local model load
taggly keys "natural language processing"  # → [keys] api
```

The CLI prints `[command] api` or `[command] local` to stderr so you can always see which path was taken.

## Model warmup

Heavy models (transformers, spacy, etc.) are loaded lazily on first use. Use `WARMUP` to pre-load them at API startup so the first request is fast:

**Linux / macOS**
```bash
WARMUP='["keys", "ents"]' MODE=api taggly
```

**Windows (PowerShell)**
```powershell
$env:WARMUP = '["keys", "ents"]'
$env:MODE = "api"
taggly
```

## Generating docs

`MODE=docs` writes a markdown reference file to `docs/` for every registered command:

```bash
MODE=docs taggly
# docs/keys.md, docs/ents.md, docs/sent.md, docs/spam.md, docs/tox.md
```

## Configuration

All settings are read from environment variables or a `.env` file in the project root.

| Variable   | Default     | Description                                        |
|------------|-------------|----------------------------------------------------|
| `MODE`     | `cli`       | `cli`, `api`, or `docs`                            |
| `HOST`     | `127.0.0.1` | API server bind address                            |
| `PORT`     | `8000`      | API server port                                    |
| `COMMANDS` | `{}`        | Per-command config as JSON (see below)             |
| `WARMUP`   | `[]`        | Command names to pre-load on API startup           |

### Configuration priority

```
CLI --flag / API ?query_param  >  COMMANDS env var  >  Config field default
```

```bash
# 1. Config field default (top_n=3):
taggly keys "natural language processing"

# 2. COMMANDS env var overrides the default (top_n=10):
COMMANDS='{"keys": {"top_n": 10}}' taggly keys "natural language processing"

# 3. Per-call --flag overrides the env var (top_n=1):
COMMANDS='{"keys": {"top_n": 10}}' taggly keys "natural language processing" --top-n 1
```

The same priority applies to the API via query params:

```bash
COMMANDS='{"keys": {"top_n": 10}}' MODE=api taggly

curl -X POST "http://127.0.0.1:8000/keys?top_n=1" \
  -H "Content-Type: application/json" \
  -d '{"content": "natural language processing"}'
```

## Extensions

Taggly implements a modular command framework. Drop a module into `src/taggly/commands/` and it is automatically registered as both a CLI sub-command and an API endpoint — with no wiring required.

### Adding commands

Create a `.py` file in `src/taggly/commands/` — it is auto-discovered on next run.

```python
from pydantic import BaseModel, Field
from taggly.base import AbstractBaseCommand


class GreetInput(BaseModel):
    name: str


class GreetOutput(BaseModel):
    message: str


class GreetConfig(BaseModel):
    greeting: str = Field("Hello", description="Word to prepend to the name")


class GreetCommand(AbstractBaseCommand):
    name = "greet"
    Input = GreetInput
    Output = GreetOutput
    Config = GreetConfig  # omit if the command needs no config

    def operation(self, data: GreetInput, config: GreetConfig = None) -> GreetOutput:
        """Greet someone by name."""
        cfg = config or self.config or GreetConfig()
        return GreetOutput(message=f"{cfg.greeting}, {data.name}!")
```

Commands with expensive initialization (large models) should override `warmup()`:

```python
def warmup(self) -> None:
    if self._model is None:
        import heavy_library
        self._model = heavy_library.load(...)
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
