"""Abstract LLM provider interface for manimator."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate Manim Python code from the given prompts.

        Args:
            system_prompt: The system-level instructions for the LLM.
            user_prompt: The user's animation description / correction request.

        Returns:
            A string containing the generated (or corrected) Python code.
        """
        ...

    def generate_with_history(self, system_prompt: str, messages: list[dict]) -> str:
        """
        Generate Manim code using full conversation history.

        Args:
            system_prompt: The system-level instructions for the LLM.
            messages: A list of {"role": "user"|"assistant", "content": "..."} dicts.

        Returns:
            A string containing the generated (or corrected) Python code.

        Default implementation falls back to generate() using the last user message.
        """
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return self.generate(system_prompt, last_user)

    @abstractmethod
    def list_models(self) -> list[dict]:
        """
        Return a list of available models with metadata.

        Each dict should contain:
            - name: str
            - context: str  (e.g. "128k tokens")
            - speed: str    (e.g. "Balanced")
            - description: str
        """
        ...
