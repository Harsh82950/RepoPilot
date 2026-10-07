from __future__ import annotations

import re
from typing import Any


def _normalize_text(text: str) -> str:
    """
    Normalize text for simple evidence matching.
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _hypothesis_keywords(hypothesis: str) -> list[str]:
    """
    Extract useful technical terms from a hypothesis.
    """
    normalized = _normalize_text(hypothesis)

    words = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_.-]*",
        normalized,
    )

    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "may",
        "might",
        "could",
        "possibly",
        "likely",
        "due",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "that",
        "this",
        "be",
        "being",
        "from",
        "with",
        "when",
        "where",
        "if",
        "not",
    }

    keywords = []

    for word in words:
        if word in stop_words:
            continue

        if len(word) < 3:
            continue

        if word not in keywords:
            keywords.append(word)

    return keywords


def _evidence_contains_any(
    evidence_text: str,
    keywords: list[str],
) -> bool:
    """
    Check whether repository evidence contains
    at least one important technical term.
    """
    normalized_evidence = _normalize_text(
        evidence_text
    )

    for keyword in keywords:
        if keyword in normalized_evidence:
            return True

    return False


def classify_hypothesis(
    hypothesis: str,
    evidence: str,
) -> str:
    """
    Classify a hypothesis using repository evidence.

    Returns:
        confirmed
        disproved
        unresolved

    This is intentionally conservative.
    It should not claim that a hypothesis is disproved
    merely because one keyword is missing.
    """
    if not hypothesis or not hypothesis.strip():
        return "unresolved"

    if not evidence or not evidence.strip():
        return "unresolved"

    keywords = _hypothesis_keywords(
        hypothesis
    )

    if not keywords:
        return "unresolved"

    normalized_hypothesis = _normalize_text(
        hypothesis
    )

    normalized_evidence = _normalize_text(
        evidence
    )

    # Explicit contradiction patterns.
    contradiction_patterns = [
        r"\bdoes not\b",
        r"\bdoesn't\b",
        r"\bdo not\b",
        r"\bnot present\b",
        r"\bmissing\b",
        r"\bnever\b",
        r"\bwithout\b",
        r"\bno\b",
    ]

    has_contradiction = any(
        re.search(
            pattern,
            normalized_evidence,
        )
        for pattern in contradiction_patterns
    )

    if has_contradiction:
        return "disproved"

    # If the evidence directly contains the hypothesis
    # terms, treat it as supported but still conservative.
    if _evidence_contains_any(
        normalized_evidence,
        keywords,
    ):
        return "confirmed"

    return "unresolved"


def validate_hypotheses(
    hypotheses: list[str],
    evidence: str,
) -> dict[str, Any]:
    """
    Classify all hypotheses against repository evidence.

    Returns a structured result containing:
    - confirmed
    - disproved
    - unresolved
    """
    confirmed = []
    disproved = []
    unresolved = []

    for hypothesis in hypotheses:
        if not isinstance(hypothesis, str):
            continue

        hypothesis = hypothesis.strip()

        if not hypothesis:
            continue

        status = classify_hypothesis(
            hypothesis=hypothesis,
            evidence=evidence,
        )

        if status == "confirmed":
            confirmed.append(hypothesis)

        elif status == "disproved":
            disproved.append(hypothesis)

        else:
            unresolved.append(hypothesis)

    return {
        "confirmed": confirmed,
        "disproved": disproved,
        "unresolved": unresolved,
    }