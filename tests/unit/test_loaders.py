"""Unit tests for external LLM configuration and loading."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from types import SimpleNamespace


class TestSetLlmEndpoint:
    """Tests for set_llm_endpoint() configuration."""

    def test_set_llm_endpoint_updates_globals(self):
        """set_llm_endpoint updates _LLM_ENDPOINT and _LLM_MODEL."""
        from taggly import loaders

        # Reset globals
        loaders._LLM_ENDPOINT = ""
        loaders._LLM_MODEL = ""

        loaders.set_llm_endpoint("http://localhost:1234", "my-model")

        assert loaders._LLM_ENDPOINT == "http://localhost:1234"
        assert loaders._LLM_MODEL == "my-model"

    def test_set_llm_endpoint_clears_cache(self):
        """set_llm_endpoint clears load_generator cache so next call reloads."""
        from taggly import loaders

        loaders.load_generator.cache_clear()
        loaders._LLM_ENDPOINT = ""
        loaders._LLM_MODEL = ""

        # Verify that cache_clear is called when set_llm_endpoint is called
        original_clear = loaders.load_generator.cache_clear
        clear_called = []

        def track_clear():
            clear_called.append(True)
            original_clear()

        loaders.load_generator.cache_clear = track_clear

        try:
            loaders.set_llm_endpoint("http://localhost:1234")
            assert len(clear_called) == 1, "cache_clear should have been called"
        finally:
            loaders.load_generator.cache_clear = original_clear

    def test_set_llm_endpoint_propagates_timeout(self):
        """load_generator builds _ExternalGenerator with the timeout from set_llm_endpoint."""
        from taggly import loaders

        loaders.set_llm_endpoint("http://localhost:1234", "my-model", timeout=42.0)
        try:
            gen = loaders.load_generator("my-model")
            assert gen._timeout == 42.0
        finally:
            loaders.set_llm_endpoint("", "")

    def test_set_llm_endpoint_with_empty_model(self):
        """set_llm_endpoint allows empty model name (uses command's model name)."""
        from taggly import loaders

        loaders._LLM_ENDPOINT = ""
        loaders._LLM_MODEL = ""

        loaders.set_llm_endpoint("http://localhost:1234")

        assert loaders._LLM_ENDPOINT == "http://localhost:1234"
        assert loaders._LLM_MODEL == ""

    def test_set_llm_endpoint_strips_trailing_slash(self):
        """_ExternalGenerator strips trailing slash from endpoint."""
        from taggly import loaders

        loaders._LLM_ENDPOINT = ""
        loaders._LLM_MODEL = ""
        loaders.set_llm_endpoint("http://localhost:1234/", "model")

        # Check that the endpoint is stored as-is (stripping happens in _ExternalGenerator)
        assert loaders._LLM_ENDPOINT == "http://localhost:1234/"
        gen = loaders._ExternalGenerator(loaders._LLM_ENDPOINT, "model")
        assert gen._url == "http://localhost:1234/v1/chat/completions"


class TestExternalGenerator:
    """Tests for _ExternalGenerator class."""

    def test_external_generator_formats_url(self):
        """_ExternalGenerator constructs correct endpoint URL."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")
        assert gen._url == "http://localhost:1234/v1/chat/completions"
        assert gen._model == "my-model"

    def test_external_generator_strips_trailing_slash(self):
        """_ExternalGenerator strips trailing slash from endpoint."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234/", "my-model")
        assert gen._url == "http://localhost:1234/v1/chat/completions"

    def test_external_generator_string_input(self):
        """_ExternalGenerator accepts string and wraps it in a user message."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Hello, world!"}}]
            }
            mock_post.return_value = mock_response

            result = gen("hello")

            # Check the call was made with correct format
            assert mock_post.called
            call_args = mock_post.call_args
            assert call_args[1]["json"]["messages"] == [{"role": "user", "content": "hello"}]
            assert call_args[1]["json"]["model"] == "my-model"
            assert call_args[1]["json"]["max_tokens"] == 256

            # Check output format matches transformers pipeline
            assert result == [{"generated_text": "Hello, world!"}]

    def test_external_generator_list_input(self):
        """_ExternalGenerator accepts list of messages (chat history)."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")

        messages = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a language."},
        ]

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "It's widely used."}}]
            }
            mock_post.return_value = mock_response

            result = gen(messages)

            # Check the call includes all messages
            call_args = mock_post.call_args
            assert call_args[1]["json"]["messages"] == messages

            # Check output format: should append assistant response to messages
            expected = list(messages) + [{"role": "assistant", "content": "It's widely used."}]
            assert result == [{"generated_text": expected}]

    def test_external_generator_custom_max_tokens(self):
        """_ExternalGenerator uses generation_config.max_new_tokens if provided."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")
        generation_config = SimpleNamespace(max_new_tokens=512)

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            gen("hello", generation_config=generation_config)

            call_args = mock_post.call_args
            assert call_args[1]["json"]["max_tokens"] == 512

    def test_external_generator_custom_timeout(self):
        """_ExternalGenerator posts with the timeout it was constructed with."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model", timeout=42.0)

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            gen("hello")

            assert mock_post.call_args[1]["timeout"] == 42.0

    def test_external_generator_timeout(self):
        """_ExternalGenerator uses 300s timeout."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "response"}}]
            }
            mock_post.return_value = mock_response

            gen("hello")

            call_args = mock_post.call_args
            assert call_args[1]["timeout"] == 300.0

    def test_external_generator_raises_on_http_error(self):
        """_ExternalGenerator raises on HTTP error response."""
        from taggly.loaders import _ExternalGenerator

        gen = _ExternalGenerator("http://localhost:1234", "my-model")

        with patch("httpx.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="401 Unauthorized"):
                gen("hello")


class TestLoadGenerator:
    """Tests for load_generator function with external endpoint."""

    def test_load_generator_uses_external_when_endpoint_set(self):
        """load_generator returns _ExternalGenerator when _LLM_ENDPOINT is set."""
        from taggly import loaders

        loaders._LLM_ENDPOINT = "http://localhost:1234"
        loaders._LLM_MODEL = "my-model"
        loaders.load_generator.cache_clear()

        try:
            gen = loaders.load_generator("ignored-name")
            assert isinstance(gen, loaders._ExternalGenerator)
            assert gen._model == "my-model"
        finally:
            loaders._LLM_ENDPOINT = ""
            loaders._LLM_MODEL = ""
            loaders.load_generator.cache_clear()

    def test_load_generator_falls_back_to_model_name_if_no_llm_model(self):
        """load_generator uses command model name if _LLM_MODEL is empty."""
        from taggly import loaders

        loaders._LLM_ENDPOINT = "http://localhost:1234"
        loaders._LLM_MODEL = ""  # empty
        loaders.load_generator.cache_clear()

        try:
            gen = loaders.load_generator("gemma-2b")
            assert isinstance(gen, loaders._ExternalGenerator)
            assert gen._model == "gemma-2b"  # should use the provided name
        finally:
            loaders._LLM_ENDPOINT = ""
            loaders._LLM_MODEL = ""
            loaders.load_generator.cache_clear()

    def test_load_generator_caches_result(self):
        """load_generator caches results per model name."""
        from taggly import loaders

        loaders._LLM_ENDPOINT = "http://localhost:1234"
        loaders._LLM_MODEL = "my-model"
        loaders.load_generator.cache_clear()

        try:
            gen1 = loaders.load_generator("model-a")
            gen2 = loaders.load_generator("model-a")

            # Both calls should return the same cached instance
            assert gen1 is gen2

            cache_info = loaders.load_generator.cache_info()
            assert cache_info.currsize == 1
            assert cache_info.hits == 1
        finally:
            loaders._LLM_ENDPOINT = ""
            loaders._LLM_MODEL = ""
            loaders.load_generator.cache_clear()


class TestAppConfigExternalLlm:
    """Tests for AppConfig loading of llm_endpoint and llm_model from .env."""

    def test_app_config_reads_llm_endpoint(self, tmp_path, monkeypatch):
        """AppConfig reads LLM_ENDPOINT from .env."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("LLM_ENDPOINT=http://localhost:1234\n")

        from taggly.config import AppConfig
        config = AppConfig()

        assert config.llm_endpoint == "http://localhost:1234"

    def test_app_config_reads_llm_model(self, tmp_path, monkeypatch):
        """AppConfig reads LLM_MODEL from .env."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("LLM_MODEL=my-model-id\n")

        from taggly.config import AppConfig
        config = AppConfig()

        assert config.llm_model == "my-model-id"

    def test_app_config_reads_both(self, tmp_path, monkeypatch):
        """AppConfig reads both LLM_ENDPOINT and LLM_MODEL from .env."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text(
            "LLM_ENDPOINT=http://localhost:1234\nLLM_MODEL=neural-chat-7b\n"
        )

        from taggly.config import AppConfig
        config = AppConfig()

        assert config.llm_endpoint == "http://localhost:1234"
        assert config.llm_model == "neural-chat-7b"

    def test_app_config_defaults_to_empty(self, tmp_path, monkeypatch):
        """AppConfig defaults llm_endpoint and llm_model to empty strings."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("")

        from taggly.config import AppConfig
        config = AppConfig()

        assert config.llm_endpoint == ""
        assert config.llm_model == ""


class TestProbeExternalLlm:
    """Tests for _probe_llm() startup health check."""

    def test_probe_llm_success(self, capsys):
        """_probe_llm succeeds when endpoint is reachable."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            _probe_llm("http://localhost:1234")

            # Should have called GET on /v1/models endpoint
            assert mock_get.called
            call_args = mock_get.call_args
            assert call_args[0][0] == "http://localhost:1234/v1/models"
            assert call_args[1]["timeout"] == 5.0

            # Should print success message
            out, err = capsys.readouterr()
            assert "probing" in err
            assert "reachable" in err

    def test_probe_llm_failure_aborts(self, capsys):
        """_probe_llm exits with code 1 if endpoint is unreachable."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("Connection refused")
            mock_get.return_value = mock_response

            with pytest.raises(SystemExit) as exc:
                _probe_llm("http://localhost:1234")

            assert exc.value.code == 1

            out, err = capsys.readouterr()
            assert "Startup aborted" in err
            assert "LLM endpoint unreachable" in err

    def test_probe_llm_strips_trailing_slash(self):
        """_probe_llm strips trailing slash from endpoint URL."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            _probe_llm("http://localhost:1234/")

            call_args = mock_get.call_args
            assert call_args[0][0] == "http://localhost:1234/v1/models"

    def test_probe_llm_passes_when_model_served(self):
        """_probe_llm succeeds when the configured model appears in /v1/models."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"data": [{"id": "my-model"}, {"id": "other"}]}
            mock_get.return_value = mock_response

            _probe_llm("http://localhost:1234", "my-model")

    def test_probe_llm_aborts_when_model_not_served(self, capsys):
        """_probe_llm exits 1 when the configured model is missing from /v1/models."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"data": [{"id": "other"}]}
            mock_get.return_value = mock_response

            with pytest.raises(SystemExit) as exc:
                _probe_llm("http://localhost:1234", "my-model")

            assert exc.value.code == 1
            err = capsys.readouterr().err
            assert "my-model" in err and "other" in err

    def test_probe_llm_skips_model_check_on_nonstandard_response(self):
        """_probe_llm tolerates /v1/models responses it cannot parse."""
        from taggly.main import _probe_llm

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.side_effect = ValueError("not json")
            mock_get.return_value = mock_response

            _probe_llm("http://localhost:1234", "my-model")


