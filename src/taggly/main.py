from taggly.config import AppConfig
from taggly.registry import discover_commands
from taggly.cli import build_cli
from taggly.api import build_api


def main():
    config = AppConfig()
    registry = discover_commands(app_config=config)

    # Start the app as either a CLI or API based on the config setting
    if config.mode == "cli":
        cli = build_cli(registry)
        cli()
    else:
        import uvicorn
        api = build_api(registry)
        uvicorn.run(api, host=config.host, port=config.port)


if __name__ == "__main__":
    main()