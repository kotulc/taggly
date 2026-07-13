"""desc command: Generate a natural-language description of the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import load_generator
from taggly.models.base import AbstractBaseCommand

# Model query prompt template
PROMPT = "Describe the following text in a single short sentence:\n\n{}"


class DescConfig(BaseModel):
    model: str = Field("smollm-135m", description="Generative model: 'smollm-135m', 'gemma-2b', 'gemma-4b', or 'gemma-12b'")
    max_tokens: int = Field(128, description="Maximum number of tokens to generate")


class DescInput(BaseModel):
    content: str = Field(..., description="A text string to generate a description from.")


class DescOutput(BaseModel):
    description: str = Field(..., description="The generated description.")


class DescCommand(AbstractBaseCommand):
    name = "desc"
    requires_llm = True
    Config = DescConfig
    Input = DescInput
    Output = DescOutput

    def __init__(self, config: DescConfig=None, **kwargs):
        super().__init__(**kwargs)
        self._config = config if config is not None else DescConfig()

    def warmup(self) -> None:
        """Pre-load the configured generative model."""
        load_generator(self._config.model)

    def operation(self, data: DescInput, params: BaseModel=None) -> DescOutput:
        """Generate a concise description of the supplied text."""
        from transformers import GenerationConfig
        messages = [{"role": "user", "content": PROMPT.format(data.content)}]
        output = load_generator(self._config.model)(
            messages, generation_config=GenerationConfig(max_new_tokens=self._config.max_tokens)
        )
        result = output[0]["generated_text"]
        text = result[-1]["content"] if isinstance(result, list) else result
        return DescOutput(description=text.strip())
