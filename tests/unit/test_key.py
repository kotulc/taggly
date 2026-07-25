"""Unit tests for the key command."""

from taggly.commands.key import KeyCommand, KeyInput, KeyParams


def test_clean_term_drops_noise():
    """_clean_term drops pure digits, punctuation-only, and single-character terms."""
    assert KeyCommand._clean_term("2024") is None
    assert KeyCommand._clean_term("...") is None
    assert KeyCommand._clean_term("a") is None
    assert KeyCommand._clean_term("") is None


def test_clean_term_strips_edge_punctuation():
    """_clean_term trims edge punctuation but keeps the word."""
    assert KeyCommand._clean_term("models,") == "models"
    assert KeyCommand._clean_term('"learning"') == "learning"


def test_postprocess_dedupes_by_stem():
    """Morphological variants collapse to the first surface form in extractor order."""
    cmd = KeyCommand()
    cmd._stem_key = lambda term: {"models": "model", "modeling": "model", "model": "model", "language": "language"}[term]
    out = cmd._postprocess(
        [("models", 0.9), ("modeling", 0.8), ("language", 0.7), ("model", 0.6)],
        KeyParams(),
    )
    assert out == ["models", "language"]


def test_postprocess_normalize_preserves_order():
    """normalize lowercases without scrambling extractor order via set-hashing."""
    cmd = KeyCommand()
    cmd._stem_key = lambda term: term.lower()
    out = cmd._postprocess(
        [("Models", 0.9), ("Language", 0.8), ("models", 0.7)],
        KeyParams(normalize=True),
    )
    assert out == ["models", "language"]


def test_postprocess_drops_noisy_terms():
    """Numeric / punctuation noise is filtered before stemming."""
    cmd = KeyCommand()
    cmd._stem_key = lambda term: term.lower()
    out = cmd._postprocess(
        [("models", 0.9), ("2024", 0.8), ("...", 0.7), ("a", 0.6), ("learning", 0.5)],
        KeyParams(),
    )
    assert out == ["models", "learning"]


def test_operation_applies_postprocess_and_top_n(monkeypatch):
    """operation post-processes raw extractor output and respects top_n."""
    cmd = KeyCommand()
    cmd._stem_key = lambda term: {"models": "model", "modeling": "model", "learning": "learning", "data": "data"}[term]
    monkeypatch.setattr(
        cmd,
        "_extract",
        lambda content, params, top_n=None: [
            ("models", 0.9),
            ("modeling", 0.85),
            ("learning", 0.8),
            ("data", 0.7),
            ("2024", 0.6),
        ],
    )
    out = cmd.operation(KeyInput(content="..."), KeyParams(top_n=2))
    assert out.keywords == ["models", "learning"]
