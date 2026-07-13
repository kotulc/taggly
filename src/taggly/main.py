import os
import sys

from taggly.config import AppConfig
from taggly.registry import discover_commands
from taggly.cli import build_cli
from taggly.api import build_api


def main():
    config = AppConfig()
    if config.hf_token:
        os.environ["HF_TOKEN"] = config.hf_token  # let huggingface_hub authenticate downloads

    if config.llm_endpoint:
        from taggly.loaders import set_llm_endpoint
        set_llm_endpoint(config.llm_endpoint, config.llm_model, config.api_timeout)
    elif config.llm_model:
        print("warning: LLM_MODEL is set but LLM_ENDPOINT is not; using local models.", file=sys.stderr)

    registry = discover_commands(app_config=config)

    if config.mode == "api":
        import uvicorn
        api = build_api(registry)
        startup_checks(registry, config)
        uvicorn.run(api, host=config.host, port=config.port)
    else:
        build_cli(registry, config)()


def startup_checks(registry, config) -> None:
    """Fail fast before serving: validate LLM config, probe the endpoint, pre-load models."""
    _check_llm(registry, config)
    if config.llm_endpoint:
        _probe_llm(config.llm_endpoint, config.llm_model)
    _probe(registry, config.warmup)


def _check_hf_token(token: str) -> None:
    """Abort when huggingface.co rejects the token; network errors defer to the model probe."""
    from huggingface_hub import whoami
    from huggingface_hub.errors import HfHubHTTPError
    try:
        whoami(token=token)
    except HfHubHTTPError as e:
        print(f"\nStartup aborted — HF_TOKEN rejected by huggingface.co: {e}", file=sys.stderr)
        print("  Generate a valid token at https://huggingface.co/settings/tokens.", file=sys.stderr)
        sys.exit(1)
    except Exception:
        pass  # offline or transient error; the warmup model load surfaces real failures


def _check_llm(registry, config) -> None:
    """Abort when warmup includes gated-model commands but no usable LLM source is configured."""
    from taggly.loaders import GATED_MODELS
    names = [n for n in config.warmup if getattr(registry.get(n), "requires_llm", False)]
    if not names:
        return

    if config.llm_endpoint:
        if not config.llm_model:
            print("\nStartup aborted — LLM_MODEL must be set when LLM_ENDPOINT is configured.", file=sys.stderr)
            sys.exit(1)
        return

    gated = [n for n in names
             if getattr(getattr(registry[n], "_config", None), "model", "").lower() in GATED_MODELS]
    if not gated:
        return  # ungated models (e.g. smollm-135m) download without a token

    if not config.hf_token:
        print(f"\nStartup aborted — warmup commands use gated models: {', '.join(gated)}.", file=sys.stderr)
        print(
            "  Set HF_TOKEN to download gated models from huggingface.co, or LLM_ENDPOINT "
            "and LLM_MODEL to use an external API.",
            file=sys.stderr,
        )
        sys.exit(1)

    _check_hf_token(config.hf_token)  # local fallback: token must be valid before downloading


def _probe(registry, names) -> None:
    """Load each warmup command's model, aborting startup if any are unavailable."""
    if not names:
        return
    failures = []
    for name in names:
        if name not in registry:
            print(f"warning: unknown warmup command '{name}', skipping.", file=sys.stderr)
            continue
        print(f"[{name}] loading model...", file=sys.stderr)
        try:
            registry[name].warmup()
            registry[name].warmed_up = True
        except Exception as e:
            failures.append((name, e))
            print(f"[{name}] failed", file=sys.stderr)

    if failures:
        print("\nStartup aborted — these models could not be loaded:", file=sys.stderr)
        for name, e in failures:
            print(f"  - {name}: {e}", file=sys.stderr)
        print(
            "\nCheck connectivity to huggingface.co; for gated models (e.g. Gemma) set "
            "HF_TOKEN and accept the model license on its model page. Generative commands "
            "can use an external API instead via LLM_ENDPOINT and LLM_MODEL.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("All models loaded.\n", file=sys.stderr)


def _probe_llm(endpoint: str, model: str = "") -> None:
    """Verify the LLM endpoint is reachable and serves the configured model, aborting if not."""
    import httpx
    url = f"{endpoint.rstrip('/')}/v1/models"
    print(f"[llm] probing {url}...", file=sys.stderr)
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
    except Exception as e:
        print(f"\nStartup aborted — LLM endpoint unreachable: {e}", file=sys.stderr)
        print("  Check that the LLM service is running and LLM_ENDPOINT is correct.", file=sys.stderr)
        sys.exit(1)

    if model:
        try:
            served = [m.get("id", "") for m in response.json().get("data", [])]
        except Exception:
            served = None  # nonstandard /v1/models response; skip model verification
        if served is not None and model not in served:
            print(f"\nStartup aborted — model '{model}' not served by {endpoint}.", file=sys.stderr)
            print(f"  Available models: {', '.join(served) or 'none'}", file=sys.stderr)
            sys.exit(1)

    print("[llm] endpoint reachable.\n", file=sys.stderr)


if __name__ == "__main__":
    main()
