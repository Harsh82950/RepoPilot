
import re

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.repository_chunk import RepositoryChunk
from app.models.repository_file import RepositoryFile
from app.services.embeddings.embedding_provider import EmbeddingProvider


DEFAULT_TOP_K = 5
DEFAULT_CANDIDATE_K = 20

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "the",
    "to", "was", "were", "where", "which", "with",
}

ACTION_WORDS = {
    "update",
    "updated",
    "updating",
    "change",
    "changed",
    "modify",
    "modified",
    "create",
    "created",
    "insert",
    "delete",
    "deleted",
    "remove",
    "read",
    "fetch",
    "get",
    "find",
    "reserve",
    "reserved",
    "release",
    "released",
    "debit",
    "debited",
    "credit",
    "credited",
    "increment",
    "decrement",
}


def extract_keywords(query: str) -> list[str]:
    tokens = re.findall(
        r"[A-Za-z_][A-Za-z0-9_.-]*",
        query.lower(),
    )

    keywords = []

    for token in tokens:
        if token in STOP_WORDS:
            continue

        if len(token) < 2:
            continue

        if token not in keywords:
            keywords.append(token)

    return keywords


def extract_actions(query: str) -> list[str]:
    """
    Extract action words from the natural-language query.
    """

    keywords = extract_keywords(query)

    return [
        keyword
        for keyword in keywords
        if keyword in ACTION_WORDS
    ]


def calculate_keyword_score(
    content: str,
    file_path: str,
    keywords: list[str],
) -> float:
    """
    Calculate a code-aware keyword score.
    """

    if not keywords:
        return 0.0

    content_lower = content.lower()
    file_path_lower = file_path.lower()

    score = 0.0
    maximum_score = 0.0

    for keyword in keywords:

        if keyword in ACTION_WORDS:
            weight = 1.0
        else:
            weight = 1.5

        maximum_score += weight

        exact_pattern = (
            rf"(?<![a-zA-Z0-9_])"
            rf"{re.escape(keyword)}"
            rf"(?![a-zA-Z0-9_])"
        )

        if re.search(exact_pattern, content_lower):
            score += weight
            continue

        if keyword in file_path_lower:
            score += weight * 0.8
            continue

        if keyword in content_lower:
            score += weight * 0.4

    return min(score / maximum_score, 1.0)


def calculate_action_score(
    content: str,
    actions: list[str],
) -> float:
    """
    Estimate whether a code chunk actually performs
    the action requested by the user.
    """

    if not actions:
        return 0.0

    content_lower = content.lower()

    score = 0.0
    maximum_score = float(len(actions))

    for action in actions:

        # Direct database mutation patterns.
        if action in {"update", "updated", "updating", "change", "changed", "modify", "modified"}:
            mutation_patterns = [
                r"\.update\s*\(",
                r"\.updateMany\s*\(",
                r"\.upsert\s*\(",
                r"\bset\s*:",
                r"\bincrement\s*:",
                r"\bdecrement\s*:",
            ]

            if any(
                re.search(pattern, content_lower)
                for pattern in mutation_patterns
            ):
                score += 1.0
                continue

        # Creation patterns.
        if action in {"create", "created", "insert"}:
            creation_patterns = [
                r"\.create\s*\(",
                r"\.createMany\s*\(",
                r"\binsert\s*\(",
            ]

            if any(
                re.search(pattern, content_lower)
                for pattern in creation_patterns
            ):
                score += 1.0
                continue

        # Deletion patterns.
        if action in {"delete", "deleted", "remove"}:
            deletion_patterns = [
                r"\.delete\s*\(",
                r"\.deleteMany\s*\(",
                r"\bremove\s*\(",
            ]

            if any(
                re.search(pattern, content_lower)
                for pattern in deletion_patterns
            ):
                score += 1.0
                continue

        # Wallet/accounting-specific actions.
        if action in {
            "debit",
            "debited",
            "credit",
            "credited",
            "reserve",
            "reserved",
            "release",
            "released",
        }:
            if re.search(
                rf"\b{re.escape(action.rstrip('ed'))}",
                content_lower,
            ):
                score += 1.0
                continue

        # Generic exact action match.
        exact_pattern = (
            rf"(?<![a-zA-Z0-9_])"
            rf"{re.escape(action)}"
            rf"(?![a-zA-Z0-9_])"
        )

        if re.search(exact_pattern, content_lower):
            score += 0.5

    return min(score / maximum_score, 1.0)


