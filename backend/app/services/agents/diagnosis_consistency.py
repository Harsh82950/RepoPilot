from __future__ import annotations

import re
from pathlib import PurePosixPath


FORBIDDEN_RUNTIME_PATTERNS = [
    r"\bruntime\b",
    r"\blogs?\b",
    r"\bdatabase state\b",
    r"\bbreakpoint\b",
    r"\bproduction\b",
    r"\bactual value\b",
    r"\bcurrent value\b",
    r"\bobserve\b.*\bvalue\b",
]


def _normalize_path(path: str) -> str:
    """
    Normalize a repository-relative path.
    """
    path = path.strip().replace("\\", "/")

    while path.startswith("./"):
        path = path[2:]

    return str(
        PurePosixPath(path)
    )


def _path_matches_evidence(
    path: str,
    evidence: str,
) -> bool:
    """
    Check whether a proposed file path appears in
    repository evidence.
    """
    normalized_path = _normalize_path(path)

    if not normalized_path:
        return False

    normalized_evidence = evidence.replace(
        "\\",
        "/",
    )

    return normalized_path in normalized_evidence


def _is_source_only_step(
    step: str,
) -> bool:
    """
    Reject debugging steps that require runtime or
    external-system information.
    """
    normalized_step = re.sub(
        r"\s+",
        " ",
        step.strip().lower(),
    )

    if not normalized_step:
        return False

    for pattern in FORBIDDEN_RUNTIME_PATTERNS:
        if re.search(
            pattern,
            normalized_step,
        ):
            return False

    return True


def validate_likely_locations(
    likely_locations,
    evidence: str,
):
    """
    Keep only likely locations whose file paths are
    supported by repository evidence.
    """
    if not isinstance(
        likely_locations,
        list,
    ):
        return []

    validated = []

    for location in likely_locations:
        if not isinstance(
            location,
            dict,
        ):
            continue

        file_path = location.get(
            "file",
            "",
        )

        if not isinstance(
            file_path,
            str,
        ):
            continue

        file_path = _normalize_path(
            file_path
        )

        if not file_path:
            continue

        if not _path_matches_evidence(
            file_path,
            evidence,
        ):
            continue

        validated.append(
            {
                "file": file_path,
                "function": str(
                    location.get(
                        "function",
                        "",
                    )
                ).strip(),
                "reason": str(
                    location.get(
                        "reason",
                        "",
                    )
                ).strip(),
            }
        )

    return validated


def validate_debugging_steps(
    debugging_steps,
):
    """
    Keep only debugging steps that can be performed
    using source-code investigation.
    """
    if not isinstance(
        debugging_steps,
        list,
    ):
        return []

    validated = []

    for step in debugging_steps:
        if not isinstance(
            step,
            str,
        ):
            continue

        step = re.sub(
            r"\s+",
            " ",
            step.strip(),
        )

        if not step:
            continue

        if not _is_source_only_step(
            step
        ):
            continue

        if step not in validated:
            validated.append(step)

    return validated


def validate_root_cause(
    root_cause: str,
    confirmed_hypotheses,
):
    """
    A root cause is allowed only when there is at least
    one confirmed hypothesis.
    """
    if not isinstance(
        root_cause,
        str,
    ):
        return ""

    root_cause = root_cause.strip()

    if not root_cause:
        return ""

    if not confirmed_hypotheses:
        return ""

    return root_cause


def validate_diagnosis_output(
    diagnosis_data,
    evidence: str,
):
    """
    Apply final consistency checks to an LLM diagnosis.
    """
    if not isinstance(
        diagnosis_data,
        dict,
    ):
        return {
            "likely_locations": [],
            "root_cause": "",
            "debugging_steps": [],
        }

    confirmed_hypotheses = diagnosis_data.get(
        "confirmed_hypotheses",
        [],
    )

    if not isinstance(
        confirmed_hypotheses,
        list,
    ):
        confirmed_hypotheses = []

    confirmed_hypotheses = [
        item.strip()
        for item in confirmed_hypotheses
        if isinstance(
            item,
            str,
        )
        and item.strip()
    ]

    likely_locations = validate_likely_locations(
        likely_locations=diagnosis_data.get(
            "likely_locations",
            [],
        ),
        evidence=evidence,
    )

    debugging_steps = validate_debugging_steps(
        debugging_steps=diagnosis_data.get(
            "debugging_steps",
            [],
        )
    )

    root_cause = validate_root_cause(
        root_cause=diagnosis_data.get(
            "root_cause",
            "",
        ),
        confirmed_hypotheses=confirmed_hypotheses,
    )

    return {
        "likely_locations": likely_locations,
        "root_cause": root_cause,
        "debugging_steps": debugging_steps,
    }