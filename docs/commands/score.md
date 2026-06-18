# 'score' Command

Score each candidate's semantic similarity to the query.

## Examples

**CLI**

```
taggly score "Language models are transforming how we interact with text and data." ['...']
```

**API**

```bash
curl -X POST "http://localhost:8000/score" \
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
│ --help          Show this message and exit.                                 │
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
| `query` | string | yes | — | The reference text to compare candidates against. |
| `candidates` | array[string] | yes | — | A list of candidate strings to score. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `scores` | array[number] | yes | — | Cosine similarity scores in the same order as candidates. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |
