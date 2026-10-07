from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.services.embeddings.embedding_provider import EmbeddingProvider
from app.services.retrieval.semantic_retriever import retrieve_hybrid_chunks


def _search_repository(
    db: Session,
    embedding_provider: EmbeddingProvider,
    repository_id: str,
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
) -> list[dict[str, Any]]:
    """
    Internal repository search implementation.

    Uses the existing hybrid semantic + keyword retrieval pipeline.
    """

    if not repository_id or not repository_id.strip():
        raise ValueError("Repository ID cannot be empty.")

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    result = retrieve_hybrid_chunks(
        db=db,
        repository_id=repository_id,
        query=query,
        embedding_provider=embedding_provider,
        top_k=top_k,
        candidate_k=candidate_k,
    )

    return result["results"]


def create_search_repository_tool(
    db: Session,
    embedding_provider: EmbeddingProvider,
    repository_id: str,
):
    """
    Create a LangChain/LangGraph-compatible repository search tool.

    The database, embedding provider, and repository ID are injected
    when the tool is created. The agent only needs to provide a query.
    """

    @tool
    def search_repository(query: str) -> str:
        """
        Search the repository for relevant code.

        Use this tool when you need to find files, functions,
        implementations, or code related to the user's question.
        """

        results = _search_repository(
            db=db,
            embedding_provider=embedding_provider,
            repository_id=repository_id,
            query=query,
            top_k=3,
            candidate_k=20,
        )

        if not results:
            return "No relevant repository evidence was found."

        formatted_results = []

        for index, result in enumerate(results, start=1):
            formatted_results.append(
                f"[Result {index}]\n"
                f"File: {result.get('file_path', 'Unknown')}\n"
                f"Lines: "
                f"{result.get('start_line', '?')}-"
                f"{result.get('end_line', '?')}\n"
                f"Content:\n"
                f"{result.get('content', '').strip()}"
            )

        return "\n\n" + ("\n" + "=" * 80 + "\n").join(
            formatted_results
        )

    return search_repository