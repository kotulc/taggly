"""Abstract base class for all commands."""

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class AbstractBaseCommand(ABC):
    """Base class for all commands. Subclasses must define name, Input, Output, and run()."""
    name: str
    Input: Type[BaseModel]
    Output: Type[BaseModel]
    Config: Type[BaseModel] | None = None

    def __init__(self, config: BaseModel | None = None):
        self.config = config

    @abstractmethod
    def run(self, data: BaseModel) -> BaseModel:
        """Command description (used by CLI + API)."""
        pass
