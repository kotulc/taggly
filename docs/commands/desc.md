# 'desc' Command

Generate a concise description of the supplied text.

## Examples

**CLI**

```
taggly desc "Language models are transforming how we interact with text and data."
```

**API**

```bash
curl -X POST "http://localhost:8000/desc" \
  -H "Content-Type: application/json" \
  -d '{"content": "Language models are transforming how we interact with text and data."}'
```

## CLI

```
Usage: taggly desc [OPTIONS] CONTENT                                                                                                                                                     
                                                                                                                                                                                          
 Generate a concise description of the supplied text.                                                                                                                                     
                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    content      TEXT  [required]                                                                                                                                                     │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## API

`POST /desc`

**Request**

```json
{
  "content": "..."
}
```

**Response**

```json
{
  "description": "..."
}
```

## Input

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | yes | — | A text string to generate a description from. |

## Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `description` | string | yes | — | The generated description. |

## Config

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | no | qwen-0.8b | Generative model: 'qwen-0.8b', 'gemma-2b', 'gemma-4b', or 'gemma-12b' |
| `max_tokens` | integer | no | 128 | Maximum number of tokens to generate |
