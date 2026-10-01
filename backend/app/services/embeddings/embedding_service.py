
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.services.embeddings.embedding_provider import EmbeddingProvider


MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
EMBEDDING_DIMENSION = 1024
DEVICE = "cpu"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load the Qwen embedding model once and reuse it.
    """
    return SentenceTransformer(
        MODEL_NAME,
        device=DEVICE,
        trust_remote_code=True,
    )


class QwenEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider backed by Qwen3-Embedding-0.6B.
    """

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        model = get_embedding_model()

        embedding = model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        result = embedding.tolist()

        if len(result) != self.dimension:
            raise RuntimeError(
                f"Expected {self.dimension}-dimensional embedding, "
                f"got {len(result)}."
            )

        return result

    def embed_texts(
        self,
        texts: list[str],
        batch_size: int = 4,
    ) -> list[list[float]]:
        if not texts:
            return []

        if any(not text or not text.strip() for text in texts):
            raise ValueError("Texts cannot contain empty values.")

        model = get_embedding_model()

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        results = embeddings.tolist()

        if any(len(embedding) != self.dimension for embedding in results):
            raise RuntimeError(
                f"One or more embeddings are not "
                f"{self.dimension}-dimensional."
            )

        return results