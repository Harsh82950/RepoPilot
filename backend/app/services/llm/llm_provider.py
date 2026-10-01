from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract interface for all LLM providers used by RepoPilot.

    RepoPilot should depend on this interface rather than directly
    depending on OpenAI, Gemini, Ollama, or another provider.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the given prompt.
        """
        raise NotImplementedError