# 'tags' Command

Extract typed tag groups and a combined relevance-sorted list.

## Examples

**CLI**

```
taggly tags "Language models are transforming how we interact with text and data." --concepts concepts, entities, topics
```

**API**

```bash
curl -X POST "http://localhost:8000/tags?concepts=concepts, entities, topics" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly tags [OPTIONS] CONTENT                                                                                                                                                     
                                                                                                                                                                                          
 Extract typed tag groups and a combined relevance-sorted list.                                                                                                                           
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --concepts                       TEXT     Comma-separated concept categories to extract [default: concepts, entities, topics]                                                          │
│ --max-ngram                      INTEGER  Maximum candidate tag word length [default: 2]                                                                                               │
│ --top-n                          INTEGER  Maximum number of tags to return per type [default: 10]                                                                                      │
│ --rank         --no-rank                  Rank candidates by MMR for relevance and diversity [default: no-rank]                                                                        │
│ --normalize    --no-normalize             Normalize candidates to lowercase [default: normalize]                                                                                       │
│ --help                                    Show this message and exit.                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /tags`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `concepts`, `max_ngram`, `top_n`, `rank`, `normalize`

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
| `concepts` | string | no | concepts, entities, topics | Comma-separated concept categories to extract |
| `max_ngram` | integer | no | 2 | Maximum candidate tag word length |
| `top_n` | integer | no | 10 | Maximum number of tags to return per type |
| `rank` | boolean | no | False | Rank candidates by MMR for relevance and diversity |
| `normalize` | boolean | no | True | Normalize candidates to lowercase |
