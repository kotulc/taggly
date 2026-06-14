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
| `keys`   | Keyword extraction | `model`, `top_n`, `ngram_max`, `language`, `dedup_lim`, `dedup_func`, `stop_words`, `use_mmr` |
| `ents`   | Named entity extraction | `top_n`, `language` |
| `polar`  | Polarity sentiment analysis | `model` |
| `spam`   | Spam detection scoring | `threshold` |
| `tox`    | Toxicity scoring | `threshold` |
| `desc`   | Text description via a language model | `model`, `max_tokens` |
| `ext`    | Typed concept extraction via a language model | `model`, `concepts`, `max_tokens` |
| `score`  | Semantic similarity scores (cosine/dot) | `model`, `metric` |
| `rank`   | Maximal Marginal Relevance ranking | `model`, `top_n`, `diversity` |
| `topics` | Topic discovery via BERTopic | `model`, `top_n` |

Semantic commands (`score`, `rank`, `topics`) share embedding models — `all-minilm`,
`bge-base`, `bge-large`. Generative commands (`desc`, `ext`) share Gemma models —
`gemma-1b`, `gemma-4b`, `gemma-12b`.

Per-command reference docs are in [`docs/commands/`](docs/commands/); the framework design is
described in [`docs/framework.md`](docs/framework.md).

## Running as CLI

```bash
taggly --help
taggly keys --help

taggly keys "natural language processing is a subfield of AI"
# {"keywords": ["natural language processing", "subfield", "AI"]}

taggly keys "natural language processing" --model yake --top-n 5
# {"keywords": [...]}

taggly polar "I love this product!"
# {"tags": ["positive"], "scores": {"negative": 0.0, "neutral": 0.1, "positive": 0.9}}

taggly tox "You are amazing!"
# {"tags": [], "score": 0.02}
```

## Running as API

Start the server in the background with the built-in `start` command (and stop it with `stop`):

```bash
taggly start   # launches the API server in the background, writes .taggly.pid
taggly stop    # stops the running server
```

To run it in the foreground instead, set `MODE=api`:

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

## Model downloads

Models are downloaded automatically on first use (or at warmup) and cached locally. Gated
models such as Gemma (`desc`, `ext`) require accepting the model license on its HuggingFace
page and authenticating. Provide a token any of these ways:

```bash
# 1. Standard HuggingFace env var (read by transformers directly)
export HF_TOKEN=hf_xxx

# 2. A .env file in the project root
echo 'HF_TOKEN=hf_xxx' >> .env

# 3. The HuggingFace CLI login (writes to the shared cache)
hf auth login
```

If a model is unavailable (missing token, unaccepted license, or bad identifier), taggly
reports it clearly instead of dumping a traceback:

- **API startup** runs a preflight probe that loads every `WARMUP` model. If any fail, it
  prints the offending commands and aborts with exit code 1 — the server will not start in a
  half-broken state.
- **API requests** return `503` with a `{"detail": "<command> unavailable: ..."}` message.
- **CLI** prints `Error: <command> failed: ...` and exits with code 1.

Only the commands listed in `WARMUP` are probed at startup, so set it to the models a given
deployment actually requires.

## Generating docs

The built-in `docs` command writes a markdown reference file to `docs/commands/` for every
registered command, plus a `home.md` copied from this README:

```bash
taggly docs
# docs/home.md, docs/commands/keys.md, docs/commands/ents.md, ...
```

## Configuration

All settings are read from environment variables or a `.env` file in the project root.

| Variable   | Default     | Description                                        |
|------------|-------------|----------------------------------------------------|
| `MODE`     | `cli`       | `cli` or `api`                                     |
| `HOST`     | `127.0.0.1` | API server bind address                            |
| `PORT`     | `8000`      | API server port                                    |
| `COMMANDS` | `{}`        | Per-command config as JSON (see below)             |
| `WARMUP`   | `[]`        | Command names to pre-load on API startup           |
| `HF_TOKEN` | `""`        | HuggingFace token for downloading gated models     |

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

The names `docs`, `start`, and `stop` are reserved for the built-in CLI commands; a discovered
command using one of those names is skipped with a warning.

### Adding commands

Create a `.py` file in `src/taggly/commands/` — it is auto-discovered on next run.

```python
from pydantic import BaseModel, Field
from taggly.models.base import AbstractBaseCommand


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
