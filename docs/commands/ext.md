# 'ext' Command

Extract typed concepts from the supplied text.

## Examples

**CLI**

```
taggly ext "Language models are transforming how we interact with text and data." --concepts concepts, entities, topics
```

**API**

```bash
curl -X POST "http://localhost:8000/ext?concepts=concepts, entities, topics" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly ext [OPTIONS] CONTENT                                           
                                                                               
 Extract typed concepts from the supplied text.                                
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --concepts                         TEXT  Comma-separated concept categories │
│                                          to extract (spaces around commas   │
│                                          are fine)                          │
│                                          [default: concepts, entities,      │
│                                          topics]                            │
│ --structured    --no-structured          Extract all concepts in one        │
│                                          structured JSON generation instead │
│                                          of one list generation per concept │
│                                          [default: no-structured]           │
│ --help                                   Show this message and exit.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /ext`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `concepts`, `structured`

**Response**

```json
{
  "concepts": {}
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | A text string to extract concepts from |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concepts` | dict[str, array[string]] | yes | — | Extracted concepts grouped by category |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | smollm-135m | Generative model: 'smollm-135m', 'gemma-2b', 'gemma-4b', or 'gemma-12b' |
| `max_tokens` | integer | no | 256 | Maximum number of tokens to generate |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concepts` | string | no | concepts, entities, topics | Comma-separated concept categories to extract (spaces around commas are fine) |
| `structured` | boolean | no | False | Extract all concepts in one structured JSON generation instead of one list generation per concept |
