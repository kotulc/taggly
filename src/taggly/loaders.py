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


@lru_cache(maxsize=None)
def load_embedder(name: str):
    """Load and cache a SentenceTransformer by short name or full identifier."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODELS.get(name.lower(), name))


@lru_cache(maxsize=None)
def load_generator(name: str):
    """Load and cache a text-generation pipeline by short name or full identifier."""
    from transformers import pipeline
    from transformers import AutoTokenizer, AutoModelForMultimodalLM
    name = GEMMA_MODELS.get(name.lower(), name)
    tokenizer = AutoTokenizer.from_pretrained(name, clean_up_tokenization_spaces=False)
    model = AutoModelForMultimodalLM.from_pretrained(name)
    return pipeline("text-generation", model=model, tokenizer=tokenizer, clean_up_tokenization_spaces=False)
