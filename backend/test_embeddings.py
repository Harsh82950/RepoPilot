from app.db.session import SessionLocal
from app.models.repository import Repository
from app.services.embeddings.chunk_embedding_service import (
    embed_repository_chunks,
)


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        repository = (
            db.query(Repository)
            .filter(Repository.id == REPOSITORY_ID)
            .first()
        )

        if repository is None:
            raise RuntimeError("Repository not found.")

        print(f"Repository: {repository.name}")
        print("Generating embeddings...")

        count = embed_repository_chunks(
            db=db,
            repository=repository,
            batch_size=4,
        )

        db.commit()

        print(f"Embedded chunks: {count}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()