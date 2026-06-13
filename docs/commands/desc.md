# 'desc' Command

Generate a concise description of the supplied text.

## Examples

**CLI**

```
taggly desc "Language models are transforming how we interact with text and data." --model gemma-1b
```

**API**

```bash
curl -X POST "http://localhost:8000/desc?model=gemma-1b" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly desc [OPTIONS] CONTENT                                          
                                                                               
 Generate a concise description of the supplied text.                          
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model             TEXT     Generative model: 'gemma-1b', 'gemma-4b', or   │
│                              'gemma-12b'                                    │
│                              [default: gemma-1b]                            │
│ --max-tokens        INTEGER  Maximum number of tokens to generate           │
│                              [default: 128]                                 │
│ --help                       Show this message and exit.                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /desc`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `model`, `max_tokens`

**Response**

```json
{
  "description": "..."
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `description` | string | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | gemma-1b | Generative model: 'gemma-1b', 'gemma-4b', or 'gemma-12b' |
| `max_tokens` | integer | no | 128 | Maximum number of tokens to generate |
