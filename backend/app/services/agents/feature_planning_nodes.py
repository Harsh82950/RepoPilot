from typing import Any

from app.services.agents.feature_planning_state import (
    FeaturePlanningState,
)


def prepare_feature_request(
    state: FeaturePlanningState,
) -> dict[str, Any]:

    feature_request = state.get(
        "feature_request",
        "",
    ).strip()

    if not feature_request:
        raise ValueError(
            "Feature request cannot be empty."
        )

    return {
        "feature_request": feature_request,
    }


def prepare_feature_search(
    state: FeaturePlanningState,
) -> dict[str, Any]:

    existing_queries = state.get(
        "search_queries",
        [],
    )

    cleaned_queries: list[str] = []

    for query in existing_queries:

        if not isinstance(query, str):
            continue

        query = query.strip()

        if (
            query
            and query not in cleaned_queries
        ):
            cleaned_queries.append(query)

    return {
        "search_queries": cleaned_queries,
    }