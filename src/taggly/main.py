import sys

from taggly.config import AppConfig
from taggly.registry import discover_commands
from taggly.cli import build_cli
from taggly.api import build_api


def main():
    config = AppConfig()
    registry = discover_commands(app_config=config)

    if config.mode == "api":
        import uvicorn
        api = build_api(registry)
        for name in config.warmup:
            if name in registry:
                print(f"[{name}] warming up...", file=sys.stderr)
                registry[name].warmup()
        print("", file=sys.stderr)
        uvicorn.run(api, host=config.host, port=config.port)
    else:
        build_cli(registry, config)()


if __name__ == "__main__":
    main()
