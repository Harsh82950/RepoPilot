from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.mock_llm_provider import MockLLMProvider
from app.services.rag.rag_service import answer_repository_question


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


EVALUATION_QUERIES = [
    {
        "question": "Where is the wallet balance updated?",
        "expected_path": "src/modules/wallet",
    },
    {
        "question": "Where is wallet top-up implemented?",
        "expected_path": "src/modules/wallet",
    },
    {
        "question": "Where is customer authentication implemented?",
        "expected_path": "src/modules/auth",
    },
    {
        "question": "Where is payment order creation handled?",
        "expected_path": "src/modules/payment",
    },
    {
        "question": "Where is the mock gateway charge implemented?",
        "expected_path": "src/modules/payment/gateway.service.ts",
    },
]


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()
        llm_provider = MockLLMProvider()

        passed = 0

        print()
        print("=" * 80)
        print("REPOPILOT RAG EVALUATION")
        print("=" * 80)

        for index, item in enumerate(EVALUATION_QUERIES, start=1):
            question = item["question"]
            expected_path = item["expected_path"]

            print()
            print(f"[{index}/{len(EVALUATION_QUERIES)}] {question}")
            print("-" * 80)

            result = answer_repository_question(
                db=db,
                repository_id=REPOSITORY_ID,
                question=question,
                embedding_provider=embedding_provider,
                llm_provider=llm_provider,
                top_k=5,
                candidate_k=20,
            )

            sources = result["sources"]

            matched = any(
                expected_path.lower() in source["file_path"].lower()
                for source in sources
            )

            if matched:
                passed += 1
                print("RESULT: PASS")
            else:
                print("RESULT: MISS")

            print(f"Expected area: {expected_path}")

            print()
            print("Retrieved sources:")

            for source_index, source in enumerate(sources, start=1):
                print(
                    f"  #{source_index} "
                    f"{source['file_path']} "
                    f"[{source['start_line']}-{source['end_line']}] "
                    f"score={source['hybrid_score']:.4f}"
                )

            print()
            print("Answer:")
            print(result["answer"])

        total = len(EVALUATION_QUERIES)
        recall = passed / total if total else 0.0

        print()
        print("=" * 80)
        print("RAG EVALUATION SUMMARY")
        print("=" * 80)
        print(f"Passed    : {passed}/{total}")
        print(f"Recall@5  : {recall:.2%}")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()