"""Cached loaders for the embedding and generative models shared across commands."""

from functools import lru_cache

# Short names mapped to full sentence-transformers identifiers for similarity commands
EMBED_MODELS = {
    "all-minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "bge-base": "BAAI/bge-base-en-v1.5",
    "bge-large": "BAAI/bge-large-en-v1.5",
}

# Short names mapped to full Gemma instruct identifiers for generative commands
GEMMA_MODELS = {
    "gemma-2b": "google/gemma-4-E2B-it",
    "gemma-4b": "google/gemma-4-E4B-it",
    "gemma-12b": "google/gemma-4-12B-it",
}

# External LLM endpoint set at startup via set_llm_endpoint(); empty = use local models
_LLM_ENDPOINT: str = ""
_LLM_MODEL: str = ""


def set_llm_endpoint(endpoint: str, model: str = "") -> None:
    """Configure an external OpenAI-compatible LLM endpoint for load_generator."""
    global _LLM_ENDPOINT, _LLM_MODEL
    _LLM_ENDPOINT = endpoint
    _LLM_MODEL = model
    load_generator.cache_clear()


class _ExternalGenerator:
    """Calls an OpenAI-compatible /v1/chat/completions endpoint.

    Returns output in the same format as a transformers text-generation pipeline
    so callers (ext, desc) need no changes.
    """

    def __init__(self, endpoint: str, model: str):
        self._url = f"{endpoint.rstrip('/')}/v1/chat/completions"
        self._model = model

    def __call__(self, messages, generation_config=None, **kwargs):
        import httpx
        max_tokens = getattr(generation_config, "max_new_tokens", 256)
        chat = messages if isinstance(messages, list) else [{"role": "user", "content": messages}]
        response = httpx.post(
            self._url,
            json={"model": self._model, "messages": chat, "max_tokens": max_tokens},
            timeout=300.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(messages, list):
            return [{"generated_text": list(messages) + [{"role": "assistant", "content": content}]}]
        return [{"generated_text": content}]


@lru_cache(maxsize=None)
def load_embedder(name: str):
    """Load and cache a SentenceTransformer by short name or full identifier."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODELS.get(name.lower(), name))


@lru_cache(maxsize=None)
def load_generator(name: str):
    """Return a cached text-generation callable — external API if configured, local model otherwise."""
    if _LLM_ENDPOINT:
        model = _LLM_MODEL or name  # external APIs use their own model names, not GEMMA_MODELS
        return _ExternalGenerator(_LLM_ENDPOINT, model)
    from transformers import pipeline
    from transformers import AutoTokenizer, AutoModelForMultimodalLM
    hf_name = GEMMA_MODELS.get(name.lower(), name)
    tokenizer = AutoTokenizer.from_pretrained(hf_name, clean_up_tokenization_spaces=False)
    model = AutoModelForMultimodalLM.from_pretrained(hf_name)
    return pipeline("text-generation", model=model, tokenizer=tokenizer, clean_up_tokenization_spaces=False)
