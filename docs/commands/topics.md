# 'topics' Command

Discover topic keywords across the sentences of the supplied text.

## Examples

**CLI**

```
taggly topics "Language models are transforming how we interact with text and data." --model all-minilm
```

**API**

```bash
curl -X POST "http://localhost:8000/topics?model=all-minilm" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly topics [OPTIONS] CONTENT                                        
                                                                               
 Discover topic keywords across the sentences of the supplied text.            
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model        TEXT     Embedding model: 'all-minilm', 'bge-base', or       │
│                         'bge-large'                                         │
│                         [default: all-minilm]                               │
│ --top-n        INTEGER  Number of topic keywords to return [default: 10]    │
│ --help                  Show this message and exit.                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /topics`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `model`, `top_n`

**Response**

```json
{
  "topics": [
    "..."
  ]
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `topics` | array[string] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |
| `top_n` | integer | no | 10 | Number of topic keywords to return |
