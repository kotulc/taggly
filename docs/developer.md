# Development Guide

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
