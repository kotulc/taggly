"""Application-level configuration loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    mode: str = "cli"  # "cli" or "api"
    host: str = "127.0.0.1"
    port: int = 8000
    commands: dict[str, dict] = {}  # per-command config keyed by command name
