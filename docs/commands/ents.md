# 'ents' Command

Extract named entities from the supplied text.

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
                                                                               
 Extract named entities from the supplied text.                                
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --top-n        INTEGER  Maximum number of entities to return [default: 10]  │
│ --help                  Show this message and exit.                         │
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

**Query parameters**: `top_n`

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
| `content` | string | yes | — | A text string to extract named entities from. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `entities` | array[string] | yes | — | The list of extracted entities. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `language` | string | no | en_core_web_lg | spaCy model name for entity extraction |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `top_n` | integer | no | 10 | Maximum number of entities to return |