class TestFromHub:
    """Tests for the cache-first from_hub loader."""

    def test_from_hub_prefers_local_cache(self):
        """from_hub loads with local_files_only and never hits the network when cached."""
        from taggly.loaders import from_hub

        loader = Mock(return_value="model")

        assert from_hub(loader, "org/name", trust=True) == "model"
        loader.assert_called_once_with("org/name", local_files_only=True, trust=True)

    def test_from_hub_downloads_when_not_cached(self):
        """from_hub falls back to a hub download when the local cache misses."""
        from taggly.loaders import from_hub

        loader = Mock(side_effect=[OSError("not cached"), "model"])

        assert from_hub(loader, "org/name") == "model"
        loader.assert_called_with("org/name")


class TestGenerate:
    """Tests for the shared greedy generate() helper."""

    def test_generate_strips_think_blocks(self):
        """generate removes leaked <think>…</think> wrappers from the reply."""
        from taggly import loaders

        def fake_generator(messages, generation_config=None, **kwargs):
            return [{"generated_text": list(messages) + [
                {"role": "assistant", "content": "<think>plan</think>\n{\"ok\": true}"}
            ]}]

        with patch.object(loaders, "load_generator", return_value=fake_generator):
            assert loaders.generate("qwen-0.8b", [{"role": "user", "content": "hi"}], 64) == '{"ok": true}'

    def test_generate_disables_thinking(self):
        """generate asks the tokenizer to leave thinking mode off."""
        from taggly import loaders

        seen = {}

        def fake_generator(messages, generation_config=None, **kwargs):
            seen.update(kwargs)
            return [{"generated_text": list(messages) + [{"role": "assistant", "content": "ok"}]}]

        with patch.object(loaders, "load_generator", return_value=fake_generator):
            loaders.generate("qwen-0.8b", [{"role": "user", "content": "hi"}], 64)

        assert seen.get("tokenizer_encode_kwargs") == {"enable_thinking": False}
