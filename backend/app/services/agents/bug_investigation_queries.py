import re
from typing import Any

from app.services.agents.bug_investigation_state import (
    BugInvestigationState,
)


def _clean_query(query: str) -> str:
    """
    Normalize a search query and remove obvious duplicate tokens.
    """

    query = re.sub(r"\s+", " ", query).strip()

    if not query:
        return ""

    words = query.split()
    cleaned_words: list[str] = []

    for word in words:
        normalized = word.lower().rstrip(":,.!?")

        if not cleaned_words:
            cleaned_words.append(word)
            continue

        previous_normalized = (
            cleaned_words[-1]
            .lower()
            .rstrip(":,.!?")
        )

        if normalized == previous_normalized:
            continue

        cleaned_words.append(word)

    return " ".join(cleaned_words)


def _build_semantic_queries(
    bug_report: str,
) -> list[str]:
    """
    Build broad repository-search queries for natural-language
    bug reports that do not contain explicit symbols or file paths.
    """

    text = bug_report.strip()

    if not text:
        return []

    queries: list[str] = []

    # Keep the original bug description as the strongest
    # semantic-search query.
    queries.append(text)

    # Extract useful domain words while removing common
    # conversational words.
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "but",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "with",
        "not",
        "does",
        "do",
        "doesn't",
        "did",
        "this",
        "that",
        "it",
        "my",
        "me",
        "i",
        "when",
        "after",
        "before",
        "expected",
        "actual",
        "please",
    }

    words = re.findall(
        r"[A-Za-z][A-Za-z0-9_-]*",
        text,
    )

    keywords: list[str] = []

    for word in words:
        normalized = word.lower()

        if normalized in stop_words:
            continue

        if len(normalized) < 3:
            continue

        if normalized not in keywords:
            keywords.append(normalized)

    if keywords:
        queries.append(" ".join(keywords[:8]))

    return queries


def build_bug_search_queries(
    state: BugInvestigationState,
) -> dict[str, Any]:
    """
    Build repository search queries from extracted bug signals.

    Strategy:

    1. Prefer exact functions and symbols when available.
    2. Use exact file paths when available.
    3. Fall back to semantic queries for natural-language
       bug reports without explicit code references.
    """

    queries: list[str] = []

    functions = state.get(
        "extracted_functions",
        [],
    )

    files = state.get(
        "extracted_files",
        [],
    )

    symbols = state.get(
        "extracted_symbols",
        [],
    )

    error_type = state.get(
        "error_type",
        "",
    )

    error_message = state.get(
        "error_message",
        "",
    )

    bug_report = state.get(
        "bug_report",
        "",
    )

    # ---------------------------------------------------------
    # 1. Exact function names
    # ---------------------------------------------------------

    for function_name in functions:
        query = _clean_query(function_name)

        if query and query not in queries:
            queries.append(query)

    # ---------------------------------------------------------
    # 2. Exact symbols
    # ---------------------------------------------------------

    for symbol in symbols:
        query = _clean_query(symbol)

        if query and query not in queries:
            queries.append(query)

    # ---------------------------------------------------------
    # 3. Exact file paths
    # ---------------------------------------------------------

    for file_path in files:
        query = _clean_query(file_path)

        if query and query not in queries:
            queries.append(query)

    # ---------------------------------------------------------
    # 4. Error information
    # ---------------------------------------------------------

    error_parts = []

    if error_type:
        error_parts.append(error_type)

    if error_message:
        error_parts.append(error_message)

    if error_parts:
        error_query = _clean_query(
            " ".join(error_parts)
        )

        if error_query and error_query not in queries:
            queries.append(error_query)

    # ---------------------------------------------------------
    # 5. Natural-language fallback
    # ---------------------------------------------------------

    if not functions and not files and not symbols:
        semantic_queries = _build_semantic_queries(
            bug_report
        )

        for query in semantic_queries:
            query = _clean_query(query)

            if query and query not in queries:
                queries.append(query)

    return {
        "search_queries": queries,
    }