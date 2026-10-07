from pathlib import Path
from typing import Any


def _normalize_path(path: str) -> str:
    """
    Normalize a repository-relative path for comparison.
    """
    return path.replace("\\", "/").strip().lstrip("./")


def validate_existing_files(
    repository_root: str,
    affected_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Validate that files identified by the feature planner actually exist
    inside the repository.

    Returns the same file entries with an additional `exists` field.
    """

    root = Path(repository_root).resolve()

    validated_files: list[dict[str, Any]] = []

    for item in affected_files:
        if not isinstance(item, dict):
            continue

        file_path = item.get("file")

        if not isinstance(file_path, str) or not file_path.strip():
            continue

        normalized = _normalize_path(file_path)

        candidate = (root / normalized).resolve()

        # Prevent paths outside the repository.
        try:
            candidate.relative_to(root)
        except ValueError:
            validated_files.append(
                {
                    **item,
                    "file": normalized,
                    "exists": False,
                    "validation": "Path is outside the repository.",
                }
            )
            continue

        exists = candidate.is_file()

        validated_files.append(
            {
                **item,
                "file": normalized,
                "exists": exists,
                "validation": (
                    "Existing repository file."
                    if exists
                    else "File does not exist in the repository."
                ),
            }
        )

    return validated_files


def separate_existing_and_missing_files(
    affected_files: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Separate planner-proposed files into existing and missing files.
    """

    existing_files: list[dict[str, Any]] = []
    missing_files: list[dict[str, Any]] = []

    for item in affected_files:
        if item.get("exists") is True:
            existing_files.append(item)
        else:
            missing_files.append(item)

    return existing_files, missing_files