# 'rank' Command

Rank candidates by relevance to the query while maximizing diversity.

## Examples

**CLI**

```
taggly rank "Language models are transforming how we interact with text and data." ['...'] --model all-minilm
```

**API**

```bash
curl -X POST "http://localhost:8000/rank?model=all-minilm" \
  -H "Content-Type: application/json" \
  -d '{"query": "Language models are transforming how we interact with text and data.", "candidates": ["..."]}'
```

## CLI

```
Usage: taggly rank [OPTIONS] QUERY CANDIDATES...                              
                                                                               
 Rank candidates by relevance to the query while maximizing diversity.         
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    query           TEXT           [required]                              │
│ *    candidates      CANDIDATES...  [required]                              │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model            TEXT     Embedding model: 'all-minilm', 'bge-base', or   │
│                             'bge-large'                                     │
│                             [default: all-minilm]                           │
│ --top-n            INTEGER  Number of candidates to return [default: 10]    │
│ --diversity        FLOAT    MMR diversity weight (0=pure relevance, 1=pure  │
│                             diversity)                                      │
│                             [default: 0.5]                                  │
│ --help                      Show this message and exit.                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /rank`

**Request**

```json
{
  "query": "...",
  "candidates": [
    "..."
  ]
}
```

**Query parameters** (override config defaults): `model`, `top_n`, `diversity`

**Response**

```json
{
  "ranked": [
    "..."
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
| `ranked` | array[string] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |
| `top_n` | integer | no | 10 | Number of candidates to return |
| `diversity` | number | no | 0.5 | MMR diversity weight (0=pure relevance, 1=pure diversity) |
