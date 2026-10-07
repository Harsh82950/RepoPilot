from app.db.session import SessionLocal
from app.services.agents.bug_investigation_search import (
    search_repository_for_bug,
)
from app.services.embeddings.embedding_service import (
    QwenEmbeddingProvider,
)


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    state = {
        "repository_id": REPOSITORY_ID,
        "search_queries": [
            "processRefund",
            "payOrder",
        ],
    }

    db = SessionLocal()
    embedding_provider = QwenEmbeddingProvider()

    try:
        result = search_repository_for_bug(
            state=state,
            db=db,
            embedding_provider=embedding_provider,
        )

        print("\n=== Bug Investigation Search ===")

        print(
            "\nTool calls:",
            result["tool_call_count"],
        )

        for index, item in enumerate(
            result["retrieval_results"],
            start=1,
        ):
            print("\n" + "=" * 80)
            print(f"QUERY {index}: {item['query']}")
            print("=" * 80)
            print(item["content"])

    finally:
        db.close()


if __name__ == "__main__":
    main()