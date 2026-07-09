# taggly

Taggly is a hyper extensible CLI-first NLP command framework. Add a command by implementing
one class — it is automatically registered as a CLI sub-command, an API endpoint, and a docs
page with no additional wiring.

### Features
- Auto command registration and docs generation
- Commands are automatically included as endpoints in the API
- Commands check for their active API server or fall back to local operation
- CLI and API mode with zero additional logic per command


## Installation

```bash
pip install -e .
```

## Commands

Commands separate **Config** (system-level, set at deploy time via `config/config.yaml`) from
**Params** (per-call, passed as CLI flags or API query params).

| Command | Description | Config (system) | Params (per-call) |
|---------|-------------|-----------------|-------------------|
| `keys`   | Keyword extraction | `model`, `language`, `dedup_*`, `stop_words`, `use_mmr` | `top_n`, `ngram_max` |
| `ents`   | Named entity extraction | `language` | `top_n` |
| `polar`  | Polarity sentiment analysis | `model` | — |
| `spam`   | Spam detection scoring | — | `threshold` |
| `tox`    | Toxicity scoring | — | `threshold` |
| `desc`   | Text description via a language model | `model`, `max_tokens` | — |
| `ext`    | Typed concept extraction via a language model | `model`, `max_tokens` | `concepts` |
| `score`  | Semantic similarity scores (cosine) | `model` | — |
| `rank`   | Maximal Marginal Relevance ranking | `model` | `top_n`, `diversity` |
| `topics` | Topic discovery via BERTopic | `model` | `top_n` |

Semantic commands (`score`, `rank`, `topics`) share embedding models — `all-minilm`,
`bge-base`, `bge-large`. Generative commands (`desc`, `ext`) use Gemma models —
`gemma-2b`, `gemma-4b`, `gemma-12b`.

Per-command reference docs are in [`docs/commands/`](docs/commands/); the framework design is
described in [`docs/framework.md`](docs/framework.md).

## Running as CLI

```bash
taggly --help
taggly keys --help

taggly keys "natural language processing is a subfield of AI"
# {"keywords": ["natural language processing", "subfield", "AI"]}

taggly keys "natural language processing" --top-n 5
# {"keywords": [...]}

taggly polar "I love this product!"
# {"tags": ["positive"], "scores": {"negative": 0.0, "neutral": 0.1, "positive": 0.9}}

taggly tox "You are amazing!"
# {"tags": [], "score": 0.02}

taggly score "machine learning" --candidates '["deep learning", "cooking", "neural networks"]'
# {"scores": [0.85, 0.12, 0.79]}

taggly ext "Python was created by Guido van Rossum at CWI."
# {"concepts": {"entities": ["Guido van Rossum", "CWI"], "topics": ["Python"], ...}}

taggly topics "Language models are changing AI." "BERT and GPT are key examples."
# {"topics": ["language", "models", "bert"]}
```

## Running as API

Start the server with the built-in `start` command (press Ctrl+C to stop):

```bash
taggly start
# Starting API server → http://127.0.0.1:8000  (Ctrl+C to stop)
```

The server starts at `http://127.0.0.1:8000`. Interactive docs: `http://127.0.0.1:8000/docs`

```bash
curl -X POST http://127.0.0.1:8000/keys \
  -H "Content-Type: application/json" \
  -d '{"content": "natural language processing is a subfield of AI"}'
# {"keywords": ["natural language processing", "subfield", "AI"]}

# Override Params per-request via query params:
curl -X POST "http://127.0.0.1:8000/keys?top_n=5" \
  -H "Content-Type: application/json" \
  -d '{"content": "natural language processing is a subfield of AI"}'
```

## API delegation

When a taggly API server is already running, CLI commands automatically delegate to it instead
of loading models locally. This avoids slow initialization on every CLI invocation.

```bash
# Terminal 1 — start the API
taggly start

# Terminal 2 — CLI auto-delegates; no local model load
taggly keys "natural language processing"  # → [keys] api
```

The CLI prints `[command] api` to stderr when a request is handled by the API server.

## Model warmup

Heavy models are loaded lazily on first use. Set `WARMUP` in `.env` to pre-load them at
startup so the first request is fast:

```bash
# .env
WARMUP='["keys", "ext", "score"]'
```

```bash
taggly start
# [keys] loading model...
# [ext] loading model...
# [score] loading model...
# All models loaded.
# Starting API server → http://127.0.0.1:8000  (Ctrl+C to stop)
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

If a model is unavailable, taggly reports it clearly:

- **API startup** — preflight probe loads every `WARMUP` model; aborts with exit code 1 if
  any fail so the server never starts in a half-broken state.
- **API requests** — return `503` with `{"detail": "<command> unavailable: ..."}`.
- **CLI** — prints `Error: <command> failed: ...` and exits with code 1.

## Generating docs

```bash
taggly docs
# docs/home.md, docs/commands/keys.md, docs/commands/ents.md, ...
```

## Configuration

### Server settings (`.env`)

Read from environment variables or a `.env` file in the project root.

| Variable         | Default     | Description                                    |
|------------------|-------------|------------------------------------------------|
| `MODE`           | `cli`       | `cli` or `api`                                 |
| `HOST`           | `127.0.0.1` | API server bind address                        |
| `PORT`           | `8000`      | API server port                                |
| `WARMUP`         | `[]`        | Command names to pre-load on API startup       |
| `HF_TOKEN`       | `""`        | HuggingFace token for downloading gated models |
| `API_TIMEOUT`    | `300.0`     | Read timeout for API delegation (seconds)      |
| `CONNECT_TIMEOUT`| `2.0`       | Connect timeout; fast-fails if server is down  |

### System config (`config/config.yaml`)

System-level **Config** defaults live in `config/config.yaml`. These are deployment-time
settings (which model to use, language settings, generation limits) that do not vary per
request. Edit `config/config.yaml` to change them without touching code:

```yaml
# config/config.yaml
keys:
  model: yake          # switch from keybert to yake for all requests

ext:
  model: gemma-4b      # upgrade to a larger model
  max_tokens: 512

score:
  model: bge-large     # use a higher-quality embedding model
```

Only **Config** fields belong in `config/config.yaml`. Per-call options (**Params**) like
`top_n`, `threshold`, and `concepts` are set per-request via CLI flags or API query params.

### Priority chains

```
Per-call:   CLI --flag  /  API ?query_param   →  Params field default
System:     config/config.yaml                →  Config field default
```

```bash
# Params: top_n is per-call — CLI flag overrides the default
taggly keys "machine learning" --top-n 3

# Config: model is system-level — set in config/config.yaml, not per-call
# config/config.yaml: keys: { model: yake }
taggly keys "machine learning"  # uses yake as configured
```
