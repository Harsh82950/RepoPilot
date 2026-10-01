from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.rag.rag_service import answer_repository_question


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


EVALUATION_QUERIES = [
    "Where is the wallet balance updated?",
    "Where is wallet top-up implemented?",
    "Where is customer authentication implemented?",
    "Where is payment order creation handled?",
    "Where is the mock gateway charge implemented?",
]


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()
        llm_provider = OllamaProvider()

        print()
        print("=" * 80)
        print("REPOPILOT REAL LLM RAG EVALUATION")
        print("=" * 80)

        for index, question in enumerate(EVALUATION_QUERIES, start=1):
            print()
            print(f"[{index}/{len(EVALUATION_QUERIES)}] {question}")
            print("-" * 80)

            try:
                result = answer_repository_question(
                    db=db,
                    repository_id=REPOSITORY_ID,
                    question=question,
                    embedding_provider=embedding_provider,
                    llm_provider=llm_provider,
                    top_k=5,
                    candidate_k=20,
                )

                print()
                print("ANSWER:")
                print(result["answer"])

                print()
                print("SOURCES:")

                for source_index, source in enumerate(
                    result["sources"],
                    start=1,
                ):
                    print(
                        f"  #{source_index} "
                        f"{source['file_path']} "
                        f"[{source['start_line']}-{source['end_line']}] "
                        f"score={source['hybrid_score']:.4f}"
                    )

            except Exception as exc:
                print()
                print("ERROR:")
                print(exc)

            print()
            print("=" * 80)

        print()
        print("REAL LLM RAG EVALUATION COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()