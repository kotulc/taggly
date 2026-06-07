"""Application-level configuration loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    mode: str = "cli"  # "cli", "api" or "docs"
    host: str = "127.0.0.1"
    port: int = 8000
    commands: dict[str, dict] = {}  # per-command config keyed by command name
    warmup: list[str] = ["keys", "spam", "tox"]  # command names to pre-load on API startup
