"""Google Gemini LLM provider for manimator."""

from google import genai
from google.genai import types

from manimator.providers.base import LLMProvider

GEMINI_MODELS = [
    {
        "name": "gemini-2.5-pro-preview-06-05",
        "context": "1M tokens",
        "speed": "Powerful",
        "description": "Most capable Gemini model — best for complex animations",
    },
    {
        "name": "gemini-2.5-flash-preview-04-17",
        "context": "1M tokens",
        "speed": "Fast",
        "description": "Fast and efficient — great balance for most animations",
    },
    {
        "name": "gemini-2.0-flash",
        "context": "1M tokens",
        "speed": "Very Fast",
        "description": "Gemini 2.0 Flash — excellent speed with strong code generation",
    },
    {
        "name": "gemini-1.5-pro",
        "context": "2M tokens",
        "speed": "Balanced",
        "description": "Stable Gemini 1.5 Pro with massive context window",
    },
    {
        "name": "gemini-1.5-flash",
        "context": "1M tokens",
        "speed": "Fast",
        "description": "Lightweight Gemini 1.5 — fast and cost-efficient",
    },
]


class GeminiProvider(LLMProvider):
    """LLM provider backed by the Google Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview-04-17") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
        return response.text or ""

    def generate_with_history(self, system_prompt: str, messages: list[dict]) -> str:
        # Convert messages to Gemini content parts
        contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
                max_output_tokens=8192,
            ),
        )
        return response.text or ""

    def list_models(self) -> list[dict]:
        return GEMINI_MODELS
