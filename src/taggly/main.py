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
        set_llm_endpoint(config.llm_endpoint, config.llm_model)

    registry = discover_commands(app_config=config)

    if config.mode == "api":
        import uvicorn
        api = build_api(registry)
        if config.llm_endpoint:
            _probe_llm(config.llm_endpoint)
        _probe(registry, config.warmup)
        uvicorn.run(api, host=config.host, port=config.port)
    else:
        build_cli(registry, config)()


def _probe_llm(endpoint: str) -> None:
    """Verify the external LLM endpoint is reachable, aborting startup if not."""
    import httpx
    url = f"{endpoint.rstrip('/')}/v1/models"
    print(f"[llm] probing {url}...", file=sys.stderr)
    try:
        httpx.get(url, timeout=5.0).raise_for_status()
        print("[llm] endpoint reachable.\n", file=sys.stderr)
    except Exception as e:
        print(f"\nStartup aborted — LLM endpoint unreachable: {e}", file=sys.stderr)
        print("  Check that the LLM service is running and LLM_ENDPOINT is correct.", file=sys.stderr)
        sys.exit(1)


def _probe(registry, names) -> None:
    """Load each warmup command's model, aborting startup if any are unavailable."""
    if not names:
        return
    failures = []
    for name in names:
        if name not in registry:
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
            "HF_TOKEN and accept the model license on its model page.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("All models loaded.\n", file=sys.stderr)


if __name__ == "__main__":
    main()
