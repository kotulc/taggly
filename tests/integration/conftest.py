"""Lightweight stubs replacing heavy ML models for fast integration testing."""

import importlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import taggly.commands
import taggly.loaders


class _FakeEmbedder:
    """Stub embedder — deterministic output per (model_name, text) pair."""
    DIM = 4

    def __init__(self, name: str):
        self._name = name

    def encode(self, texts):
        if isinstance(texts, str):
            seed = hash((self._name, texts)) % (2 ** 31)
            return np.random.RandomState(seed).rand(self.DIM).astype(np.float32)
        return np.vstack([self.encode(t) for t in texts]) if texts else np.zeros((0, self.DIM), np.float32)


class _FakeGenerator:
    """Stub generator — returns valid JSON so concept parsing doesn't silently fail."""

    def __init__(self, name: str):
        self._name = name

    def __call__(self, messages, generation_config=None, **kwargs):
        text = '{"entities":["stub"],"topics":["stub"],"concepts":["stub"]}'
        if isinstance(messages, list):
            return [{"generated_text": list(messages) + [{"role": "assistant", "content": text}]}]
        return [{"generated_text": text}]


class _FakeKeyBERT:
    """Stub KeyBERT — avoids loading sentence-transformers through the keybert side door."""
    def extract_keywords(self, content, top_n=5, **kwargs):
        return [("stub", 0.5)] * min(top_n, 1)


class _FakeClassifier:
    """Stub sequence classifier — fixed logits so spam scoring runs without a model download."""
    def __call__(self, **inputs):
        import torch
        return SimpleNamespace(logits=torch.tensor([[0.2, 0.8]]))


class _FakeTokenizer:
    """Stub tokenizer — supports call/encode/decode so token-window chunking runs offline."""
    model_max_length = 512

    def __call__(self, text, **kwargs):
        return {}

    def encode(self, text, add_special_tokens=False):
        return list(range(len(text.split())))

    def decode(self, ids, skip_special_tokens=True):
        return " ".join("tok" for _ in ids)


class _FakeDoc:
    """Stub spaCy Doc — iterable over lemmatized tokens (key) with fixed .ents (ent)."""
    def __init__(self, text):
        self._tokens = [
            SimpleNamespace(lemma_=word, is_space=False) for word in text.split()
        ] or [SimpleNamespace(lemma_="stub", is_space=False)]
        self.ents = [SimpleNamespace(text="stub")]

    def __iter__(self):
        return iter(self._tokens)


class _FakeSpacy:
    """Stub spaCy pipeline — returns a Doc-like object without downloading a model."""
    def __call__(self, text):
        return _FakeDoc(text)


_embedder_cache: dict = {}
_generator_cache: dict = {}


def _fake_embedder(name: str) -> _FakeEmbedder:
    return _embedder_cache.setdefault(name, _FakeEmbedder(name))


def _fake_generator(name: str) -> _FakeGenerator:
    return _generator_cache.setdefault(name, _FakeGenerator(name))


@pytest.fixture(autouse=True)
def stub_loaders(monkeypatch):
    """Patch load_embedder and load_generator in every command module that imports them."""
    cmds_dir = Path(taggly.commands.__file__).parent
    for path in cmds_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        mod = importlib.import_module(f"taggly.commands.{path.stem}")
        if hasattr(mod, "load_embedder"):
            monkeypatch.setattr(mod, "load_embedder", _fake_embedder)
        if hasattr(mod, "load_generator"):
            monkeypatch.setattr(mod, "load_generator", _fake_generator)

    # loaders.generate resolves load_generator inside the loaders module itself
    monkeypatch.setattr(taggly.loaders, "load_generator", _fake_generator)

    # keybert.KeyBERT loads sentence-transformers internally, bypassing load_embedder
    try:
        import keybert
        monkeypatch.setattr(keybert, "KeyBERT", lambda *a, **kw: _FakeKeyBERT())
    except ImportError:
        pass

    # spam/tox build transformers pipelines directly and ents loads spaCy, bypassing the loaders
    import spacy
    import transformers
    monkeypatch.setattr(spacy, "load", lambda name: _FakeSpacy())
    monkeypatch.setattr(transformers, "pipeline", lambda *a, **kw: lambda text, **kwargs: [{"label": "toxic", "score": 0.8}])
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *a, **kw: _FakeTokenizer())
    monkeypatch.setattr(transformers.AutoModelForSequenceClassification, "from_pretrained", lambda *a, **kw: _FakeClassifier())
