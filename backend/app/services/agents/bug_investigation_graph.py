from langgraph.graph import END, START, StateGraph

from app.services.agents.bug_diagnosis import diagnose_bug
from app.services.agents.bug_file_inspection import inspect_repository_files
from app.services.agents.bug_investigation_queries import build_bug_search_queries
from app.services.agents.bug_investigation_search import search_repository_for_bug
from app.services.agents.bug_investigation_state import BugInvestigationState
from app.services.agents.bug_verification_search import (
    search_repository_for_verification,
)


MAX_VERIFICATION_ATTEMPTS = 1


def build_bug_investigation_graph(
    db,
    embedding_provider,
    initial_llm_provider,
    final_llm_provider,
):
    def extract_signals_node(state):
        from app.services.agents.bug_investigation_nodes import (
            extract_bug_signals,
        )

        return extract_bug_signals(state)

    def build_queries_node(state):
        return build_bug_search_queries(state)

    def search_node(state):
        return search_repository_for_bug(
            state=state,
            db=db,
            embedding_provider=embedding_provider,
        )

    def initial_diagnosis_node(state):
        """
        Perform the first diagnosis using the cheaper/faster model.

        This pass identifies:
        - repository facts
        - possible hypotheses
        - likely locations
        - source-code verification queries
        """
        return diagnose_bug(
            state=state,
            llm_provider=initial_llm_provider,
        )

    def prepare_verification_attempt(state):
        return {
            "verification_attempts": state.get("verification_attempts", 0) + 1
        }

    def verification_search_node(state):
        return search_repository_for_verification(
            state=state,
            db=db,
            embedding_provider=embedding_provider,
        )

    def file_inspection_node(state):
        from app.models.repository import Repository

        repository_id = state.get("repository_id", "").strip()

        repository = (
            db.query(Repository)
            .filter(Repository.id == repository_id)
            .first()
        )

        if repository is None:
            raise ValueError(
                f"Repository not found: {repository_id}"
            )

        if not repository.local_path:
            raise ValueError(
                "Repository local path is not available."
            )

        return inspect_repository_files(
            state=state,
            repository_path=repository.local_path,
        )

    def final_diagnosis_node(state):
        """
        Perform the final evidence-based diagnosis using the stronger model.

        At this point the state contains:
        - initial diagnosis
        - verification search results
        - exact file inspection results
        """
        return diagnose_bug(
            state=state,
            llm_provider=final_llm_provider,
        )

    def should_verify(state):
        verification_queries = state.get(
            "verification_queries",
            [],
        )

        attempts = state.get(
            "verification_attempts",
            0,
        )

        if (
            verification_queries
            and attempts < MAX_VERIFICATION_ATTEMPTS
        ):
            return "verify"

        return "end"

    graph = StateGraph(BugInvestigationState)

    graph.add_node(
        "extract_signals",
        extract_signals_node,
    )

    graph.add_node(
        "build_queries",
        build_queries_node,
    )

    graph.add_node(
        "search_repository",
        search_node,
    )

    graph.add_node(
        "initial_diagnosis",
        initial_diagnosis_node,
    )

    graph.add_node(
        "prepare_verification",
        prepare_verification_attempt,
    )

    graph.add_node(
        "verify_repository",
        verification_search_node,
    )

    graph.add_node(
        "inspect_repository_files",
        file_inspection_node,
    )

    graph.add_node(
        "final_diagnosis",
        final_diagnosis_node,
    )

    graph.add_edge(
        START,
        "extract_signals",
    )

    graph.add_edge(
        "extract_signals",
        "build_queries",
    )

    graph.add_edge(
        "build_queries",
        "search_repository",
    )

    graph.add_edge(
        "search_repository",
        "initial_diagnosis",
    )

    graph.add_conditional_edges(
        "initial_diagnosis",
        should_verify,
        {
            "verify": "prepare_verification",
            "end": END,
        },
    )

    graph.add_edge(
        "prepare_verification",
        "verify_repository",
    )

    graph.add_edge(
        "verify_repository",
        "inspect_repository_files",
    )

    graph.add_edge(
        "inspect_repository_files",
        "final_diagnosis",
    )

    graph.add_edge(
        "final_diagnosis",
        END,
    )

    return graph.compile()