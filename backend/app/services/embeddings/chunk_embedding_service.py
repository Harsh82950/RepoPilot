from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.models.repository_chunk import RepositoryChunk
from app.services.embeddings.embedding_service import embed_texts


def embed_repository_chunks(
    db: Session,
    repository: Repository,
    batch_size: int = 4,
) -> int:
    """
    Generate embeddings for all chunks belonging to a repository
    and persist them in repository_chunks.embedding.

    Returns the number of chunks embedded.
    """

    chunks = (
        db.query(RepositoryChunk)
        .filter(RepositoryChunk.repository_id == repository.id)
        .order_by(
            RepositoryChunk.repository_file_id,
            RepositoryChunk.chunk_index,
        )
        .all()
    )

    if not chunks:
        return 0

    texts = [chunk.content for chunk in chunks]

    embeddings = embed_texts(
        texts=texts,
        batch_size=batch_size,
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match chunk count."
        )

    for chunk, embedding in zip(chunks, embeddings):
        if len(embedding) != 1024:
            raise RuntimeError(
                f"Unexpected embedding dimension: {len(embedding)}"
            )

        chunk.embedding = embedding

    db.flush()

    return len(chunks)