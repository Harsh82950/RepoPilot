import json

from app.db.session import SessionLocal
from app.services.agents.bug_investigation_graph import (
    build_bug_investigation_graph,
)
from app.services.embeddings.embedding_service import QwenEmbeddingProvider
from app.services.llm.groq_provider import GroqProvider


REPOSITORY_ID = "c52a3bb9-cbaa-4370-89d2-dcfcbc8a9043"

BUG_REPORT = """
Refund succeeds, but the wallet refund amount is calculated incorrectly.
A customer who used part of their wallet balance for a payment receives
the wrong wallet credit when the refund is processed.
The refund amount should correspond to the wallet amount originally used.
"""


def main():
    print("Starting Bug Investigation Agent test...\n")

    db = SessionLocal()

    try:
        print("Initializing embedding provider...")
        embedding_provider = QwenEmbeddingProvider()

        print("Initializing initial diagnosis model: GPT-OSS 20B...")
        initial_llm_provider = GroqProvider(
            model_name="openai/gpt-oss-20b",
            
        )

        print("Initializing final diagnosis model: GPT-OSS 120B...")
        final_llm_provider = GroqProvider(
            model_name="openai/gpt-oss-120b"
        )

        print("Building bug investigation graph...")

        graph = build_bug_investigation_graph(
            db=db,
            embedding_provider=embedding_provider,
            initial_llm_provider=initial_llm_provider,
            final_llm_provider=final_llm_provider,
        )

        initial_state = {
            "repository_id": REPOSITORY_ID,
            "bug_report": BUG_REPORT.strip(),
            "error_message": "",
            "error_type": "",
            "stack_trace": "",
            "extracted_symbols": [],
            "extracted_files": [],
            "extracted_functions": [],
            "search_queries": [],
            "retrieval_results": [],
            "tool_calls": [],
            "tool_messages": [],
            "tool_call_count": 0,
            "likely_locations": [],
            "hypotheses": [],
            "verification_queries": [],
            "verification_results": [],
            "verification_tool_calls": [],
            "verification_tool_messages": [],
            "verification_tool_count": 0,
            "verification_attempts": 0,
            "file_inspection_calls": [],
            "file_inspection_results": [],
            "file_inspection_count": 0,
            "diagnosis": "",
            "root_cause": "",
            "debugging_steps": [],
            "confidence": "",
            "messages": [],
        }

        print("\nRunning investigation...\n")

        result = graph.invoke(initial_state)

        print("=" * 80)
        print("FINAL BUG INVESTIGATION RESULT")
        print("=" * 80)

        diagnosis = result.get("diagnosis", "")

        if diagnosis:
            try:
                parsed_diagnosis = json.loads(diagnosis)

                print(
                    json.dumps(
                        parsed_diagnosis,
                        indent=2,
                    )
                )

            except json.JSONDecodeError:
                print(diagnosis)

        else:
            print("No diagnosis returned.")

        print("\n" + "=" * 80)
        print("INVESTIGATION METADATA")
        print("=" * 80)

        print(
            f"Verification attempts: "
            f"{result.get('verification_attempts', 0)}"
        )

        print(
            f"Repository search calls: "
            f"{len(result.get('tool_calls', []))}"
        )

        print(
            f"Verification search calls: "
            f"{len(result.get('verification_tool_calls', []))}"
        )

        print(
            f"File inspection calls: "
            f"{len(result.get('file_inspection_calls', []))}"
        )

        print(
            f"Verification queries: "
            f"{result.get('verification_queries', [])}"
        )

        print("\nTest completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()