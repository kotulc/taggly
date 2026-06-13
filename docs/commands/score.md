# 'score' Command

Score each candidate's semantic similarity to the query.

## Examples

**CLI**

```
taggly score "Language models are transforming how we interact with text and data." ['...'] --model all-minilm
```

**API**

```bash
curl -X POST "http://localhost:8000/score?model=all-minilm" \
  -H "Content-Type: application/json" \
  -d '{"query": "Language models are transforming how we interact with text and data.", "candidates": ["..."]}'
```

## CLI

```
Usage: taggly score [OPTIONS] QUERY CANDIDATES...                             
                                                                               
 Score each candidate's semantic similarity to the query.                      
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    query           TEXT           [required]                              │
│ *    candidates      CANDIDATES...  [required]                              │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model         TEXT  Embedding model: 'all-minilm', 'bge-base', or         │
│                       'bge-large'                                           │
│                       [default: all-minilm]                                 │
│ --metric        TEXT  Similarity metric: 'cosine' or 'dot'                  │
│                       [default: cosine]                                     │
│ --help                Show this message and exit.                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /score`

**Request**

```json
{
  "query": "...",
  "candidates": [
    "..."
  ]
}
```

**Query parameters** (override config defaults): `model`, `metric`

**Response**

```json
{
  "scores": [
    0.0
  ]
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | yes | — | — |
| `candidates` | array[string] | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `scores` | array[number] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |
| `metric` | string | no | cosine | Similarity metric: 'cosine' or 'dot' |
