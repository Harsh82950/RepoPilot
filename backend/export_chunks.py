import json

from app.db.session import SessionLocal
from app.models.repository_chunk import RepositoryChunk


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"
OUTPUT_FILE = "chunks_for_embedding.json"


def main():
    db = SessionLocal()

    try:
        chunks = (
            db.query(RepositoryChunk)
            .filter(
                RepositoryChunk.repository_id == REPOSITORY_ID
            )
            .order_by(
                RepositoryChunk.repository_file_id,
                RepositoryChunk.chunk_index,
            )
            .all()
        )

        if not chunks:
            raise RuntimeError("No chunks found.")

        records = []

        for chunk in chunks:
            records.append(
                {
                    "id": str(chunk.id),
                    "repository_id": str(chunk.repository_id),
                    "repository_file_id": str(chunk.repository_file_id),
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                }
            )

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                records,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(f"Exported chunks: {len(records)}")
        print(f"Output file: {OUTPUT_FILE}")

    finally:
        db.close()


if __name__ == "__main__":
    main()