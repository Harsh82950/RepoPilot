from __future__ import annotations

import re
from typing import Any


MAX_RESULTS_PER_SECTION = 2
MAX_INITIAL_CHARS = 9000
MAX_FINAL_CHARS = 7000


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _deduplicate_results(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen = set()

    for result in results:
        if not isinstance(result, dict):
            continue

        content = str(
            result.get("content", "")
        ).strip()

        if not content:
            continue

        normalized = _normalize_text(content)

        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(result)

    return unique


def _limit_results(
    results: list[dict[str, Any]],
    limit: int = MAX_RESULTS_PER_SECTION,
) -> list[dict[str, Any]]:
    results = _deduplicate_results(results)
    return results[:limit]


def _format_section(
    title: str,
    results: list[dict[str, Any]],
) -> str:
    if not results:
        return ""

    parts = [title]

    for index, result in enumerate(
        results,
        start=1,
    ):
        content = str(
            result.get("content", "")
        ).strip()

        if not content:
            continue

        parts.append(
            f"[Evidence {index}]\n{content}"
        )

    return "\n\n".join(parts)


def _truncate_evidence(
    evidence: str,
    max_chars: int,
) -> str:
    if len(evidence) <= max_chars:
        return evidence

    return (
        evidence[:max_chars]
        + "\n\n"
        "[Evidence truncated to fit "
        "the diagnosis context limit.]"
    )


def build_compressed_evidence(
    state,
    max_chars: int = MAX_INITIAL_CHARS,
) -> str:
    """
    Build compact evidence for the initial diagnosis.

    Includes:
    1. Initial repository search results
    2. Verification search results
    3. Exact file inspection results
    """

    sections: list[str] = []

    retrieval_results = _limit_results(
        state.get(
            "retrieval_results",
            [],
        )
    )

    verification_results = _limit_results(
        state.get(
            "verification_results",
            [],
        )
    )

    file_inspection_results = _limit_results(
        state.get(
            "file_inspection_results",
            [],
        )
    )

    section = _format_section(
        "INITIAL REPOSITORY SEARCH RESULTS:",
        retrieval_results,
    )

    if section:
        sections.append(section)

    section = _format_section(
        "VERIFICATION SEARCH RESULTS:",
        verification_results,
    )

    if section:
        sections.append(section)

    section = _format_section(
        "EXACT FILE INSPECTION RESULTS:",
        file_inspection_results,
    )

    if section:
        sections.append(section)

    evidence = "\n\n" + (
        "\n" + "=" * 80 + "\n"
    ).join(sections)

    return _truncate_evidence(
        evidence,
        max_chars,
    )


def build_final_diagnosis_evidence(
    state,
    max_chars: int = MAX_FINAL_CHARS,
) -> str:
    """
    Build compact evidence for the final diagnosis.

    The final diagnosis retains a small amount of
    initial repository evidence so that important
    context is not lost after verification.

    Evidence order:
    1. Initial repository search
    2. Verification search
    3. Exact file inspection
    """

    sections: list[str] = []

    retrieval_results = _limit_results(
        state.get(
            "retrieval_results",
            [],
        )
    )

    verification_results = _limit_results(
        state.get(
            "verification_results",
            [],
        )
    )

    file_inspection_results = _limit_results(
        state.get(
            "file_inspection_results",
            [],
        )
    )

    section = _format_section(
        "INITIAL REPOSITORY SEARCH RESULTS:",
        retrieval_results,
    )

    if section:
        sections.append(section)

    section = _format_section(
        "VERIFICATION SEARCH RESULTS:",
        verification_results,
    )

    if section:
        sections.append(section)

    section = _format_section(
        "EXACT FILE INSPECTION RESULTS:",
        file_inspection_results,
    )

    if section:
        sections.append(section)

    evidence = "\n\n" + (
        "\n" + "=" * 80 + "\n"
    ).join(sections)

    return _truncate_evidence(
        evidence,
        max_chars,
    )