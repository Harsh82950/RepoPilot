from sqlalchemy.orm import Session

from app.services.agents.repository_qa_state import RepositoryQAState
from app.services.embeddings.embedding_provider import EmbeddingProvider
from app.services.llm.llm_provider import LLMProvider
from app.services.rag.context_builder import build_rag_context
from app.services.rag.rag_prompt import build_rag_prompt
from app.services.retrieval.semantic_retriever import (
    extract_keywords,
    retrieve_hybrid_chunks,
)


def retrieve_repository_context(
    state: RepositoryQAState,
    db: Session,
    embedding_provider: EmbeddingProvider,
) -> RepositoryQAState:
    """
    Retrieve repository evidence for the user's question.

    This node reuses RepoPilot's existing hybrid retrieval system.
    """

    question = state.get("question", "").strip()
    repository_id = state.get("repository_id", "").strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if not repository_id:
        raise ValueError("Repository ID cannot be empty.")

    retrieval_attempts = state.get("retrieval_attempts", 0) + 1

    retrieval_result = retrieve_hybrid_chunks(
        db=db,
        repository_id=repository_id,
        query=question,
        embedding_provider=embedding_provider,
        top_k=3,
        candidate_k=20,
    )

    return {
        **state,
        "retrieval_results": retrieval_result["results"],
        "keywords": retrieval_result["keywords"],
        "actions": retrieval_result["actions"],
        "retrieval_attempts": retrieval_attempts,
    }


def build_repository_context(
    state: RepositoryQAState,
) -> RepositoryQAState:
    """
    Build an LLM-ready context from retrieved repository evidence.
    """

    results = state.get("retrieval_results", [])

    context = build_rag_context(results)

    return {
        **state,
        "context": context,
    }


def generate_repository_answer(
    state: RepositoryQAState,
    llm_provider: LLMProvider,
) -> RepositoryQAState:
    """
    Generate a repository-grounded answer using the configured LLM.
    """

    question = state.get("question", "").strip()
    context = state.get("context", "").strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if not context:
        raise ValueError("Repository context cannot be empty.")

    prompt = build_rag_prompt(
        question=question,
        context=context,
    )

    answer = llm_provider.generate(prompt)

    return {
        **state,
        "prompt": prompt,
        "answer": answer,
    }


def evaluate_repository_context(
    state: RepositoryQAState,
) -> RepositoryQAState:
    """
    Evaluate whether the retrieved repository context is relevant
    enough to answer the user's question.

    This evaluator is deterministic and intentionally lightweight.
    """

    question = state.get("question", "").strip()
    results = state.get("retrieval_results", [])
    context = state.get("context", "").strip()

    if not question or not results or not context:
        return {
            **state,
            "context_sufficient": False,
        }

    question_keywords = extract_keywords(question)

    if not question_keywords:
        return {
            **state,
            "context_sufficient": bool(results),
        }

    combined_evidence = " ".join(
        result.get("content", "")
        for result in results
    ).lower()

    matched_keywords = [
        keyword
        for keyword in question_keywords
        if keyword in combined_evidence
    ]

    coverage = len(matched_keywords) / len(question_keywords)

    context_sufficient = coverage >= 0.30

    return {
        **state,
        "context_sufficient": context_sufficient,
    }