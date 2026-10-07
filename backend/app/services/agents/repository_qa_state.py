from typing import Any, TypedDict


class RepositoryQAState(TypedDict, total=False):
    repository_id: str
    question: str

    retrieval_results: list[dict[str, Any]]

    context: str
    prompt: str
    answer: str

    keywords: list[str]
    actions: list[str]

    retrieval_attempts: int
    context_sufficient: bool

    tool_calls: list[dict[str, Any]]
    tool_messages: list[dict[str, Any]]

    # Complete conversation history sent to the LLM.
    messages: list[dict[str, Any]]

    tool_call_count: int