# 'spam' Command

Compute spam score for the supplied text.

## Examples

**CLI**

```
taggly spam "Language models are transforming how we interact with text and data." --threshold 0.5
```

**API**

```bash
curl -X POST "http://localhost:8000/spam?threshold=0.5" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly spam [OPTIONS] CONTENT                                          
                                                                               
 Compute spam score for the supplied text.                                     
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --threshold        FLOAT  The spam score threshold to assign a 'spam' label │
│                           [default: 0.5]                                    │
│ --help                    Show this message and exit.                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /spam`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `threshold`

**Response**

```json
{
  "tags": [
    "..."
  ],
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
| `tags` | array[string] | yes | — | — |
| `score` | number | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `threshold` | number | no | 0.5 | The spam score threshold to assign a 'spam' label |
