# 'tags' Command

Extract a unified ranked list of tags combining keywords and named entities.

## Examples

**CLI**

```
taggly tags "Language models are transforming how we interact with text and data." --max-ngram 2
```

**API**

```bash
curl -X POST "http://localhost:8000/tags?max_ngram=2" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly tags [OPTIONS] CONTENT                                          
                                                                               
 Extract a unified ranked list of tags combining keywords and named entities.  
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --max-ngram                 INTEGER  Maximum candidate tag word length      │
│                                      [default: 2]                           │
│ --top-n                     INTEGER  Maximum number of tags to return       │
│                                      [default: 10]                          │
│ --rank         --no-rank             Rank candidates by MMR for relevance   │
│                                      and diversity                          │
│                                      [default: no-rank]                     │
│ --help                               Show this message and exit.            │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /tags`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `max_ngram`, `top_n`, `rank`

**Response**

```json
{
  "tags": [
    "..."
  ]
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | A text string to extract tags from |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tags` | array[string] | yes | — | Extracted tags in ranked order |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `max_ngram` | integer | no | 2 | Maximum candidate tag word length |
| `top_n` | integer | no | 10 | Maximum number of tags to return |
| `rank` | boolean | no | False | Rank candidates by MMR for relevance and diversity |
