# ents

Extract entities from the supplied text.

## Examples

**CLI**

```
taggly ents "Language models are transforming how we interact with text and data." --top-n 10
```

**API**

```bash
curl -X POST "http://localhost:8000/ents?top_n=10" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly ents [OPTIONS] CONTENT                                          
                                                                               
 Extract entities from the supplied text.                                      
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --top-n           INTEGER  Number of entities to extract [default: 10]      │
│ --language        TEXT     Language for spacy nlp model                     │
│                            [default: en_core_web_lg]                        │
│ --help                     Show this message and exit.                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /ents`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `top_n`, `language`

**Response**

```json
{
  "entities": [
    "..."
  ]
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `entities` | array[string] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `top_n` | integer | no | 10 | Number of entities to extract |
| `language` | string | no | en_core_web_lg | Language for spacy nlp model |
