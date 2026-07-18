"""Application-level configuration loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Server settings: model_config enables .env file loading via pydantic-settings."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mode: str = "cli"
    host: str = "127.0.0.1"
    port: int = 8000
    warmup: list[str] = ["ext", "key", "score"]
    hf_token: str = ""
    api_timeout: float = 300.0    # read/write/pool timeout for API delegation (seconds)
    connect_timeout: float = 2.0  # connect timeout; fast-fails when server is down
    llm_endpoint: str = ""        # optional OpenAI-compatible API base URL for generative commands
    llm_model: str = ""           # model name sent to the external LLM (overrides command Config)
