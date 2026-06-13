# Framework Philosophy

Taggly is a **CLI-first, config-driven NLP framework**. Its goal is to let you add a new
language task once and get a command-line tool, an HTTP endpoint, and reference docs from
that single definition — with no wiring, registration, or boilerplate in between.

## One definition, three surfaces

Every capability is a single `AbstractBaseCommand` subclass declaring four things:

| Member | Purpose |
|--------|---------|
| `name` | The command/endpoint identifier |
| `Input` | A Pydantic model of the request payload |
| `Output` | A Pydantic model of the result |
| `Config` | A Pydantic model of tunable options (optional) |

From those models the framework derives, automatically:

- a **CLI sub-command** — `Input` fields become positional arguments, `Config` fields become `--flags`
- an **API endpoint** — `POST /{name}` with `Input` as the JSON body and `Config` fields as query parameters
- **reference docs** — schemas, help text, and examples generated from the models and docstrings

Adding a `.py` file to `src/taggly/commands/` is the *entire* registration step. Discovery
walks the directory, finds every `AbstractBaseCommand` subclass, and exposes it everywhere.

## Convention over configuration

The Pydantic models *are* the contract. Field types drive CLI argument parsing, API
validation, and documentation alike, so the schema never drifts from the three surfaces.
A field's `description` is its CLI help, its API doc, and its docs-table entry — written once.

This is why **types matter more than logic**: when a value doesn't fit the CLI/API surface,
change the field type rather than adding special-case handling to the framework. The framework
stays small; the commands stay declarative.

## Lazy by default, fast when it counts

NLP models are expensive to load. Taggly keeps the framework cheap to import by deferring
every heavy dependency (`transformers`, `sentence-transformers`, `bertopic`, `spacy`, …) to
inside the method that needs it. Command discovery, CLI help, and docs generation never touch
a model.

- **`warmup()`** lets a command pre-load its model so the first real request isn't slow.
- Shared models live in [`loaders.py`](../src/taggly/loaders.py) behind cached loaders, so
  `score`, `rank`, and `topics` reuse one embedding model instance rather than each loading
  their own.

## Per-call configuration with a clear priority

Config is resolved fresh on every call, never baked into a cached model. The priority chain is:

```
CLI --flag  /  API ?query_param   >   COMMANDS env var   >   Config field default
```

The cached object is only the heavy model; all tunables flow through the effective `Config`
for that single invocation. The same request can ask for a different model or threshold each
time without reloading anything it doesn't have to.

## Run anywhere, delegate automatically

The same registry powers both modes with no extra logic:

- **CLI mode** — run a command directly; the model loads locally.
- **API mode** — `taggly start` runs the server; commands become endpoints.

When a server is already running, the CLI **delegates** to it instead of loading models
locally, then falls back silently to local execution if the server is unreachable. One
codebase, two deployment shapes, zero duplicated handling.

## Composability

Commands are deliberately small and single-purpose so they compose into pipelines. This is
what lets downstream projects (e.g. [graphly](https://github.com/kotulc/graphly)) build a
document knowledge graph by chaining taggly primitives:

- `keys` / `ents` / `ext` — extract candidate tags and typed concepts
- `score` — measure semantic similarity for clustering and node weighting
- `rank` — select diverse, representative members per cluster via MMR
- `topics` / `desc` — summarize clusters and the document as a whole

Each command does one thing, exposes it identically across CLI and API, and stays out of the
way of the next one in the chain. That is the whole framework: **minimal core, declarative
commands, three surfaces for free.**
