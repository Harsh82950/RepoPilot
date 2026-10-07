from typing import Any, TypedDict


class BugInvestigationState(TypedDict, total=False):
    repository_id: str

    # Bug input
    bug_report: str
    error_message: str
    error_type: str
    stack_trace: str

    # Extracted signals
    extracted_symbols: list[str]
    extracted_files: list[str]
    extracted_functions: list[str]

    # Initial repository investigation
    search_queries: list[str]
    retrieval_results: list[dict[str, Any]]

    tool_calls: list[dict[str, Any]]
    tool_messages: list[dict[str, Any]]
    tool_call_count: int

    # Candidate diagnosis
    likely_locations: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]

    # Verification investigation
    verification_queries: list[str]
    verification_results: list[dict[str, Any]]

    verification_tool_calls: list[dict[str, Any]]
    verification_tool_messages: list[dict[str, Any]]
    verification_tool_count: int

    verification_attempts: int

    # Exact file inspection
    file_inspection_calls: list[dict[str, Any]]
    file_inspection_results: list[dict[str, Any]]
    file_inspection_count: int

    # Final diagnosis
    diagnosis: str
    root_cause: str
    debugging_steps: list[str]
    confidence: str

    # Agent messages
    messages: list[dict[str, Any]]