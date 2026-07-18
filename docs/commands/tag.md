# 'tag' Command

Extract typed tag groups and a combined relevance-sorted list.

## Examples

**CLI**

```
taggly tag "Language models are transforming how we interact with text and data." --concepts concepts, entities, topics
```

**API**

```bash
curl -X POST "http://localhost:8000/tag?concepts=concepts, entities, topics" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly tag [OPTIONS] CONTENT                                                                                                                                                                   
                                                                                                                                                                                                       
 Extract typed tag groups and a combined relevance-sorted list.                                                                                                                                        
                                                                                                                                                                                                       
┌─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                                                                                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ --concepts                       TEXT     Comma-separated tag groups to extract [default: concepts, entities, topics]                                                                               │
│ --max-ngram                      INTEGER  Maximum candidate tag word length [default: 2]                                                                                                            │
│ --top-n                          INTEGER  Maximum number of tags to return per concept tag group [default: 10]                                                                                      │
│ --rank         --no-rank                  Include a 'ranked' tag group listing all tags ranked with MMR [default: no-rank]                                                                          │
│ --score        --no-score                 Include a 'scored' tag group listing all tags by relevance (descending) [default: no-score]                                                               │
│ --normalize    --no-normalize             Normalize candidates to lowercase [default: normalize]                                                                                                    │
│ --help                                    Show this message and exit.                                                                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /tag`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `concepts`, `max_ngram`, `top_n`, `rank`, `score`, `normalize`

**Response**

```json
{
  "tags": {}
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | A text string to extract tags from |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tags` | dict[str, array[string]] | yes | — | Typed tag groups from each source plus a combined 'scored' or 'ranked' list |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `concepts` | string | no | concepts, entities, topics | Comma-separated tag groups to extract |
| `max_ngram` | integer | no | 2 | Maximum candidate tag word length |
| `top_n` | integer | no | 10 | Maximum number of tags to return per concept tag group |
| `rank` | boolean | no | False | Include a 'ranked' tag group listing all tags ranked with MMR |
| `score` | boolean | no | False | Include a 'scored' tag group listing all tags by relevance (descending) |
| `normalize` | boolean | no | True | Normalize candidates to lowercase |
