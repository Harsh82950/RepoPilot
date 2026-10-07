from typing import Any

from app.services.agents.bug_investigation_state import (
    BugInvestigationState,
)
from app.services.agents.repository_tools import create_search_repository_tool


def search_repository_for_verification(
    state: BugInvestigationState,
    db,
    embedding_provider,
) -> dict[str, Any]:
    """
    Search the repository using verification queries generated
    by the initial bug diagnosis.

    These searches are intended to verify hypotheses rather than
    perform the initial investigation.
    """

    repository_id = state.get("repository_id", "").strip()
    verification_queries = state.get("verification_queries", [])

    if not repository_id:
        raise ValueError("Repository ID cannot be empty.")

    if not verification_queries:
        return {
            "verification_results": [],
            "verification_tool_calls": [],
            "verification_tool_messages": [],
        }

    search_tool = create_search_repository_tool(
        db=db,
        embedding_provider=embedding_provider,
        repository_id=repository_id,
    )

    verification_results = []
    verification_tool_calls = []
    verification_tool_messages = []

    for query in verification_queries:
        query = query.strip()

        if not query:
            continue

        result = search_tool.invoke({
            "query": query
        })

        verification_tool_calls.append({
            "name": "search_repository",
            "arguments": {
                "query": query
            },
        })

        verification_tool_messages.append({
            "role": "tool",
            "name": "search_repository",
            "content": result,
        })

        verification_results.append({
            "query": query,
            "content": result,
        })

    return {
        "verification_results": verification_results,
        "verification_tool_calls": verification_tool_calls,
        "verification_tool_messages": verification_tool_messages,
        "verification_tool_count": len(
            verification_tool_calls
        ),
    }