# spam

Compute spam score for the supplied text.

## Examples

**CLI**

```
taggly spam "Language models are transforming how we interact with text and data."
```

**API**

```bash
curl -X POST "http://localhost:8000/spam" \
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
│ --help          Show this message and exit.                                 │
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
