from typing import Any


def build_rag_context(results: list[dict[str, Any]]) -> str:
    """
    Build a structured context string from retrieved repository chunks.

    Each result should contain:
    - file_path
    - start_line
    - end_line
    - content
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
            f"\n"
            f"{content}"
        )

    return "\n\n" + ("\n\n" + "=" * 80 + "\n\n").join(context_parts)