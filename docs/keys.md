# keys

Extract keywords from the supplied text.

## Examples

**CLI**

```
taggly keys "Language models are transforming how we interact with text and data." --model keybert
```

**API**

```bash
curl -X POST "http://localhost:8000/keys?model=keybert" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly keys [OPTIONS] CONTENT                                          
                                                                               
 Extract keywords from the supplied text.                                      
                                                                               
┌─ Arguments ─────────────────────────────────────────────────────────────────┐
│ *    content      TEXT  [required]                                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Options ───────────────────────────────────────────────────────────────────┐
│ --model                         TEXT     Extraction model to use: 'yake' or │
│                                          'keybert'                          │
│                                          [default: keybert]                 │
│ --top-n                         INTEGER  Number of keywords to extract      │
│                                          [default: 3]                       │
│ --ngram-max                     INTEGER  Maximum n-gram size for keyword    │
│                                          phrases                            │
│                                          [default: 1]                       │
│ --language                      TEXT     Language code for YAKE stop-word   │
│                                          filtering                          │
│                                          [default: en]                      │
│ --dedup-lim                     FLOAT    YAKE deduplication similarity      │
│                                          threshold (0–1)                    │
│                                          [default: 0.9]                     │
│ --dedup-func                    TEXT     YAKE deduplication function (seqm, │
│                                          jaro, or levs)                     │
│                                          [default: seqm]                    │
│ --stop-words                    TEXT     Stop-word list for KeyBERT         │
│                                          ('english' or None)                │
│                                          [default: english]                 │
│ --use-mmr       --no-use-mmr             Use Maximal Marginal Relevance for │
│                                          KeyBERT diversity                  │
│                                          [default: no-use-mmr]              │
│ --help                                   Show this message and exit.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

## API

`POST /keys`

**Request**

```json
{
  "content": "..."
}
```

**Query parameters** (override config defaults): `model`, `top_n`, `ngram_max`, `language`, `dedup_lim`, `dedup_func`, `stop_words`, `use_mmr`

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
| `content` | string | yes | — | — |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `keywords` | array[string] | yes | — | — |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | keybert | Extraction model to use: 'yake' or 'keybert' |
| `top_n` | integer | no | 3 | Number of keywords to extract |
| `ngram_max` | integer | no | 1 | Maximum n-gram size for keyword phrases |
| `language` | string | no | en | Language code for YAKE stop-word filtering |
| `dedup_lim` | number | no | 0.9 | YAKE deduplication similarity threshold (0–1) |
| `dedup_func` | string | no | seqm | YAKE deduplication function (seqm, jaro, or levs) |
| `stop_words` | string | no | english | Stop-word list for KeyBERT ('english' or None) |
| `use_mmr` | boolean | no | False | Use Maximal Marginal Relevance for KeyBERT diversity |
