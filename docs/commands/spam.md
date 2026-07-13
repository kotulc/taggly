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
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --threshold        FLOAT  Spam probability threshold for assigning a 'spam' label [default: 0.5]                                                                                       │
│ --help                    Show this message and exit.                                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /spam`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `threshold`

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
| `content` | string | yes | — | A text string to score for spam. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tags` | array[string] | yes | — | Label list — contains 'spam' if the threshold is exceeded. |
| `score` | number | yes | — | Spam probability score from 0 to 1. |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `threshold` | number | no | 0.5 | Spam probability threshold for assigning a 'spam' label |
