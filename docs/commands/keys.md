# 'keys' Command

Extract keywords from the supplied text.

## Examples

**CLI**

```
taggly keys "Language models are transforming how we interact with text and data." --top-n 10
```

**API**

```bash
curl -X POST "http://localhost:8000/keys?top_n=10" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly keys [OPTIONS] CONTENT                                                                                                                                                     
                                                                                                                                                                                          
 Extract keywords from the supplied text.                                                                                                                                                 
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --top-n                          INTEGER  Maximum number of keywords to return [default: 10]                                                                                           │
│ --ngram-max                      INTEGER  Maximum n-gram size for keyword phrases [default: 1]                                                                                         │
│ --normalize    --no-normalize             Normalize candidates to lowercase [default: no-normalize]                                                                                    │
│ --help                                    Show this message and exit.                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /keys`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters**: `top_n`, `ngram_max`, `normalize`

**Response**

```json
{
  "keywords": [
    "..."
  ]
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | A text string to extract keywords from. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `keywords` | array[string] | yes | — | The list of extracted keywords. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | keybert | Extraction model: 'yake' or 'keybert' |
| `language` | string | no | en | Language code for YAKE stop-word filtering |
| `dedup_lim` | number | no | 0.9 | YAKE deduplication similarity threshold (0–1) |
| `dedup_func` | string | no | seqm | YAKE deduplication function: 'seqm', 'jaro', or 'levs' |
| `stop_words` | string | no | english | Stop-word list for KeyBERT ('english' or 'None') |
| `use_mmr` | boolean | no | False | Use Maximal Marginal Relevance for KeyBERT diversity |

## Params

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `top_n` | integer | no | 10 | Maximum number of keywords to return |
| `ngram_max` | integer | no | 1 | Maximum n-gram size for keyword phrases |
| `normalize` | boolean | no | False | Normalize candidates to lowercase |
