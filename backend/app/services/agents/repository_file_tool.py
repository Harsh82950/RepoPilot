from pathlib import Path

from langchain_core.tools import tool


MAX_LINES_PER_READ = 120


def read_repository_file(
    repository_path: str,
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """
    Read a specific file or line range from a repository.

    Line numbers are 1-based and inclusive.
    """

    if not repository_path or not repository_path.strip():
        raise ValueError("Repository path cannot be empty.")

    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty.")

    repository_root = Path(repository_path).resolve()

    relative_path = Path(
        file_path.replace("\\", "/")
    )

    if relative_path.is_absolute():
        raise ValueError("Absolute file paths are not allowed.")

    full_path = (repository_root / relative_path).resolve()

    try:
        full_path.relative_to(repository_root)
    except ValueError as exc:
        raise ValueError(
            "Requested file is outside the repository."
        ) from exc

    if not full_path.exists():
        return f"File not found: {file_path}"

    if not full_path.is_file():
        return f"Path is not a file: {file_path}"

    try:
        with full_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        with full_path.open(
            "r",
            encoding="utf-8",
            errors="replace",
        ) as file:
            lines = file.readlines()

    total_lines = len(lines)

    if start_line is None:
        start_line = 1

    if end_line is None:
        end_line = min(
            total_lines,
            start_line + MAX_LINES_PER_READ - 1,
        )

    start_line = max(1, start_line)
    end_line = min(total_lines, end_line)

    if start_line > end_line:
        return (
            f"Invalid line range: "
            f"{start_line}-{end_line}"
        )

    requested_lines = end_line - start_line + 1

    if requested_lines > MAX_LINES_PER_READ:
        end_line = start_line + MAX_LINES_PER_READ - 1
        end_line = min(end_line, total_lines)

    selected_lines = lines[
        start_line - 1:end_line
    ]

    numbered_lines = []

    for line_number, line in enumerate(
        selected_lines,
        start=start_line,
    ):
        numbered_lines.append(
            f"{line_number}: {line.rstrip()}"
        )

    return (
        f"File: {file_path}\n"
        f"Lines: {start_line}-{end_line} "
        f"of {total_lines}\n\n"
        + "\n".join(numbered_lines)
    )


def create_open_repository_file_tool(repository_path: str):
    @tool
    def open_repository_file(
        file_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> str:
        """
        Open an exact file or line range from the repository.

        Use this after repository search identifies a relevant
        file, function, or implementation that needs closer inspection.
        """

        return read_repository_file(
            repository_path=repository_path,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
        )

    return open_repository_file