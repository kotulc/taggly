"""Unit tests for the docs generation module."""

from pathlib import Path

import pytest

from taggly.cli import build_cli
from taggly.docs import generate_docs
from taggly.registry import discover_commands

REGISTRY = discover_commands()
CLI = build_cli(REGISTRY)


@pytest.fixture()
def docs_dir(tmp_path):
    """Run generate_docs into a temp directory and return the path."""
    generate_docs(REGISTRY, CLI, output_dir=tmp_path)
    return tmp_path


def test_command_files_exist(docs_dir):
    """generate_docs writes one .md per command under docs/commands/."""
    for name in REGISTRY:
        assert (docs_dir / "commands" / f"{name}.md").exists(), \
            f"Missing docs/commands/{name}.md"


def test_command_files_contain_name(docs_dir):
    """Each generated doc references its own command name."""
    for name in REGISTRY:
        content = (docs_dir / "commands" / f"{name}.md").read_text(encoding="utf-8")
        assert name in content


def test_readme_copied_as_about(docs_dir, monkeypatch, tmp_path):
    """about.md is written when README.md exists in cwd."""
    fake_readme = tmp_path / "README.md"
    fake_readme.write_text("# Test Project", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    generate_docs(REGISTRY, CLI, output_dir=out)
    assert (out / "about.md").exists()
    assert (out / "about.md").read_text(encoding="utf-8") == "# Test Project"


def test_no_about_without_readme(monkeypatch, tmp_path):
    """about.md is not written when README.md is absent from cwd."""
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    generate_docs(REGISTRY, CLI, output_dir=out)
    assert not (out / "about.md").exists()
