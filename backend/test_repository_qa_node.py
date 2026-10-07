from app.db.session import SessionLocal
from app.services.agents.repository_qa_nodes import retrieve_repository_context
from app.services.embeddings.embedding_service import QwenEmbeddingProvider


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        state = {
            "repository_id": REPOSITORY_ID,
            "question": "Where is balance.increment used in the wallet repository?",
            "retrieval_attempts": 0,
        }

        embedding_provider = QwenEmbeddingProvider()

        result = retrieve_repository_context(
            state=state,
            db=db,
            embedding_provider=embedding_provider,
        )

        print()
        print("=" * 80)
        print("REPOSITORY QA RETRIEVAL NODE TEST")
        print("=" * 80)

        print()
        print("Question:")
        print(result["question"])

        print()
        print("Retrieval Attempts:")
        print(result["retrieval_attempts"])

        print()
        print("Keywords:")
        print(result["keywords"])

        print()
        print("Actions:")
        print(result["actions"])

        print()
        print("Retrieved Sources:")
        print("-" * 80)

        for index, source in enumerate(
            result["retrieval_results"],
            start=1,
        ):
            print(f"\nSource #{index}")
            print(f"File       : {source['file_path']}")
            print(
                f"Lines      : "
                f"{source['start_line']}-{source['end_line']}"
            )
            print(
                f"Hybrid     : "
                f"{source['hybrid_score']:.4f}"
            )

        print()
        print("=" * 80)
        print("RETRIEVAL NODE TEST COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()