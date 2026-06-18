"""Abstract base class for all commands."""

import sys
from abc import ABC, abstractmethod
from typing import Type

import httpx
from pydantic import BaseModel


class AbstractBaseCommand(ABC):
    """Base class for all commands. Subclasses must define name, Input, Output, and operation()."""
    name: str
    Input: Type[BaseModel]
    Output: Type[BaseModel]

    def __init__(self, api_url: str=None, api_timeout: float=300.0, connect_timeout: float=2.0):
        self.api_url = api_url
        self.api_timeout = api_timeout
        self.connect_timeout = connect_timeout
        self.warmed_up = False

    def run(self, data: BaseModel, params: BaseModel=None) -> BaseModel:
        """Delegate to the API if available, otherwise call operation() locally."""
        if self.api_url:
            try:
                result = self._call_api(self.api_url, data, params)
                print(f"[{self.name}] api", file=sys.stderr)
                return result
            except (httpx.ConnectError, httpx.ConnectTimeout):
                pass  # server not reachable, silent local fallback
            except Exception as e:
                print(f"[{self.name}] api error ({type(e).__name__}): {e}", file=sys.stderr)
        return self.operation(data, params)

    def warmup(self) -> None:
        """Pre-load any expensive dependencies. Override in commands with heavy init."""
        pass

    @abstractmethod
    def operation(self, data: BaseModel, params: BaseModel=None) -> BaseModel:
        """Command description (used by CLI + API)."""
        pass

    def _call_api(self, api_url: str, data: BaseModel, params: BaseModel=None) -> BaseModel:
        """POST to api_url with input as body and params fields as query params."""
        params = params.model_dump() if params else {}
        timeout = httpx.Timeout(self.api_timeout, connect=self.connect_timeout)
        response = httpx.post(api_url, json=data.model_dump(), params=params, timeout=timeout)
        response.raise_for_status()
        return self.Output(**response.json())
