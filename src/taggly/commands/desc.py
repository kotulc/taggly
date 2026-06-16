"""desc command: Generate a natural-language description of the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import load_generator
from taggly.models.base import AbstractBaseCommand

# Define generative prompt template
PROMPT = "Describe the following text in a single short sentence:\n\n{}"


class DescConfig(BaseModel):
    model: str = Field("gemma-2b", description="Generative model: 'gemma-2b', 'gemma-4b', or 'gemma-12b'")
    max_tokens: int = Field(128, description="Maximum number of tokens to generate")


class DescInput(BaseModel):
    content: str = Field(..., description="A text string to generate a description from.")


class DescOutput(BaseModel):
    description: str = Field(..., description="The generated description.")


class DescCommand(AbstractBaseCommand):
    name = "desc"
    Input = DescInput
    Output = DescOutput
    Config = DescConfig

    def warmup(self) -> None:
        """Pre-load the configured generative model."""
        load_generator((self.config or DescConfig()).model)

    def operation(self, data: DescInput, config: DescConfig=None) -> DescOutput:
        """Generate a concise description of the supplied text."""
        from transformers import GenerationConfig
        cfg = config or self.config or DescConfig()
        messages = [{"role": "user", "content": PROMPT.format(data.content)}]
        output = load_generator(cfg.model)(messages, generation_config=GenerationConfig(max_new_tokens=cfg.max_tokens))
        result = output[0]["generated_text"]
        text = result[-1]["content"] if isinstance(result, list) else result
        return DescOutput(description=text.strip())
