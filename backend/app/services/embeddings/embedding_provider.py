from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract interface for generating text embeddings.

    The rest of RepoPilot should depend on this interface
    instead of depending directly on a specific embedding model.
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embeddings."""
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text."""
        raise NotImplementedError

    @abstractmethod
    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 4,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        raise NotImplementedError