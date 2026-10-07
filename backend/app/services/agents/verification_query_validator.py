from __future__ import annotations

import re


FORBIDDEN_PATTERNS = [
    r"\bruntime\b",
    r"\bruntime value\b",
    r"\bruntime values\b",
    r"\blogs?\b",
    r"\blogging\b",
    r"\bdatabase state\b",
    r"\bdatabase value\b",
    r"\bproduction\b",
    r"\bbreakpoint\b",
    r"\bactual value\b",
    r"\bcurrent value\b",
    r"\bnetwork response\b",
    r"\bserver logs?\b",
    r"\bconsole output\b",
    r"\bquery the database\b",
    r"\bcheck the database\b",
    r"\bexecute sql\b",
    r"\brun sql\b",
    r"\bsql query\b",
    r"\bselect\b.*\bfrom\b.*\bwhere\b",
]


def is_source_code_query(query: str) -> bool:
    """
    Return True when the query is suitable for
    repository/source-code verification.

    The validator blocks requests for runtime,
    production, database-state, or external-system
    information while allowing source-code concepts
    such as update, delete, Prisma, and transactions.
    """

    if not query or not query.strip():
        return False

    normalized_query = re.sub(
        r"\s+",
        " ",
        query.strip().lower(),
    )

    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, normalized_query):
            return False

    return True


def validate_verification_queries(
    queries: list[str],
) -> list[str]:
    """
    Keep only unique, non-empty source-code
    verification queries.
    """

    valid_queries: list[str] = []

    for query in queries:
        if not isinstance(query, str):
            continue

        cleaned_query = re.sub(
            r"\s+",
            " ",
            query.strip(),
        )

        if not cleaned_query:
            continue

        if not is_source_code_query(cleaned_query):
            continue

        if cleaned_query not in valid_queries:
            valid_queries.append(cleaned_query)

    return valid_queries