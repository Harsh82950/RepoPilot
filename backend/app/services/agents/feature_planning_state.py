from typing import Any, TypedDict


class FeaturePlanningState(TypedDict, total=False):
    repository_id: str

    feature_request: str

    search_queries: list[str]

    retrieval_results: list[dict[str, Any]]

    tool_calls: list[dict[str, Any]]

    tool_messages: list[dict[str, Any]]

    tool_call_count: int

    affected_files: list[dict[str, Any]]

    affected_modules: list[str]

    implementation_overview: str

    implementation_steps: list[str]

    data_flow: list[str]

    new_files: list[dict[str, Any]]

    risks: list[str]

    tests: list[str]

    assumptions: list[str]

    confidence: str

    plan: str