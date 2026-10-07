from __future__ import annotations

import json
import re
from typing import Any


HYPOTHESIS_VERIFICATION_PROMPT = """
You are a repository-aware debugging reasoning component.

Your task is to evaluate debugging hypotheses against repository
source-code evidence.

For EACH hypothesis, classify it as exactly one of:

- CONFIRMED
  The evidence directly supports the hypothesis.

- DISPROVED
  The evidence directly contradicts the hypothesis.

- UNRESOLVED
  The evidence is insufficient to determine whether the hypothesis
  is true or false.

Rules:

1. Use ONLY the repository evidence provided.
2. Do not use runtime information.
3. Do not assume behavior that is not shown in the evidence.
4. If the evidence shows that an implementation exists, a hypothesis
   claiming that the implementation is missing is DISPROVED.
5. If the evidence shows the exact implementation described by a
   hypothesis, classify it as CONFIRMED.
6. Do not classify a hypothesis as DISPROVED merely because the
   evidence does not mention it.
7. Do not classify a hypothesis as CONFIRMED merely because some
   keywords appear in the evidence.
8. Be conservative when evidence is incomplete.

Return ONLY valid JSON:

{
  "evaluations": [
    {
      "hypothesis": "original hypothesis",
      "status": "CONFIRMED",
      "reason": "short evidence-based reason"
    }
  ]
}

The status must be exactly:
CONFIRMED, DISPROVED, or UNRESOLVED.
"""


def _extract_json_object(
    raw_response: str,
) -> dict[str, Any] | None:
    """
    Extract a JSON object from the LLM response.
    """
    text = raw_response.strip()

    if not text:
        return None

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    ).strip()

    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    first_brace = text.find("{")

    if first_brace == -1:
        return None

    try:
        parsed, _ = json.JSONDecoder().raw_decode(
            text[first_brace:]
        )

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    return None


def _format_hypotheses(
    hypotheses: list[str],
) -> str:
    """
    Format hypotheses for the LLM.
    """
    if not hypotheses:
        return "No hypotheses were provided."

    lines = []

    for index, hypothesis in enumerate(
        hypotheses,
        start=1,
    ):
        lines.append(
            f"{index}. {hypothesis}"
        )

    return "\n".join(lines)


def verify_hypotheses(
    hypotheses: list[str],
    evidence: str,
    llm_provider,
) -> dict[str, Any]:
    """
    Ask the LLM to classify debugging hypotheses against
    repository evidence.
    """
    if not hypotheses:
        return {
            "evaluations": [],
        }

    if not evidence or not evidence.strip():
        return {
            "evaluations": [
                {
                    "hypothesis": hypothesis,
                    "status": "UNRESOLVED",
                    "reason": (
                        "No repository evidence was provided."
                    ),
                }
                for hypothesis in hypotheses
            ],
        }

    prompt = (
        HYPOTHESIS_VERIFICATION_PROMPT.strip()
        + "\n\nHYPOTHESES:\n"
        + _format_hypotheses(hypotheses)
        + "\n\nREPOSITORY EVIDENCE:\n"
        + evidence
        + "\n\nReturn JSON only."
    )

    try:
        raw_response = (
            llm_provider
            .generate(prompt)
            .strip()
        )

    except Exception as exc:
        return {
            "evaluations": [
                {
                    "hypothesis": hypothesis,
                    "status": "UNRESOLVED",
                    "reason": (
                        f"Verification failed: {exc}"
                    ),
                }
                for hypothesis in hypotheses
            ],
        }

    parsed = _extract_json_object(
        raw_response
    )

    if parsed is None:
        return {
            "evaluations": [
                {
                    "hypothesis": hypothesis,
                    "status": "UNRESOLVED",
                    "reason": (
                        "The verifier returned invalid JSON."
                    ),
                }
                for hypothesis in hypotheses
            ],
        }

    evaluations = parsed.get(
        "evaluations",
        [],
    )

    if not isinstance(
        evaluations,
        list,
    ):
        evaluations = []

    validated_evaluations = []

    for evaluation in evaluations:
        if not isinstance(
            evaluation,
            dict,
        ):
            continue

        hypothesis = evaluation.get(
            "hypothesis",
            "",
        )

        status = evaluation.get(
            "status",
            "UNRESOLVED",
        )

        reason = evaluation.get(
            "reason",
            "",
        )

        if not isinstance(
            hypothesis,
            str,
        ):
            continue

        if status not in {
            "CONFIRMED",
            "DISPROVED",
            "UNRESOLVED",
        }:
            status = "UNRESOLVED"

        validated_evaluations.append(
            {
                "hypothesis": hypothesis,
                "status": status,
                "reason": str(reason),
            }
        )

    return {
        "evaluations": validated_evaluations,
    }