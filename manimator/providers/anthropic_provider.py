"""Anthropic LLM provider for manimator."""

import anthropic

from manimator.providers.base import LLMProvider

ANTHROPIC_MODELS = [
    {
        "name": "claude-opus-4-5",
        "context": "200k tokens",
        "speed": "Powerful",
        "description": "Most capable Claude model — best for complex animations",
    },
    {
        "name": "claude-sonnet-4-5",
        "context": "200k tokens",
        "speed": "Balanced",
        "description": "Great balance of intelligence and speed",
    },
    {
        "name": "claude-haiku-4-5",
        "context": "200k tokens",
        "speed": "Fast",
        "description": "Fastest Claude model — ideal for quick iterations",
    },
    {
        "name": "claude-3-5-sonnet-20241022",
        "context": "200k tokens",
        "speed": "Balanced",
        "description": "Stable Sonnet 3.5 release with strong code generation",
    },
]


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5") -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        return message.content[0].text if message.content else ""

    def generate_with_history(self, system_prompt: str, messages: list[dict]) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
        return message.content[0].text if message.content else ""

    def list_models(self) -> list[dict]:
        return ANTHROPIC_MODELS
