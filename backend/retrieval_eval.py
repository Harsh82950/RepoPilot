
from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.retrieval.semantic_retriever import retrieve_hybrid_chunks


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


EVALUATION_QUERIES = [
    {
        "question": "Where is the wallet balance updated?",
        "expected_paths": [
            "src/modules/wallet",
        ],
    },
    {
        "question": "Where is wallet top-up implemented?",
        "expected_paths": [
            "src/modules/wallet",
        ],
    },
    {
        "question": "Where is wallet money reserved?",
        "expected_paths": [
            "src/modules/wallet",
        ],
    },
    {
        "question": "Where are refunds credited to the wallet?",
        "expected_paths": [
            "src/modules/refund",
            "src/modules/wallet",
        ],
    },
    {
        "question": "Where is customer authentication implemented?",
        "expected_paths": [
            "src/modules/auth",
            "src/modules/customer",
        ],
    },
    {
        "question": "Where is payment order creation handled?",
        "expected_paths": [
            "src/modules/payment",
        ],
    },
    {
        "question": "Where is Redis used?",
        "expected_paths": [
            "src",
        ],
    },
   {
    "question": "Where is the mock gateway charge implemented?",
    "expected_paths": [
        "src/modules/payment/gateway.service.ts",
    ],
},
    {
        "question": "Where is idempotency implemented?",
        "expected_paths": [
            "src/common/idempotency",
        ],
    },
    {
        "question": "Where is the database connection configured?",
        "expected_paths": [
            "src/config",
        ],
    },
]


def is_relevant(file_path: str, expected_paths: list[str]) -> bool:
    """
    Check whether a retrieved file belongs to one of the
    expected repository areas.
    """

    normalized_path = file_path.replace("\\", "/").lower()

    return any(
        expected_path.lower() in normalized_path
        for expected_path in expected_paths
    )


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()

        total_queries = len(EVALUATION_QUERIES)
        successful_queries = 0

        print()
        print("=" * 80)
        print("REPOPILOT RETRIEVAL EVALUATION")
        print("=" * 80)
        print(f"Repository: {REPOSITORY_ID}")
        print(f"Queries: {total_queries}")
        print()

        for index, evaluation in enumerate(
            EVALUATION_QUERIES,
            start=1,
        ):
            question = evaluation["question"]
            expected_paths = evaluation["expected_paths"]

            print()
            print(f"[{index}/{total_queries}] {question}")
            print("-" * 80)

            result = retrieve_hybrid_chunks(
                db=db,
                repository_id=REPOSITORY_ID,
                query=question,
                embedding_provider=embedding_provider,
                top_k=5,
                candidate_k=20,
            )

            found_relevant = False

            for rank, item in enumerate(
                result["results"],
                start=1,
            ):
                relevant = is_relevant(
                    file_path=item["file_path"],
                    expected_paths=expected_paths,
                )

                marker = "✓" if relevant else " "

                print(
                    f"{marker} #{rank} "
                    f"{item['file_path']} "
                    f"[{item['start_line']}-{item['end_line']}] "
                    f"score={item['hybrid_score']:.4f}"
                )

                if relevant:
                    found_relevant = True

            if found_relevant:
                successful_queries += 1
                print("RESULT: PASS")
            else:
                print("RESULT: MISS")

            print(
                "Expected areas: "
                + ", ".join(expected_paths)
            )

        print()
        print("=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)

        print(f"Total queries : {total_queries}")
        print(f"Passed        : {successful_queries}")
        print(f"Missed        : {total_queries - successful_queries}")

        recall_at_5 = (
            successful_queries / total_queries
            if total_queries
            else 0.0
        )

        print(f"Recall@5      : {recall_at_5:.2%}")

        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()