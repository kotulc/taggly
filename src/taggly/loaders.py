"""Cached loaders for the embedding and generative models shared across commands."""

import re
from functools import lru_cache

# Qwen-style reasoning wrappers occasionally leak into the assistant reply.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

# Short names mapped to full sentence-transformers identifiers for similarity commands
EMBED_MODELS = {
    "all-minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "bge-base": "BAAI/bge-base-en-v1.5",
    "bge-large": "BAAI/bge-large-en-v1.5",
}

# Short names mapped to full instruct-model identifiers for generative commands
GEN_MODELS = {
    "gemma-2b": "google/gemma-4-E2B-it",
    "gemma-4b": "google/gemma-4-E4B-it",
    "gemma-12b": "google/gemma-4-12B-it",
    "qwen-0.8b": "Qwen/Qwen3.5-0.8B",
}

# Models that require accepting the HF license and an access token to download
GATED_MODELS = {"gemma-2b", "gemma-4b", "gemma-12b"}

# External LLM endpoint set at startup via set_llm_endpoint(); empty = use local models
_LLM_ENDPOINT: str = ""
_LLM_MODEL: str = ""
_LLM_TIMEOUT: float = 300.0


def set_llm_endpoint(endpoint: str, model: str = "", timeout: float = 300.0) -> None:
    """Configure an external OpenAI-compatible LLM endpoint for load_generator."""
    global _LLM_ENDPOINT, _LLM_MODEL, _LLM_TIMEOUT
    _LLM_ENDPOINT = endpoint
    _LLM_MODEL = model
    _LLM_TIMEOUT = timeout
    load_generator.cache_clear()


class _ExternalGenerator:
    """Calls an OpenAI-compatible /v1/chat/completions endpoint.

    Returns output in the same format as a transformers text-generation pipeline
    so callers (ext, desc) need no changes.
    """

    def __init__(self, endpoint: str, model: str, timeout: float = 300.0):
        self._url = f"{endpoint.rstrip('/')}/v1/chat/completions"
        self._model = model
        self._timeout = timeout

    def __call__(self, messages, generation_config=None, **kwargs):
        import httpx
        max_tokens = getattr(generation_config, "max_new_tokens", 256)
        chat = messages if isinstance(messages, list) else [{"role": "user", "content": messages}]
        response = httpx.post(
            self._url,
            json={"model": self._model, "messages": chat, "max_tokens": max_tokens},
            timeout=self._timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(messages, list):
            return [{"generated_text": list(messages) + [{"role": "assistant", "content": content}]}]
        return [{"generated_text": content}]


def generate(model: str, messages: list, max_tokens: int) -> str:
    """Run one greedy chat generation and return the assistant reply text.

    Greedy decoding (do_sample=False) keeps small models on-task; their default
    sampling settings tend to echo the prompt or ramble. Thinking mode is disabled
    so reasoning models don't burn the token budget before producing the answer.
    """
    from transformers import GenerationConfig
    config = GenerationConfig(max_new_tokens=max_tokens, do_sample=False)
    output = load_generator(model)(
        messages,
        generation_config=config,
        tokenizer_encode_kwargs={"enable_thinking": False},
    )
    result = output[0]["generated_text"]
    text = result[-1]["content"] if isinstance(result, list) else result
    return _THINK_BLOCK.sub("", text).strip()


def from_hub(loader, name: str, **kwargs):
    """Call a hub model loader cache-first so flaky networks can't break cached model loads."""
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity(hf_logging.CRITICAL)  # silence advisory model-load chatter (e.g. LOAD REPORT)
    try:
        return loader(name, local_files_only=True, **kwargs)
    except OSError:  # not fully cached — fetch from the hub
        return loader(name, **kwargs)


@lru_cache(maxsize=None)
def load_embedder(name: str):
    """Load and cache a SentenceTransformer by short name or full identifier."""
    from sentence_transformers import SentenceTransformer
    return from_hub(SentenceTransformer, EMBED_MODELS.get(name.lower(), name))


@lru_cache(maxsize=None)
def load_generator(name: str):
    """Return a cached text-generation callable — external API if configured, local model otherwise."""
    if _LLM_ENDPOINT:
        model = _LLM_MODEL or name  # external APIs use their own model names, not GEN_MODELS
        return _ExternalGenerator(_LLM_ENDPOINT, model, _LLM_TIMEOUT)
    from transformers import pipeline
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForMultimodalLM
    hf_name = GEN_MODELS.get(name.lower(), name)
    tokenizer = from_hub(AutoTokenizer.from_pretrained, hf_name, clean_up_tokenization_spaces=False)
    try:
        model = from_hub(AutoModelForCausalLM.from_pretrained, hf_name)
    except ValueError:  # multimodal models (e.g. gemma-4) are not registered as causal LMs
        model = from_hub(AutoModelForMultimodalLM.from_pretrained, hf_name)
    return pipeline("text-generation", model=model, tokenizer=tokenizer, clean_up_tokenization_spaces=False)
