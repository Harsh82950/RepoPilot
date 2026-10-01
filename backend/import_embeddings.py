import json

from app.db.session import SessionLocal
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_chunk import RepositoryChunk

REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"
INPUT_FILE = "embeddings.json"
EXPECTED_DIMENSION = 1024


def main():
    db = SessionLocal()

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as file:
            records = json.load(file)

        print(f"Loaded embedding records: {len(records)}")

        if len(records) != 71:
            raise RuntimeError(
                f"Expected 71 embedding records, got {len(records)}."
            )

        updated_count = 0

        for record in records:
            chunk_id = record["id"]
            repository_id = record["repository_id"]
            embedding = record["embedding"]

            if repository_id != REPOSITORY_ID:
                raise RuntimeError(
                    f"Repository mismatch for chunk {chunk_id}."
                )

            if len(embedding) != EXPECTED_DIMENSION:
                raise RuntimeError(
                    f"Invalid embedding dimension for chunk "
                    f"{chunk_id}: {len(embedding)}"
                )

            chunk = (
                db.query(RepositoryChunk)
                .filter(RepositoryChunk.id == chunk_id)
                .first()
            )

            if chunk is None:
                raise RuntimeError(
                    f"Chunk not found in database: {chunk_id}"
                )

            if str(chunk.repository_id) != REPOSITORY_ID:
                raise RuntimeError(
                    f"Database repository mismatch for chunk {chunk_id}."
                )

            chunk.embedding = embedding
            updated_count += 1

        db.commit()

        print(f"Updated chunks: {updated_count}")
        print("Embeddings successfully imported.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()