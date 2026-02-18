"""OpenAI LLM provider for manimator."""

from openai import OpenAI

from manimator.providers.base import LLMProvider

OPENAI_MODELS = [
    {
        "name": "gpt-4o",
        "context": "128k tokens",
        "speed": "Balanced",
        "description": "Best overall — fast, smart, great at code generation",
    },
    {
        "name": "gpt-4-turbo",
        "context": "128k tokens",
        "speed": "Balanced",
        "description": "High-capability model with large context window",
    },
    {
        "name": "gpt-4o-mini",
        "context": "128k tokens",
        "speed": "Fast",
        "description": "Lightweight and cost-efficient for simpler animations",
    },
    {
        "name": "gpt-3.5-turbo",
        "context": "16k tokens",
        "speed": "Very Fast",
        "description": "Fastest and cheapest; best for simple scenes",
    },
]


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def generate_with_history(self, system_prompt: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
            temperature=0.2,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def list_models(self) -> list[dict]:
        return OPENAI_MODELS
