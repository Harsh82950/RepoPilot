from typing import Any

from app.services.agents.bug_investigation_state import BugInvestigationState
from app.services.agents.repository_file_tool import (
    create_open_repository_file_tool,
)


def inspect_repository_files(
    state: BugInvestigationState,
    repository_path: str,
) -> dict[str, Any]:
    """
    Inspect exact repository files requested by the verification queries.

    The current implementation extracts file paths and optional line
    ranges from verification queries. If no explicit line range is
    provided, the tool opens the first 120 lines.
    """

    if not repository_path or not repository_path.strip():
        raise ValueError("Repository path cannot be empty.")

    verification_queries = state.get(
        "verification_queries",
        [],
    )

    if not verification_queries:
        return {
            "file_inspection_calls": [],
            "file_inspection_results": [],
            "file_inspection_count": 0,
        }

    open_file_tool = create_open_repository_file_tool(
        repository_path=repository_path,
    )

    inspection_calls = []
    inspection_results = []

    for query in verification_queries:
        query = query.strip()

        if not query:
            continue

        file_path = _extract_file_path(query)

        if not file_path:
            continue

        start_line, end_line = _extract_line_range(query)

        arguments = {
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
        }

        result = open_file_tool.invoke(arguments)

        inspection_calls.append(
            {
                "name": "open_repository_file",
                "arguments": arguments,
            }
        )

        inspection_results.append(
            {
                "query": query,
                "content": result,
            }
        )

    return {
        "file_inspection_calls": inspection_calls,
        "file_inspection_results": inspection_results,
        "file_inspection_count": len(inspection_calls),
    }


def _extract_file_path(query: str) -> str:
    """
    Extract a repository-relative source file path from a verification query.
    """

    extensions = (
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".java",
        ".cpp",
        ".cc",
        ".c",
        ".h",
        ".hpp",
        ".go",
        ".rs",
    )

    words = query.replace("`", " ").split()

    for word in words:
        cleaned = word.strip(
            " \t\n\r.,;:!?()[]{}\"'"
        )

        if cleaned.lower().endswith(extensions):
            return cleaned

    return ""


def _extract_line_range(
    query: str,
) -> tuple[int | None, int | None]:
    """
    Extract an optional line range such as:

    lines 72-120
    line 72
    """

    import re

    range_match = re.search(
        r"\blines?\s+(\d+)\s*[-–]\s*(\d+)\b",
        query,
        flags=re.IGNORECASE,
    )

    if range_match:
        return (
            int(range_match.group(1)),
            int(range_match.group(2)),
        )

    single_match = re.search(
        r"\bline\s+(\d+)\b",
        query,
        flags=re.IGNORECASE,
    )

    if single_match:
        line = int(single_match.group(1))
        return line, line

    return None, None