
from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.retrieval.semantic_retriever import retrieve_hybrid_chunks


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()

        query = "Where is the wallet balance updated?"

        result = retrieve_hybrid_chunks(
            db=db,
            repository_id=REPOSITORY_ID,
            query=query,
            embedding_provider=embedding_provider,
            top_k=5,
            candidate_k=20,
        )

        print()
        print("=" * 80)
        print("HYBRID RETRIEVAL RESULTS")
        print("=" * 80)

        print(f"Query: {result['query']}")
        print(f"Keywords: {result['keywords']}")
        print(f"Actions: {result['actions']}")
        print()

        for index, item in enumerate(result["results"], start=1):
            print(f"Result #{index}")
            print("-" * 80)

            print(f"File                : {item['file_path']}")
            print(
                f"Lines               : "
                f"{item['start_line']}-{item['end_line']}"
            )
            print(f"Chunk               : {item['chunk_index']}")

            print(
                f"Semantic similarity : "
                f"{item['semantic_similarity']:.4f}"
            )

            print(
                f"Keyword score       : "
                f"{item['keyword_score']:.4f}"
            )

            print(
                f"Action score        : "
                f"{item['action_score']:.4f}"
            )

            print(
                f"Hybrid score        : "
                f"{item['hybrid_score']:.4f}"
            )

            print()
            print("Content:")
            print("-" * 80)
            print(item["content"][:1000])
            print()

            print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()