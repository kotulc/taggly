"""desc command: Generate a natural-language description of the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import load_generator
from taggly.models.base import AbstractBaseCommand


class DescConfig(BaseModel):
    model: str = Field("gemma-1b", description="Generative model: 'gemma-1b', 'gemma-4b', or 'gemma-12b'")
    max_tokens: int = Field(128, description="Maximum number of tokens to generate")


class DescInput(BaseModel):
    content: str


class DescOutput(BaseModel):
    description: str


class DescCommand(AbstractBaseCommand):
    name = "desc"
    Input = DescInput
    Output = DescOutput
    Config = DescConfig

    def __init__(self, api_url: str=None, config: BaseModel=None):
        cfg = config if config is not None else DescConfig()
        super().__init__(api_url, cfg)

    def warmup(self) -> None:
        """Pre-load the configured generative model."""
        load_generator((self.config or DescConfig()).model)

    def operation(self, data: DescInput, config: DescConfig=None) -> DescOutput:
        """Generate a concise description of the supplied text."""
        cfg = config or self.config or DescConfig()
        prompt = f"Describe the following text in a single sentence:\n\n{data.content}"
        output = load_generator(cfg.model)(prompt, max_new_tokens=cfg.max_tokens, return_full_text=False)
        return DescOutput(description=output[0]["generated_text"].strip())
