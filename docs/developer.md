# Development Guide

## Running with Docker

Every push to `main` runs the test suite and, when it passes, builds and publishes an image
to `ghcr.io/kotulc/taggly`. The image bundles all runtime models — `all-MiniLM-L6-v2`
(embeddings), spaCy `en_core_web_sm` (entities), and `Qwen3.5-0.8B` (generation) —
so the container works fully offline with no HuggingFace token:

```bash
docker run -p 8000:8000 ghcr.io/kotulc/taggly        # API server on :8000

docker run --rm ghcr.io/kotulc/taggly taggly key "natural language processing"  # one-off CLI
```

The image sets `HF_HUB_OFFLINE=1` to serve the bundled models without probing huggingface.co.
To use gated Gemma models instead, re-enable downloads and mount a config with the desired
models plus your HF cache and token:

```bash
docker run -p 8000:8000 -e HF_HUB_OFFLINE=0 -v ./config:/app/config \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface -e HF_TOKEN ghcr.io/kotulc/taggly
```

To build locally (all bundled models are public — no HF token required):

```bash
docker build -t taggly .
```


## Extensions

Drop a `.py` file into `src/taggly/commands/` — it is auto-discovered as both a CLI
sub-command and an API endpoint. The names `docs` and `start` are reserved.

```python
from pydantic import BaseModel, Field
from taggly.models.base import AbstractBaseCommand


class GreetConfig(BaseModel):
    style: str = Field("formal", description="Greeting style: 'formal' or 'casual'")


class GreetParams(BaseModel):
    greeting: str = Field("Hello", description="Word to use as the greeting")


class GreetInput(BaseModel):
    name: str = Field(..., description="Name to greet")


class GreetOutput(BaseModel):
    message: str = Field(..., description="The greeting message")


class GreetCommand(AbstractBaseCommand):
    name = "greet"
    Config = GreetConfig   # system-level: set in config/config.yaml
    Params = GreetParams   # per-call: CLI flag or API query param
    Input = GreetInput
    Output = GreetOutput

    def __init__(self, config: GreetConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else GreetConfig()

    def operation(self, data: GreetInput, params: GreetParams=None) -> GreetOutput:
        """Greet someone by name."""
        p = params or GreetParams()
        return GreetOutput(message=f"{p.greeting}, {data.name}!")
```

Commands with expensive initialization should override `warmup()` using `self._config`:

```python
def warmup(self) -> None:
    load_my_model(self._config.model)
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```
