"""Add command: adds two numbers with configurable decimal precision."""

from pydantic import BaseModel, Field

from taggly.base import AbstractBaseCommand


class AddInput(BaseModel):
    a: float
    b: float


class AddOutput(BaseModel):
    result: float


class AddConfig(BaseModel):
    precision: int = Field(2, description="Decimal places to round the result")


class AddCommand(AbstractBaseCommand):
    name = "add"
    Input = AddInput
    Output = AddOutput
    Config = AddConfig

    def operation(self, data: AddInput, config: AddConfig | None = None) -> AddOutput:
        """Add two numbers."""
        cfg = config or self.config or AddConfig()
        return AddOutput(result=round(data.a + data.b, cfg.precision))
