"""Abstract base class for all commands."""

import httpx

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class AbstractBaseCommand(ABC):
    """Base class for all commands. Subclasses must define name, Input, Output, and operation()."""
    name: str
    Input: Type[BaseModel]
    Output: Type[BaseModel]
    Config: Type[BaseModel] | None = None

    def __init__(self, api_url: str=None, config: BaseModel=None):
        self.api_url = api_url
        self.config = config

    def run(self, data: BaseModel, config: BaseModel=None) -> BaseModel:
        """Delegate to the API if available, otherwise call operation() locally."""
        config = config or self.config
        if self.api_url:
            try:
                result = self._call_api(self.api_url, data, config)
                return result
            except Exception:
                pass

        return self.operation(data, config)

    def warmup(self) -> None:
        """Pre-load any expensive dependencies. Override in commands with heavy init."""
        pass

    @abstractmethod
    def operation(self, data: BaseModel, config: BaseModel=None) -> BaseModel:
        """Command description (used by CLI + API)."""
        pass

    @classmethod
    def _call_api(cls, api_url: str, data: BaseModel, config: BaseModel) -> BaseModel:
        """POST to api_url with input as body and config fields as query params."""
        params = config.model_dump() if config else {}
        response = httpx.post(api_url, json=data.model_dump(), params=params, timeout=5.0)
        response.raise_for_status()
        
        return cls.Output(**response.json())
