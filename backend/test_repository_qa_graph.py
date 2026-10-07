from app.db.session import SessionLocal
from app.services.agents.repository_qa_graph import build_repository_qa_graph
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.groq_provider import GroqProvider


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"


def main():
    db = SessionLocal()

    try:
        embedding_provider = QwenEmbeddingProvider()
        llm_provider = GroqProvider()

        graph = build_repository_qa_graph(
            db=db,
            embedding_provider=embedding_provider,
            llm_provider=llm_provider,
        )

        initial_state = {
            "repository_id": REPOSITORY_ID,
            "question" :"How does a customer payment using the wallet flow through the repository?",
            "tool_messages": [],
            "tool_call_count": 0,
        }

        result = graph.invoke(initial_state)

        print()
        print("=" * 80)
        print("AGENTIC REPOSITORY QA TEST")
        print("=" * 80)

        print()
        print("Question:")
        print(result["question"])

        print()
        print("Final Answer:")
        print("-" * 80)
        print(result.get("answer"))

        print()
        print("Tool Calls Executed:")
        print(result.get("tool_call_count", 0))

        print()
        print("Tool Messages:")
        print("-" * 80)

        for message in result.get("tool_messages", []):
            print(message)

        print()
        print("=" * 80)
        print("AGENTIC TEST COMPLETE")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()