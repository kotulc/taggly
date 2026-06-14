"""Application-level configuration loaded from environment variables or a .env file."""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mode: str = "cli"  # "cli" or "api"
    host: str = "127.0.0.1"
    port: int = 8000
    commands: dict[str, dict] = {}  # per-command config keyed by command name
    warmup: list[str] = ["ext", "score", "topics"]  # command names to pre-load on API startup
    hf_token: str = os.getenv("HF_TOKEN", "")  # HuggingFace token for downloading gated models (e.g. Gemma)
