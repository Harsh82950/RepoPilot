from typing import Any

from app.services.agents.bug_investigation_state import (
    BugInvestigationState,
)
from app.services.agents.repository_tools import (
    create_search_repository_tool,
)


def search_repository_for_bug(
    state: BugInvestigationState,
    db,
    embedding_provider,
) -> dict[str, Any]:
    """
    Search the repository using the queries generated from the bug report.
    """

    repository_id = state.get("repository_id", "").strip()
    queries = state.get("search_queries", [])

    if not repository_id:
        raise ValueError("Repository ID cannot be empty.")

    if not queries:
        return {
            "retrieval_results": [],
            "tool_calls": [],
            "tool_messages": [],
        }

    search_tool = create_search_repository_tool(
        db=db,
        embedding_provider=embedding_provider,
        repository_id=repository_id,
    )

    retrieval_results: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []
    tool_messages: list[dict[str, Any]] = []

    for query in queries:
        if not query.strip():
            continue

        result = search_tool.invoke(
            {
                "query": query,
            }
        )

        tool_calls.append(
            {
                "name": "search_repository",
                "arguments": {
                    "query": query,
                },
            }
        )

        tool_messages.append(
            {
                "role": "tool",
                "name": "search_repository",
                "content": result,
            }
        )

        retrieval_results.append(
            {
                "query": query,
                "content": result,
            }
        )

    return {
        "retrieval_results": retrieval_results,
        "tool_calls": tool_calls,
        "tool_messages": tool_messages,
        "tool_call_count": len(tool_calls),
    }