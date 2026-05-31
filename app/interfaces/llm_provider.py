"""
Abstract interface for LLM providers.

All LLM-dependent services depend on this abstraction,
enabling future swaps to OpenAI, Claude, or local models
without changing business logic.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for language model providers."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a text completion for the given prompt.

        Args:
            prompt: The full prompt string to send to the LLM.

        Returns:
            The generated text response.

        Raises:
            LLMProviderError: If the LLM call fails.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Verify that the LLM provider is reachable and operational.

        Returns:
            True if the provider is healthy, False otherwise.
        """
        ...
