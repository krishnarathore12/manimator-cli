"""Ollama local LLM provider for manimator."""

import json
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

from manimator.providers.base import LLMProvider

OLLAMA_BASE_URL = "http://localhost:11434"

OLLAMA_RECOMMENDED_MODELS = [
    {
        "name": "codellama:latest",
        "context": "16k tokens",
        "speed": "Fast",
        "description": "Code-specialized Llama model — great for Manim code generation",
    },
    {
        "name": "llama3:latest",
        "context": "8k tokens",
        "speed": "Fast",
        "description": "General-purpose Llama 3 — good all-rounder",
    },
    {
        "name": "mistral:latest",
        "context": "32k tokens",
        "speed": "Fast",
        "description": "Mistral 7B — fast and capable for code tasks",
    },
    {
        "name": "deepseek-coder:latest",
        "context": "16k tokens",
        "speed": "Fast",
        "description": "DeepSeek Coder — excellent for Python code generation",
    },
]


def _ollama_request(path: str, payload: dict[str, Any] | None = None) -> Any:
    """Make a request to the local Ollama API."""
    url = f"{OLLAMA_BASE_URL}{path}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
    else:
        req = Request(url)
    with urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OllamaProvider(LLMProvider):
    """LLM provider backed by a locally running Ollama instance."""

    def __init__(self, model: str = "codellama:latest") -> None:
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            response = _ollama_request("/api/chat", payload)
            return response.get("message", {}).get("content", "")
        except URLError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: `ollama serve`"
            ) from e

    def generate_with_history(self, system_prompt: str, messages: list[dict]) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        payload = {
            "model": self._model,
            "messages": full_messages,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            response = _ollama_request("/api/chat", payload)
            return response.get("message", {}).get("content", "")
        except URLError as e:
            raise RuntimeError(
                f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: `ollama serve`"
            ) from e

    def list_models(self) -> list[dict]:
        """Query Ollama for locally available models."""
        try:
            response = _ollama_request("/api/tags")
            models = response.get("models", [])
            result = []
            for m in models:
                name = m.get("name", "unknown")
                size_bytes = m.get("size", 0)
                size_gb = f"{size_bytes / 1e9:.1f}GB" if size_bytes else "?"
                result.append(
                    {
                        "name": name,
                        "context": "varies",
                        "speed": "Local",
                        "description": f"Local model ({size_gb})",
                    }
                )
            return result if result else OLLAMA_RECOMMENDED_MODELS
        except URLError:
            return OLLAMA_RECOMMENDED_MODELS
