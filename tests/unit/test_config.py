"""Unit tests: config/config.yaml values are applied to command Config at discovery time."""

import pytest

from taggly.registry import discover_commands


@pytest.fixture()
def config_dir(tmp_path):
    """Return a temp directory pre-populated with a config/config.yaml."""
    (tmp_path / "config").mkdir()
    return tmp_path


def test_config_yaml_overrides_default(config_dir, monkeypatch):
    """Config fields in config/config.yaml override command Config field defaults."""
    (config_dir / "config" / "config.yaml").write_text(
        "keys:\n  model: yake\n", encoding="utf-8"
    )
    monkeypatch.chdir(config_dir)
    registry = discover_commands()
    assert registry["keys"]._config.model == "yake"


def test_config_yaml_partial_override(config_dir, monkeypatch):
    """Only the specified fields are overridden; unmentioned fields keep their defaults."""
    (config_dir / "config" / "config.yaml").write_text(
        "ents:\n  language: en_core_web_sm\n", encoding="utf-8"
    )
    monkeypatch.chdir(config_dir)
    registry = discover_commands()
    assert registry["ents"]._config.language == "en_core_web_sm"
    assert registry["keys"]._config.model == "keybert"  # untouched default


def test_missing_config_yaml_uses_defaults(tmp_path, monkeypatch):
    """When config/config.yaml is absent, all commands use their built-in defaults."""
    monkeypatch.chdir(tmp_path)
    registry = discover_commands()
    assert registry["keys"]._config.model == "keybert"
    assert registry["score"]._config.model == "all-minilm"


def test_unknown_command_in_config_is_ignored(config_dir, monkeypatch):
    """An unrecognised command key in config.yaml does not raise an error."""
    (config_dir / "config" / "config.yaml").write_text(
        "nonexistent_command:\n  model: x\n", encoding="utf-8"
    )
    monkeypatch.chdir(config_dir)
    discover_commands()  # should not raise
