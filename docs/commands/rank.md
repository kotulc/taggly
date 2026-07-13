# 'rank' Command

Rank candidates by relevance to the query while maximizing diversity.

## Examples

**CLI**

```
taggly rank "Language models are transforming how we interact with text and data." ['...'] --top-n 3
```

**API**

```bash
curl -X POST "http://localhost:8000/rank?top_n=3" \
  -H "Content-Type: application/json" \
  -d '{"query": "Language models are transforming how we interact with text and data.", "candidates": ["..."]}'
```

## CLI

```
Usage: taggly rank [OPTIONS] QUERY CANDIDATES...                                                                                                                                         
                                                                                                                                                                                          
 Rank candidates by relevance to the query while maximizing diversity.                                                                                                                    
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    query           TEXT           [required]                                                                                                                                         │
│ *    candidates      CANDIDATES...  [required]                                                                                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --top-n            INTEGER  Number of candidates to return [default: 3]                                                                                                                │
│ --diversity        FLOAT    MMR diversity weight (0=pure relevance, 1=pure diversity) [default: 0.5]                                                                                   │
│ --help                      Show this message and exit.                                                                                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
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

**Query parameters**: `top_n`, `diversity`

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
| `query` | string | yes | — | The reference text to rank candidates against. |
| `candidates` | array[string] | yes | — | A list of candidate strings to rank by relevance. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ranked` | array[string] | yes | — | The list of strings ranked with MMR. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | all-minilm | Embedding model: 'all-minilm', 'bge-base', or 'bge-large' |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `top_n` | integer | no | 3 | Number of candidates to return |
| `diversity` | number | no | 0.5 | MMR diversity weight (0=pure relevance, 1=pure diversity) |
