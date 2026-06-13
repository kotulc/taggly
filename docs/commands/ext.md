# 'ext' Command

Extract typed concepts from the supplied text as a JSON object.

## Examples

**CLI**

```
taggly ext "Language models are transforming how we interact with text and data." --model gemma-1b
```

**API**

```bash
curl -X POST "http://localhost:8000/ext?model=gemma-1b" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly ext [OPTIONS] CONTENT                                           
                                                                               
 Extract typed concepts from the supplied text as a JSON object.               
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model             TEXT     Generative model: 'gemma-1b', 'gemma-4b', or   │
│                              'gemma-12b'                                    │
│                              [default: gemma-1b]                            │
│ --concepts          TEXT     Concept categories to extract                  │
│                              [default: entities, topics, relations]         │
│ --max-tokens        INTEGER  Maximum number of tokens to generate           │
│                              [default: 256]                                 │
│ --help                       Show this message and exit.                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /ext`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `model`, `concepts`, `max_tokens`

**Response**

```json
{
  "concepts": {}
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concepts` | dict[str, array[string]] | yes | — | Extracted concepts grouped by category |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | gemma-1b | Generative model: 'gemma-1b', 'gemma-4b', or 'gemma-12b' |
| `concepts` | array[string] | no | ['entities', 'topics', 'relations'] | Concept categories to extract |
| `max_tokens` | integer | no | 256 | Maximum number of tokens to generate |
