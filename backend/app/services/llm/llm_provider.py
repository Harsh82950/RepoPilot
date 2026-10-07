from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a text response from a prompt.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate a response that may request tool calls.

        Returns a provider-independent response containing either
        normal text or one or more tool calls.
        """
        raise NotImplementedError