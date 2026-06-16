"""Lightweight stubs replacing heavy ML models for fast integration testing."""

import importlib
from pathlib import Path

import numpy as np
import pytest

import taggly.commands


class _FakeEmbedder:
    """Stub embedder — output is deterministic per (model_name, text) so models are distinguishable."""
    DIM = 4

    def __init__(self, name: str):
        self._name = name

    def encode(self, texts):
        if isinstance(texts, str):
            seed = hash((self._name, texts)) % (2 ** 31)
            return np.random.RandomState(seed).rand(self.DIM).astype(np.float32)
        return np.vstack([self.encode(t) for t in texts]) if texts else np.zeros((0, self.DIM), np.float32)


class _FakeGenerator:
    """Stub generator — returns model-name-tagged JSON so tests can distinguish models."""

    def __init__(self, name: str):
        self._name = name

    def __call__(self, messages, generation_config=None, **kwargs):
        text = f'{{"entities":["{self._name}"],"topics":["stub"],"concepts":["test"]}}'
        if isinstance(messages, list):
            return [{"generated_text": list(messages) + [{"role": "assistant", "content": text}]}]
        return [{"generated_text": text}]


_embedder_cache: dict = {}
_generator_cache: dict = {}


def _fake_embedder(name: str) -> _FakeEmbedder:
    return _embedder_cache.setdefault(name, _FakeEmbedder(name))


def _fake_generator(name: str) -> _FakeGenerator:
    return _generator_cache.setdefault(name, _FakeGenerator(name))


def _fake_topics(self, documents, cfg):
    """Return model-specific keywords so test_model_config_respected can distinguish models."""
    return [f"{cfg.model}:topic", "stub"] if len(documents) >= 2 else []


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

    from taggly.commands.topics import TopicsCommand
    monkeypatch.setattr(TopicsCommand, "_topics", _fake_topics)
