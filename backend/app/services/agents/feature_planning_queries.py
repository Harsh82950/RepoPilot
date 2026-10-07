import re
from typing import Any

from app.services.agents.feature_planning_state import (
    FeaturePlanningState,
)


def _clean_query(query: str) -> str:
    query = re.sub(
        r"\s+",
        " ",
        query.strip(),
    )

    return query


def _extract_keywords(feature_request: str) -> list[str]:
    stop_words = {
        "add",
        "create",
        "implement",
        "build",
        "make",
        "support",
        "the",
        "a",
        "an",
        "to",
        "for",
        "in",
        "on",
        "with",
        "using",
        "into",
        "and",
        "or",
        "of",
        "is",
        "are",
        "this",
        "that",
    }

    words = re.findall(
        r"[A-Za-z][A-Za-z0-9_.-]*",
        feature_request,
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

    return keywords


def build_feature_search_queries(
    state: FeaturePlanningState,
) -> dict[str, Any]:

    feature_request = state.get(
        "feature_request",
        "",
    ).strip()

    if not feature_request:
        return {
            "search_queries": [],
        }

    queries: list[str] = []

    # Full feature request.
    full_query = _clean_query(
        feature_request
    )

    if full_query:
        queries.append(full_query)

    # Keyword-oriented query.
    keywords = _extract_keywords(
        feature_request
    )

    if keywords:
        keyword_query = _clean_query(
            " ".join(keywords[:10])
        )

        if (
            keyword_query
            and keyword_query not in queries
        ):
            queries.append(keyword_query)

    # Search for common architectural concepts
    # associated with feature implementation.
    architecture_query = _clean_query(
        f"{feature_request} service controller route repository model"
    )

    if architecture_query not in queries:
        queries.append(
            architecture_query
        )

    return {
        "search_queries": queries,
    }