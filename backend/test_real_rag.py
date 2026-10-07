from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.groq_provider import GroqProvider
from app.services.rag.rag_service import answer_repository_question


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()
        llm_provider = llm_provider = GroqProvider()

        question = question = "Where is balance.increment used in the wallet repository?"

        result = answer_repository_question(
            db=db,
            repository_id=REPOSITORY_ID,
            question=question,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
            top_k=3,
            candidate_k=20,
        )

        print()
        print("=" * 80)
        print("REPOPILOT REAL RAG TEST")
        print("=" * 80)

        print()
        print("Question:")
        print(result["question"])

        print()
        print("Answer:")
        print("-" * 80)
        print(result["answer"])

        print()
        print("Evidence:")
        print("-" * 80)

        for evidence in result["evidence"]:
            print(f"\n[{evidence['source_id']}]")
            print(f"File  : {evidence['file_path']}")
            print(
                f"Lines : "
                f"{evidence['start_line']}-{evidence['end_line']}"
            )

        print()
        print("Sources:")
        print("-" * 80)

        for index, source in enumerate(result["sources"], start=1):
            print(f"\nSource #{index}")
            print(f"File       : {source['file_path']}")
            print(f"Lines      : {source['start_line']}-{source['end_line']}")
            print(f"Chunk      : {source['chunk_index']}")
            print(f"Similarity : {source['semantic_similarity']:.4f}")
            print(f"Keyword    : {source['keyword_score']:.4f}")
            print(f"Action     : {source['action_score']:.4f}")
            print(
                 f"Code Expr  : "
                 f"{source['code_expression_score']:.4f}"
            )
            print(f"Hybrid     : {source['hybrid_score']:.4f}")

        print()
        print("=" * 80)
        print("REAL RAG TEST COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()