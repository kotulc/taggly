"""Unit tests for the desc command."""

from taggly.commands.desc import DescCommand, DescInput


def test_clean_strips_markdown_bold():
    """_clean removes paired **bold** / __bold__ markers."""
    assert DescCommand._clean("A **quick** summary") == "A quick summary"
    assert DescCommand._clean("__Language models__") == "Language models"


def test_clean_strips_unpaired_bold_markers():
    """_clean drops leftover unpaired bold markers."""
    assert DescCommand._clean("**partial bold") == "partial bold"
    assert DescCommand._clean("trailing**") == "trailing"


def test_operation_cleans_generated_text(monkeypatch):
    """operation strips markdown from the model reply before returning."""
    monkeypatch.setattr(
        "taggly.commands.desc.generate",
        lambda *a, **k: "  **Machine learning overview**  ",
    )
    out = DescCommand().operation(DescInput(content="..."))
    assert out.description == "Machine learning overview"