def semantic_search(
    db: Session,
    repository_id,
    query_embedding: list[float],
    candidate_k: int = DEFAULT_CANDIDATE_K,
):
    distance = RepositoryChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    results = (
        db.query(
            RepositoryChunk,
            RepositoryFile,
            distance,
        )
        .join(
            RepositoryFile,
            RepositoryChunk.repository_file_id == RepositoryFile.id,
        )
        .filter(
            RepositoryChunk.repository_id == repository_id,
            RepositoryChunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(candidate_k)
        .all()
    )

    return [
        {
            "chunk": chunk,
            "repository_file": repository_file,
            "semantic_distance": float(distance_value),
        }
        for chunk, repository_file, distance_value in results
    ]


def keyword_search(
    db: Session,
    repository_id,
    keywords: list[str],
    candidate_k: int = DEFAULT_CANDIDATE_K,
):
    if not keywords:
        return []

    conditions = []

    for keyword in keywords:
        pattern = f"%{keyword}%"

        conditions.append(
            RepositoryChunk.content.ilike(pattern)
        )

        conditions.append(
            RepositoryFile.file_path.ilike(pattern)
        )

    results = (
        db.query(
            RepositoryChunk,
            RepositoryFile,
        )
        .join(
            RepositoryFile,
            RepositoryChunk.repository_file_id == RepositoryFile.id,
        )
        .filter(
            RepositoryChunk.repository_id == repository_id,
            RepositoryChunk.embedding.isnot(None),
            or_(*conditions),
        )
        .limit(candidate_k)
        .all()
    )

    return [
        {
            "chunk": chunk,
            "repository_file": repository_file,
        }
        for chunk, repository_file in results
    ]


def retrieve_hybrid_chunks(
    db: Session,
    repository_id,
    query: str,
    embedding_provider: EmbeddingProvider,
    top_k: int = DEFAULT_TOP_K,
    candidate_k: int = DEFAULT_CANDIDATE_K,
):
    """
    Retrieve chunks using:

    1. Semantic similarity
    2. Keyword matching
    3. Code/action-aware matching
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    if candidate_k < top_k:
        raise ValueError("candidate_k must be >= top_k.")

    # ---------------------------------------------------------
    # 1. Query embedding
    # ---------------------------------------------------------

    query_embedding = embedding_provider.embed_text(query)

    if len(query_embedding) != embedding_provider.dimension:
        raise RuntimeError(
            f"Unexpected query embedding dimension: "
            f"{len(query_embedding)}. "
            f"Expected: {embedding_provider.dimension}."
        )

    # ---------------------------------------------------------
    # 2. Extract keywords and actions
    # ---------------------------------------------------------

    keywords = extract_keywords(query)
    actions = extract_actions(query)

    # ---------------------------------------------------------
    # 3. Semantic search
    # ---------------------------------------------------------

    semantic_results = semantic_search(
        db=db,
        repository_id=repository_id,
        query_embedding=query_embedding,
        candidate_k=candidate_k,
    )

    # ---------------------------------------------------------
    # 4. Keyword search
    # ---------------------------------------------------------

    keyword_results = keyword_search(
        db=db,
        repository_id=repository_id,
        keywords=keywords,
        candidate_k=candidate_k,
    )

    # ---------------------------------------------------------
    # 5. Merge candidates
    # ---------------------------------------------------------

    candidates = {}

    for result in semantic_results:
        chunk = result["chunk"]

        candidates[str(chunk.id)] = {
            "chunk": chunk,
            "repository_file": result["repository_file"],
            "semantic_distance": result["semantic_distance"],
        }

    for result in keyword_results:
        chunk = result["chunk"]

        if str(chunk.id) not in candidates:
            candidates[str(chunk.id)] = {
                "chunk": chunk,
                "repository_file": result["repository_file"],
                "semantic_distance": 1.0,
            }

    # ---------------------------------------------------------
    # 6. Score
    # ---------------------------------------------------------

    results = []

    for candidate in candidates.values():

        chunk = candidate["chunk"]
        repository_file = candidate["repository_file"]

        semantic_similarity = max(
            0.0,
            1.0 - candidate["semantic_distance"],
        )

        keyword_score = calculate_keyword_score(
            content=chunk.content,
            file_path=repository_file.file_path,
            keywords=keywords,
        )

        action_score = calculate_action_score(
            content=chunk.content,
            actions=actions,
        )

        # Initial weights:
        #
        # 60% semantic
        # 20% keyword
        # 20% action/mutation
        #
        # These are heuristics for the initial system.
        hybrid_score = (
            0.60 * semantic_similarity
            + 0.20 * keyword_score
            + 0.20 * action_score
        )

        results.append(
            {
                "chunk": chunk,
                "repository_file": repository_file,
                "semantic_similarity": semantic_similarity,
                "keyword_score": keyword_score,
                "action_score": action_score,
                "hybrid_score": hybrid_score,
            }
        )

    # ---------------------------------------------------------
    # 7. Rank
    # ---------------------------------------------------------

    results.sort(
        key=lambda result: result["hybrid_score"],
        reverse=True,
    )

    # ---------------------------------------------------------
    # 8. Format output
    # ---------------------------------------------------------

    formatted_results = []

    for result in results[:top_k]:

        chunk = result["chunk"]
        repository_file = result["repository_file"]

        formatted_results.append(
            {
                "chunk_id": str(chunk.id),
                "file_id": str(repository_file.id),
                "file_path": repository_file.file_path,
                "chunk_index": chunk.chunk_index,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "semantic_similarity": result["semantic_similarity"],
                "keyword_score": result["keyword_score"],
                "action_score": result["action_score"],
                "hybrid_score": result["hybrid_score"],
                "content": chunk.content,
            }
        )

    return {
        "query": query,
        "keywords": keywords,
        "actions": actions,
        "results": formatted_results,
    }


def retrieve_similar_chunks(
    db: Session,
    repository_id,
    query: str,
    embedding_provider: EmbeddingProvider,
    top_k: int = DEFAULT_TOP_K,
):
    """
    Backward-compatible semantic-only retrieval.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    query_embedding = embedding_provider.embed_text(query)

    distance = RepositoryChunk.embedding.cosine_distance(
        query_embedding
    ).label("distance")

    results = (
        db.query(
            RepositoryChunk,
            RepositoryFile,
            distance,
        )
        .join(
            RepositoryFile,
            RepositoryChunk.repository_file_id == RepositoryFile.id,
        )
        .filter(
            RepositoryChunk.repository_id == repository_id,
            RepositoryChunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(top_k)
        .all()
    )

    return [
        {
            "chunk_id": str(chunk.id),
            "file_id": str(repository_file.id),
            "file_path": repository_file.file_path,
            "chunk_index": chunk.chunk_index,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "similarity": 1.0 - float(distance_value),
            "content": chunk.content,
        }
        for chunk, repository_file, distance_value in results
    ]