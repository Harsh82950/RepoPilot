from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.models.repository import Repository

from app.services.agents.feature_planning import (
    plan_feature,
)

from app.services.agents.feature_planning_queries import (
    build_feature_search_queries,
)

from app.services.agents.feature_planning_search import (
    search_repository_for_feature,
)

from app.services.agents.feature_planning_state import (
    FeaturePlanningState,
)


def _prepare_feature_request(
    state: FeaturePlanningState,
) -> FeaturePlanningState:
    """
    Validate and normalize the feature request.
    """

    feature_request = str(
        state.get(
            "feature_request",
            "",
        )
    ).strip()

    if not feature_request:
        raise ValueError(
            "Feature request cannot be empty."
        )

    return {
        **state,
        "feature_request": feature_request,
    }


def _load_repository_root(
    state: FeaturePlanningState,
    db: Session,
) -> FeaturePlanningState:
    """
    Load the local repository path from the Repository database record.
    """

    repository_id = state.get(
        "repository_id"
    )

    if not repository_id:
        raise ValueError(
            "Repository ID is required for feature planning."
        )

    repository = (
        db.query(Repository)
        .filter(
            Repository.id == repository_id
        )
        .first()
    )

    if repository is None:
        raise ValueError(
            f"Repository '{repository_id}' was not found."
        )

    return {
        **state,
        "repository_root": repository.local_path,
    }


def _build_search_queries(
    state: FeaturePlanningState,
) -> FeaturePlanningState:
    """
    Build repository search queries directly from the feature request.
    """

    feature_request = state.get(
        "feature_request",
        "",
    )

    queries_result = build_feature_search_queries(
        {
            "feature_request": feature_request,
        }
    )

    queries = queries_result.get(
        "search_queries",
        [],
    )

    cleaned_queries: list[str] = []

    seen: set[str] = set()

    for query in queries:

        if not isinstance(query, str):
            continue

        query = query.strip()

        if not query:
            continue

        key = query.lower()

        if key in seen:
            continue

        seen.add(key)

        cleaned_queries.append(
            query
        )

    return {
        **state,
        "search_queries": cleaned_queries[:3],
    }


def _search_repository(
    state: FeaturePlanningState,
    db: Session,
    embedding_provider,
) -> FeaturePlanningState:
    """
    Search the repository using the generated feature queries.

    This wrapper explicitly merges the search results into the graph
    state so they remain available to the planning node.
    """

    search_result = search_repository_for_feature(
        state,
        db=db,
        embedding_provider=embedding_provider,
    )

    return {
        **state,
        **search_result,
    }


def build_feature_planning_graph(
    db: Session,
    embedding_provider,
    llm_provider,
):
    """
    Build the Feature Planning LangGraph workflow.

    Flow:

        START
          ↓
        prepare_request
          ↓
        load_repository
          ↓
        build_queries
          ↓
        search_repository
          ↓
        plan_feature
          ↓
        END
    """

    graph = StateGraph(
        FeaturePlanningState
    )

    graph.add_node(
        "prepare_request",
        _prepare_feature_request,
    )

    graph.add_node(
        "load_repository",
        lambda state: _load_repository_root(
            state,
            db,
        ),
    )

    graph.add_node(
        "build_queries",
        _build_search_queries,
    )

    graph.add_node(
        "search_repository",
        lambda state: _search_repository(
            state,
            db=db,
            embedding_provider=embedding_provider,
        ),
    )

    graph.add_node(
        "plan_feature",
        lambda state: plan_feature(
            state,
            llm_provider=llm_provider,
        ),
    )

    graph.add_edge(
        START,
        "prepare_request",
    )

    graph.add_edge(
        "prepare_request",
        "load_repository",
    )

    graph.add_edge(
        "load_repository",
        "build_queries",
    )

    graph.add_edge(
        "build_queries",
        "search_repository",
    )

    graph.add_edge(
        "search_repository",
        "plan_feature",
    )

    graph.add_edge(
        "plan_feature",
        END,
    )

    return graph.compile()