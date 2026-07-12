# taggly

[![CI](https://github.com/kotulc/taggly/actions/workflows/ci.yml/badge.svg)](https://github.com/kotulc/taggly/actions/workflows/ci.yml)

Taggly is a hyper extensible CLI-first NLP command framework. Add a command by implementing
one class — it is automatically registered as a CLI sub-command, an API endpoint, and a docs
page with no additional wiring.

### Features
- Auto command registration and docs generation
- Commands are automatically included as endpoints in the API
- Commands check for their active API server or fall back to local operation
- CLI and API mode with zero additional logic per command


## Installation

Simply navigate to the cloned project folder and pip install the project:

```bash
pip install -e .
```

## Running with Docker

Every push to `main` runs the test suite and, when it passes, builds and publishes an image
to `ghcr.io/kotulc/taggly`. The image bundles all runtime models — `all-MiniLM-L6-v2`
(embeddings), spaCy `en_core_web_lg` (entities), and `SmolLM2-135M-Instruct` (generation) —
so the container works fully offline with no HuggingFace token:

```bash
docker run -p 8000:8000 ghcr.io/kotulc/taggly        # API server on :8000

docker run --rm ghcr.io/kotulc/taggly taggly keys "natural language processing"  # one-off CLI
```

In the image, `desc` and `ext` default to the bundled `smollm-135m` model, and
`HF_HUB_OFFLINE=1` serves the bundled models without probing huggingface.co. To use gated
Gemma models instead, re-enable downloads and mount a config with the desired models plus
your HF cache and token:

```bash
docker run -p 8000:8000 -e HF_HUB_OFFLINE=0 -v ./config:/app/config \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface -e HF_TOKEN ghcr.io/kotulc/taggly
```

To build locally (the `hf_token` build secret is optional — all bundled models are public,
a token only raises download rate limits):

```bash
docker build -t taggly .
docker build --secret id=hf_token,env=HF_TOKEN -t taggly .  # with a token
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
| `tags`   | Combined typed tag extraction from all sources | — | `concepts`, `max_ngram`, `top_n`, `rank` |

Semantic commands (`score`, `rank`, `topics`) share embedding models — `all-minilm`,
`bge-base`, `bge-large`. Generative commands (`desc`, `ext`) use Gemma models —
`gemma-2b`, `gemma-4b`, `gemma-12b` — or the compact ungated `smollm-135m`
(SmolLM2-135M-Instruct), which needs no HuggingFace token.

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
# docs/about.md, docs/commands/keys.md, docs/commands/ents.md, ...
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
| `LLM_ENDPOINT`   | `""`        | External LLM server URL (OpenAI-compatible)    |
| `LLM_MODEL`      | `""`        | Model name to use on the external LLM server   |

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

### Using an external language model

Generative commands (`desc`, `ext`) can use a remote language model via an OpenAI-compatible
endpoint instead of downloading and running a local Gemma model. This is useful for integrating
with hosted LLM services, local servers like LM Studio or Ollama, or internal proxies.

Set `LLM_ENDPOINT` and `LLM_MODEL` in `.env`:

```bash
# .env
LLM_ENDPOINT=http://127.0.0.1:1234
LLM_MODEL=lmstudio-model
```

Then `desc` and `ext` commands will POST to `{LLM_ENDPOINT}/v1/chat/completions` with the
specified model name. The endpoint must be compatible with OpenAI's chat-completions API
(request/response shape). This works with:

- **LM Studio** at `http://127.0.0.1:1234`
- **Ollama** in OpenAI-compatibility mode: `http://localhost:11434`
- **vLLM**, **llama.cpp**, **LM Studio**, **text-generation-webui**
- Internal proxies in front of hosted providers (OpenAI, Anthropic, etc.)

**Example with LM Studio:**

First, find your loaded model's identifier. In LM Studio, this is shown in the "Server" panel
or you can query `http://127.0.0.1:1234/v1/models` to see available models.

```bash
# .env
LLM_ENDPOINT=http://127.0.0.1:1234
LLM_MODEL=<your-lm-studio-model-id>
```

Replace `<your-lm-studio-model-id>` with the actual model identifier (e.g. `neural-chat-7b-v3-1`,
`mistral-7b-instruct`, etc. — whatever model you have loaded in LM Studio).

```bash
taggly desc "Python is a programming language"
# Uses your LM Studio model running locally instead of downloading Gemma

taggly ext "Alice works at Acme Corp." --concepts '["person", "company"]'
# Extraction via LM Studio model
```

**Note:** `LLM_ENDPOINT` must use an endpoint that does **not** require authentication (or has
auth handled by a proxy). There is no built-in API key / bearer token support yet. If you need
authenticated providers, set up a local proxy that injects credentials, or let us know and we
can add API key support.

If `LLM_ENDPOINT` is not set, `desc` and `ext` use the configured Gemma model (`config/config.yaml`
`desc.model` / `ext.model`) and download it locally on first use.

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
