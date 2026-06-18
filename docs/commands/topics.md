# 'topics' Command

Discover topic keywords across the supplied documents.

## Examples

**CLI**

```
taggly topics ['...'] --top-n 3
```

**API**

```bash
curl -X POST "http://localhost:8000/topics?top_n=3" \
  -H "Content-Type: application/json" \
  -d '{"documents": ["..."]}'
```

## CLI

```
Usage: taggly topics [OPTIONS] DOCUMENTS...                                   
                                                                               
 Discover topic keywords across the supplied documents.                        
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    documents      DOCUMENTS...  [required]                                │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --top-n        INTEGER  Maximum number of topic keywords to return          │
│                         [default: 3]                                        │
│ --help                  Show this message and exit.                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /topics`

**Request**

```json
{
  "documents": [
    "..."
  ]
}
```

**Query parameters**: `top_n`

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
| `documents` | array[string] | yes | — | Two or more document strings to extract topics from. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `topics` | array[string] | yes | — | Common topics shared between the supplied documents. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `top_n` | integer | no | 3 | Maximum number of topic keywords to return |
