# Framework Philosophy

Taggly is a **CLI-first, config-driven NLP framework**. Its goal is to let you add a new
language task once and get a command-line tool, an HTTP endpoint, and reference docs from
that single definition — with no wiring, registration, or boilerplate in between.

## One definition, three surfaces

Every capability is a single `AbstractBaseCommand` subclass declaring up to six things:

| Member | Purpose |
|--------|---------|
| `name` | The command/endpoint identifier |
| `Input` | Pydantic model of the request payload (positional CLI args, API request body) |
| `Output` | Pydantic model of the result |
| `Config` | Pydantic model of **system-level** settings — loaded once from `config/config.yaml` |
| `Params` | Pydantic model of **per-call** options — CLI `--flags` and API `?query_params` |
| `warmup()` | Optional: pre-load heavy models at server startup |

From those declarations the framework derives, automatically:

- a **CLI sub-command** — `Input` fields → positional arguments, `Params` fields → `--flags`
- an **API endpoint** — `POST /{name}` with `Input` as the JSON body, `Params` as query params
- **reference docs** — schemas, examples, and help text generated from the models and docstrings

Adding a `.py` file to `src/taggly/commands/` is the *entire* registration step.

## Config vs Params

The split between `Config` and `Params` keeps deployment-time decisions separate from
request-time decisions:

| | `Config` | `Params` |
|--|----------|----------|
| **Set by** | `config/config.yaml` at deploy time | CLI flag or API query param per request |
| **Exposed as** | Not exposed to callers | `--flag` (CLI) / `?param=` (API) |
| **Typical fields** | Which model to load, language, generation limits | How many results, thresholds, filters |
| **Example** | `model: "gemma-4b"`, `language: "en"` | `top_n: 5`, `threshold: 0.8` |

Config fields are system-level decisions a deployment makes once. Params are per-call
options the user can override every request without restarting anything.

Commands that need neither declare neither — `spam` and `tox` have only `Params`, `score`
and `desc` have only `Config`, and commands like `keys` have both.

## Convention over configuration

The Pydantic models *are* the contract. Field types drive CLI argument parsing, API
validation, and documentation alike — the schema never drifts from the three surfaces.
A field's `description` is its CLI help text, its API doc, and its docs-table entry —
written once.

This is why **types matter more than logic**: when a value doesn't fit the CLI/API surface,
change the field type rather than adding special-case handling to the framework.

## Lazy by default, fast when it counts

NLP models are expensive to load. Taggly keeps startup cheap by deferring every heavy
import to inside the method that first needs it. Command discovery, CLI help, and docs
generation never touch a model.

- **`warmup()`** lets a command pre-load its model so the first real request isn't slow.
- Shared models live in [`loaders.py`](../src/taggly/loaders.py) behind `@lru_cache`, so
  `score`, `rank`, `topics`, and `tags` all share one embedding model instance.

## Per-call options with a clear priority

Config and Params have separate priority chains:

```
System:   config/config.yaml  >  Config field default
Per-call: CLI --flag / API ?query_param  >  Params field default
```

Config is loaded once at startup and never changes within a session. Params are resolved
fresh on every call from the CLI flag or query param, falling back to the class default.

## Run anywhere, delegate automatically

The same registry powers both modes:

- **CLI mode** — run a command directly; the model loads locally.
- **API mode** — `taggly start` runs the server; commands become endpoints.

When a server is already running, the CLI delegates to it instead of loading models locally,
then falls back silently if the server is unreachable. One codebase, two deployment shapes,
zero duplicated handling.

## Composability

Commands are small, single-purpose, and compose into pipelines. The `tags` command is
an example orchestrator: it calls `keys`, `ents`, `ext`, `score`, and `rank` as first-class
objects — no special wiring, just method calls on the same command instances:

```python
class TagsCommand(AbstractBaseCommand):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keys = KeysCommand(config=KeysConfig(model="yake"))
        self._ents = EntsCommand()
        self._rank = RankCommand()
```

Each command does one thing, exposes it identically across CLI and API, and stays out of
the way of the next one. That is the whole framework: **minimal core, declarative commands,
three surfaces for free.**
