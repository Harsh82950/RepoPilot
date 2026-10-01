from app.db.session import SessionLocal
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.rag.rag_service import answer_repository_question


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()
        llm_provider = OllamaProvider()

        question = "Where is the wallet balance updated?"

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
            print(f"Hybrid     : {source['hybrid_score']:.4f}")

        print()
        print("=" * 80)
        print("REAL RAG TEST COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()