# tox

Compute toxicity score for the supplied text.

## Examples

**CLI**

```
taggly tox "Language models are transforming how we interact with text and data."
```

**API**

```bash
curl -X POST "http://localhost:8000/tox" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly tox [OPTIONS] CONTENT                                           
                                                                               
 Compute toxicity score for the supplied text.                                 
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --help          Show this message and exit.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /tox`

**Request**

```json
{
  "content": "..."
}
```

**Response**

```json
{
  "score": 0.0
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `score` | number | yes | — | — |
