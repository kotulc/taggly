"""desc command: Generate a natural-language description of the supplied text."""

from pydantic import BaseModel, Field

from taggly.loaders import generate, load_generator
from taggly.models.base import AbstractBaseCommand

# Prompt includes a one-shot worked example — small models copy a demonstrated
# format far more reliably than they follow format descriptions.
PROMPT = "Describe the following text in a single short sentence:\n\n{}"
EXAMPLE_TEXT = "Marie Curie won the Nobel Prize in Paris."
EXAMPLE_REPLY = "A note about Marie Curie receiving the Nobel Prize in Paris."


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
        messages = [
            {"role": "user", "content": PROMPT.format(EXAMPLE_TEXT)},
            {"role": "assistant", "content": EXAMPLE_REPLY},
            {"role": "user", "content": PROMPT.format(data.content)},
        ]
        text = generate(self._config.model, messages, self._config.max_tokens)
        return DescOutput(description=text.strip())
