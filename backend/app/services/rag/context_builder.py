from typing import Any


def build_rag_context(results: list[dict[str, Any]]) -> str:
    """
    Build a source-aware context string from retrieved repository chunks.

    Each result should contain:
    - file_path
    - start_line
    - end_line
    - content

    Every retrieved chunk receives a unique source ID so that the LLM
    can associate claims with the exact repository evidence supporting them.
    """

    if not results:
        return "No relevant repository context was found."

    context_parts = []

    for index, result in enumerate(results, start=1):
        file_path = result.get("file_path", "Unknown file")
        start_line = result.get("start_line", "?")
        end_line = result.get("end_line", "?")
        content = result.get("content", "").strip()

        context_parts.append(
            f"[Source {index}]\n"
            f"File: {file_path}\n"
            f"Lines: {start_line}-{end_line}\n"
            f"Evidence:\n"
            f"{content}"
        )

    separator = "\n\n" + "=" * 80 + "\n\n"

    return separator.join(context_parts)
