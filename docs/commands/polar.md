# 'polar' Command

Compute positive/neutral/negative polarity for the supplied text.

## Examples

**CLI**

```
taggly polar "Language models are transforming how we interact with text and data."
```

**API**

```bash
curl -X POST "http://localhost:8000/polar" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly polar [OPTIONS] CONTENT                                                                                                                                                    
                                                                                                                                                                                          
 Compute positive/neutral/negative polarity for the supplied text.                                                                                                                        
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /polar`

**Request**

```json
{
  "content": "..."
}
```

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
| `content` | string | yes | — | A text string to compute polarity sentiment for. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tags` | array[string] | yes | — | The dominant polarity label(s): 'positive', 'neutral', or 'negative'. |
| `scores` | dict[str, number] | yes | — | Polarity scores keyed by label. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | vader | Sentiment model: 'vader' or 'blob' |
