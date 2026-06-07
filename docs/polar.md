# 'polar' Command

Compute positive/neutral/negative polarity for the supplied text.

## Examples

**CLI**

```
taggly polar "Language models are transforming how we interact with text and data." --model vader
```

**API**

```bash
curl -X POST "http://localhost:8000/polar?model=vader" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly polar [OPTIONS] CONTENT                                                                                                                                                  
                                                                                                                                                                                        
 Compute positive/neutral/negative polarity for the supplied text.                                                                                                                      
                                                                                                                                                                                        
╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --model        TEXT  Sentiment analysis model to use: 'vader' or 'blob' [default: vader]                                                                                             │
│ --help               Show this message and exit.                                                                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /polar`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `model`

**Response**

```json
{
  "tags": [
    "..."
  ],
  "scores": {}
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
| `scores` | dict[str, number] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | vader | Sentiment analysis model to use: 'vader' or 'blob' |
