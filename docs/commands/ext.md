# 'ext' Command

Extract typed concepts from the supplied text as a JSON object.

## Examples

**CLI**

```
taggly ext "Language models are transforming how we interact with text and data." --concepts concepts,entities,topics
```

**API**

```bash
curl -X POST "http://localhost:8000/ext?concepts=concepts,entities,topics" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly ext [OPTIONS] CONTENT                                           
                                                                               
 Extract typed concepts from the supplied text as a JSON object.               
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --concepts        TEXT  Comma-separated concept categories to extract       │
│                         [default: concepts,entities,topics]                 │
│ --help                  Show this message and exit.                         │
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

**Query parameters**: `concepts`

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
| `model` | string | no | gemma-2b | Generative model: 'gemma-2b', 'gemma-4b', or 'gemma-12b' |
| `max_tokens` | integer | no | 256 | Maximum number of tokens to generate |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concepts` | string | no | concepts,entities,topics | Comma-separated concept categories to extract |
