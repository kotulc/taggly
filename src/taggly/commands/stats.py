"""Stats command: computes basic statistics over a list of floats."""

from typing import List

from pydantic import BaseModel, Field

from taggly.base import AbstractBaseCommand


class StatsInput(BaseModel):
    values: List[float]


class StatsOutput(BaseModel):
    count: int
    mean: float
    min: float
    max: float


class StatsConfig(BaseModel):
    round_digits: int = Field(2, description="Decimal places to round computed values")


class StatsCommand(AbstractBaseCommand):
    name = "stats"
    Input = StatsInput
    Output = StatsOutput
    Config = StatsConfig

    def operation(self, data: StatsInput, config: StatsConfig | None = None) -> StatsOutput:
        """Compute basic statistics."""
        cfg = config or self.config or StatsConfig()
        vals = data.values
        return StatsOutput(
            count=len(vals),
            mean=round(sum(vals) / len(vals), cfg.round_digits) if vals else 0.0,
            min=round(min(vals), cfg.round_digits) if vals else 0.0,
            max=round(max(vals), cfg.round_digits) if vals else 0.0,
        )
