"""Tests for LLM providers (mocked API calls)."""

from unittest.mock import patch, MagicMock

import pytest

from manimator.providers.openai_provider import OpenAIProvider, OPENAI_MODELS
from manimator.providers.anthropic_provider import AnthropicProvider, ANTHROPIC_MODELS
from manimator.providers.ollama_provider import OllamaProvider, OLLAMA_RECOMMENDED_MODELS
from manimator.providers.gemini_provider import GeminiProvider, GEMINI_MODELS


class TestOpenAIProvider:
    def test_list_models_returns_list(self):
        provider = OpenAIProvider(api_key="test-key")
        models = provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_list_models_have_required_keys(self):
        provider = OpenAIProvider(api_key="test-key")
        for model in provider.list_models():
            assert "name" in model
            assert "context" in model
            assert "speed" in model

    def test_generate_calls_api(self):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "from manim import *\nclass GeneratedScene(Scene): pass"

        with patch("manimator.providers.openai_provider.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.return_value = mock_response

            provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
            result = provider.generate("system prompt", "user prompt")

        assert "GeneratedScene" in result

    def test_default_model(self):
        provider = OpenAIProvider(api_key="test-key")
        assert provider._model == "gpt-4o"


class TestAnthropicProvider:
    def test_list_models_returns_list(self):
        provider = AnthropicProvider(api_key="test-key")
        models = provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_list_models_have_required_keys(self):
        for model in ANTHROPIC_MODELS:
            assert "name" in model
            assert "context" in model
            assert "speed" in model

    def test_generate_calls_api(self):
        mock_content = MagicMock()
        mock_content.text = "from manim import *\nclass GeneratedScene(Scene): pass"
        mock_response = MagicMock()
        mock_response.content = [mock_content]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            provider = AnthropicProvider(api_key="test-key")
            result = provider.generate("system prompt", "user prompt")

        assert "GeneratedScene" in result


class TestOllamaProvider:
    def test_list_models_returns_fallback_when_offline(self):
        from urllib.error import URLError
        with patch("manimator.providers.ollama_provider._ollama_request", side_effect=URLError("connection refused")):
            provider = OllamaProvider()
            models = provider.list_models()
        assert models == OLLAMA_RECOMMENDED_MODELS

    def test_list_models_from_running_ollama(self):
        mock_response = {
            "models": [
                {"name": "codellama:latest", "size": 4_000_000_000},
                {"name": "llama3:latest", "size": 8_000_000_000},
            ]
        }
        with patch("manimator.providers.ollama_provider._ollama_request", return_value=mock_response):
            provider = OllamaProvider()
            models = provider.list_models()
        assert len(models) == 2
        assert models[0]["name"] == "codellama:latest"

    def test_generate_raises_on_connection_error(self):
        from urllib.error import URLError
        with patch("manimator.providers.ollama_provider._ollama_request", side_effect=URLError("refused")):
            provider = OllamaProvider()
            with pytest.raises(RuntimeError, match="Ollama"):
                provider.generate("system", "user")

    def test_generate_returns_content(self):
        mock_response = {"message": {"content": "from manim import *\nclass GeneratedScene(Scene): pass"}}
        with patch("manimator.providers.ollama_provider._ollama_request", return_value=mock_response):
            provider = OllamaProvider()
            result = provider.generate("system", "user")
        assert "GeneratedScene" in result


class TestGeminiProvider:
    def test_list_models_returns_list(self):
        provider = GeminiProvider(api_key="test-key")
        models = provider.list_models()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_list_models_have_required_keys(self):
        for model in GEMINI_MODELS:
            assert "name" in model
            assert "context" in model
            assert "speed" in model

    def test_generate_calls_api(self):
        mock_response = MagicMock()
        mock_response.text = "from manim import *\nclass GeneratedScene(Scene): pass"

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.models.generate_content.return_value = mock_response

            provider = GeminiProvider(api_key="test-key", model="gemini-2.5-flash")
            result = provider.generate("system prompt", "user prompt")

        assert "GeneratedScene" in result

    def test_default_model(self):
        provider = GeminiProvider(api_key="test-key")
        assert provider._model == "gemini-2.5-flash"
