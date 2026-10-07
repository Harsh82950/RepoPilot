from __future__ import annotations

import json
import re
from typing import Any

from app.services.agents.bug_investigation_state import (
    BugInvestigationState,
)
from app.services.agents.diagnosis_consistency import (
    validate_diagnosis_output,
)
from app.services.agents.evidence_compression import (
    build_compressed_evidence,
    build_final_diagnosis_evidence,
)
from app.services.agents.verification_query_validator import (
    validate_verification_queries,
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Keep the amount of repository evidence sent to the diagnosis model
# deliberately small. Retrieval may collect many chunks, but the diagnosis
# model does not need the complete retrieval history.
MAX_DIAGNOSIS_EVIDENCE_CHARS = 5000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_list(value: Any) -> list[str]:
    """
    Normalize a model-generated list into a clean list of strings.
    """

    if not isinstance(value, list):
        return []

    normalized: list[str] = []

    for item in value:
        if not isinstance(item, str):
            continue

        item = item.strip()

        if item and item not in normalized:
            normalized.append(item)

    return normalized


def _extract_json_object(text: str) -> dict[str, Any]:
    """
    Extract a JSON object from the model response.

    The model is instructed to return JSON only, but this also handles
    accidental markdown/text surrounding the JSON object.
    """

    if not text:
        return {}

    text = text.strip()

    # First try the complete response directly.
    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # Fallback: find the first JSON object in the response.
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        return {}

    try:
        parsed = json.loads(match.group(0))

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        return {}

    return {}


# ---------------------------------------------------------------------------
# Initial diagnosis prompt
# ---------------------------------------------------------------------------

def _build_initial_prompt(
    state: BugInvestigationState,
) -> str:

    bug_report = state.get(
        "bug_report",
        "",
    )

    evidence = _build_evidence(state)

    return f"""
You are an expert software debugging assistant.

You are investigating a bug using ONLY repository source-code evidence.

BUG REPORT:

{bug_report}

REPOSITORY EVIDENCE:

{evidence}

Your job is to identify:

1. What the repository code proves.
2. What explanations are plausible but unproven.
3. Which files/functions are relevant.
4. What source-code evidence should be checked next.
5. Whether a root cause can actually be established.

IMPORTANT RULES:

1. Do NOT infer runtime values from source code.

2. Do NOT assume that a variable has a particular runtime
   value unless the repository evidence directly establishes it.

3. Do NOT invent files, functions, classes, modules, or paths.

4. Every likely location must come directly from repository evidence.

5. A plausible explanation is NOT automatically a root cause.

6. Only put an explanation into confirmed_hypotheses when
   the repository evidence directly supports it.

7. Put plausible but unproven explanations into
   unresolved_hypotheses.

8. If no hypothesis is directly proven, root_cause MUST
   be an empty string.

9. Do not claim that a file is missing functionality when
   the evidence shows that the functionality exists.

10. Do not claim that something is the "only" occurrence
    unless the evidence establishes exhaustiveness.

11. Debugging steps must focus on source-code investigation.
    Do not require runtime logs, production access,
    breakpoints, database inspection, or observing live values.

12. Verification queries must be queries about repository
    source code only.

13. If the root cause is not established, verification_queries
    MUST contain at least one useful source-code query targeting
    a relevant file or function whenever a relevant location
    has been identified.

14. Verification queries must help inspect or understand the
    repository implementation. Do not ask for runtime values,
    database state, logs, production behavior, or external state.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "proven_facts": [],
  "confirmed_hypotheses": [],
  "unresolved_hypotheses": [],
  "likely_locations": [
    {{
      "file": "",
      "function": "",
      "reason": ""
    }}
  ],
  "root_cause": "",
  "debugging_steps": [],
  "verification_queries": [],
  "confidence": "Low"
}}

Confidence rules:

High:
The repository directly establishes the root cause.

Medium:
Evidence strongly supports a hypothesis but does not
completely establish the root cause.

Low:
The repository evidence is insufficient to establish
the root cause.
""".strip()


# ---------------------------------------------------------------------------
# Verification/final diagnosis prompt
# ---------------------------------------------------------------------------

def _build_verification_prompt(
    state: BugInvestigationState,
) -> str:

    bug_report = state.get(
        "bug_report",
        "",
    )

    evidence = _build_evidence(state)

    existing_hypotheses = state.get(
        "hypotheses",
        [],
    )

    return f"""
You are performing the FINAL source-code investigation
of a software bug.

You already performed an initial investigation and generated
possible hypotheses.

Now additional repository evidence has been collected.

BUG REPORT:

{bug_report}

EXISTING HYPOTHESES:

{json.dumps(existing_hypotheses, indent=2)}

ADDITIONAL REPOSITORY EVIDENCE:

{evidence}

Your task is to produce the final evidence-based diagnosis.

For EACH existing hypothesis:

- Confirm it only if the repository evidence directly supports it.
- Reject it if the repository evidence contradicts it.
- Keep it unresolved if the evidence is insufficient.

You must independently reason over the evidence rather than
assuming that the previous diagnosis was correct.

IMPORTANT RULES:

1. Repository source code is the only source of truth.

2. Do NOT infer runtime values.

3. Do NOT assume database state.

4. Do NOT assume logs, production behavior, network responses,
   or external system state.

5. A hypothesis must NOT become confirmed merely because
   it is plausible.

6. If evidence contradicts a hypothesis, do not retain it
   as confirmed.

7. If evidence is insufficient, classify the hypothesis
   as unresolved.

8. root_cause MUST be empty unless a confirmed hypothesis
   directly establishes it.

9. Do not invent repository paths.

10. Do not claim exhaustiveness unless the evidence proves it.

11. Debugging steps must remain source-code oriented.

12. Do not recommend runtime observation, production logs,
    database inspection, breakpoints, or observing live values.

13. likely_locations must contain only files/functions that
    are directly present in the provided repository evidence.

14. A source-code implementation existing in the repository
    must not be described as missing merely because the bug
    report says that behavior is failing.

15. If the repository contains the expected implementation
    but does not establish why it fails, explicitly leave
    the root cause empty.

16. verification_queries are only for source-code investigation.
    Do not request runtime values, logs, database state,
    production behavior, or external system state.

Return ONLY valid JSON.

Use exactly this structure:

{{
  "proven_facts": [],
  "confirmed_hypotheses": [],
  "unresolved_hypotheses": [],
  "likely_locations": [
    {{
      "file": "",
      "function": "",
      "reason": ""
    }}
  ],
  "root_cause": "",
  "debugging_steps": [],
  "verification_queries": [],
  "confidence": "Low"
}}

Confidence rules:

High:
The repository directly establishes the root cause.

Medium:
Evidence strongly supports a hypothesis but does not
completely establish the root cause.

Low:
The repository evidence is insufficient to establish
the root cause.
""".strip()


# ---------------------------------------------------------------------------
# Evidence builder
# ---------------------------------------------------------------------------

def _build_evidence(
    state: BugInvestigationState,
) -> str:
    """
    Build compact evidence for the diagnosis model.

    Retrieval may collect many chunks, but the diagnosis model
    does not need the entire retrieval history.

    This hard character limit reduces Groq input-token usage
    while preserving the strongest evidence generated by the
    evidence-compression layer.
    """

    verification_attempts = state.get(
        "verification_attempts",
        0,
    )

    if verification_attempts > 0:
        evidence = build_final_diagnosis_evidence(
            state=state,
        )
    else:
        evidence = build_compressed_evidence(
            state=state,
        )

    if not evidence:
        return "No repository evidence was available."

    if len(evidence) > MAX_DIAGNOSIS_EVIDENCE_CHARS:
        evidence = (
            evidence[:MAX_DIAGNOSIS_EVIDENCE_CHARS]
            + "\n\n"
            "[Evidence truncated for token efficiency.]"
        )

    return evidence


# ---------------------------------------------------------------------------
# Deterministic fallback verification queries
# ---------------------------------------------------------------------------

def _build_fallback_verification_queries(
    diagnosis_data: dict[str, Any],
) -> list[str]:
    """
    Build deterministic source-code verification queries when the
    diagnosis model does not provide usable verification queries.

    This keeps the investigation moving when the model identifies
    relevant locations but forgets to request further inspection.
    """

    queries: list[str] = []

    likely_locations = diagnosis_data.get(
        "likely_locations",
        [],
    )

    if not isinstance(likely_locations, list):
        return queries

    for location in likely_locations:

        if not isinstance(location, dict):
            continue

        file_path = str(
            location.get("file", "")
        ).strip()

        function = str(
            location.get("function", "")
        ).strip()

        reason = str(
            location.get("reason", "")
        ).strip()

        if not file_path:
            continue

        parts = [
            "Inspect",
            file_path,
        ]

        if function:
            parts.extend(
                [
                    function,
                    "implementation",
                ]
            )

        if reason:
            parts.extend(
                [
                    "and",
                    reason,
                ]
            )

        query = " ".join(parts)

        if query not in queries:
            queries.append(query)

    return queries


# ---------------------------------------------------------------------------
# Main diagnosis function
# ---------------------------------------------------------------------------

def diagnose_bug(
    state: BugInvestigationState,
    llm_provider,
) -> dict[str, Any]:
    """
    Run one diagnosis pass.

    Pass 1:
        repository evidence -> hypotheses

    Pass 2:
        additional verification evidence -> final diagnosis

    The graph controls how many times this function is called.
    """

    verification_attempts = state.get(
        "verification_attempts",
        0,
    )

    if verification_attempts > 0:
        prompt = _build_verification_prompt(
            state,
        )
    else:
        prompt = _build_initial_prompt(
            state,
        )

    # The provider is responsible for enforcing the completion
    # token/reasoning budget.
    response = llm_provider.generate(
        prompt,
    )

    diagnosis_data = _extract_json_object(
        response,
    )

    # If the model did not return usable JSON, preserve the raw
    # response instead of crashing the investigation graph.
    if not diagnosis_data:
        return {
            "diagnosis": response,
            "root_cause": "",
            "debugging_steps": [],
            "confidence": "Low",
            "verification_queries": [],
            "hypotheses": [],
            "likely_locations": [],
        }

    # ------------------------------------------------------------------
    # Normalize model output
    # ------------------------------------------------------------------

    proven_facts = _normalize_list(
        diagnosis_data.get(
            "proven_facts",
            [],
        )
    )

    confirmed_hypotheses = _normalize_list(
        diagnosis_data.get(
            "confirmed_hypotheses",
            [],
        )
    )

    unresolved_hypotheses = _normalize_list(
        diagnosis_data.get(
            "unresolved_hypotheses",
            [],
        )
    )

    verification_queries = validate_verification_queries(
        _normalize_list(
            diagnosis_data.get(
                "verification_queries",
                [],
            )
        )
    )

    # ------------------------------------------------------------------
    # Deterministic fallback verification queries
    # ------------------------------------------------------------------

    # If the initial model identified relevant repository locations
    # but failed to provide verification queries, create deterministic
    # source-code queries from those locations.
    if (
        verification_attempts == 0
        and not verification_queries
    ):
        fallback_queries = (
            _build_fallback_verification_queries(
                diagnosis_data
            )
        )

        verification_queries = validate_verification_queries(
            fallback_queries
        )

    diagnosis_data["verification_queries"] = (
        verification_queries
    )

    # ------------------------------------------------------------------
    # Root cause handling
    # ------------------------------------------------------------------

    # On the verification pass, the second LLM call is itself
    # responsible for evaluating the hypotheses.
    #
    # There is deliberately no additional LLM call here.
    #
    # Therefore one investigation requires at most two
    # diagnosis-model calls.

    if verification_attempts > 0:

        if not confirmed_hypotheses:
            root_cause = ""

        else:
            root_cause = str(
                diagnosis_data.get(
                    "root_cause",
                    "",
                )
            ).strip()

    else:

        root_cause = str(
            diagnosis_data.get(
                "root_cause",
                "",
            )
        ).strip()

    # ------------------------------------------------------------------
    # Consistency validation
    # ------------------------------------------------------------------

    evidence = _build_evidence(
        state,
    )

    consistency_result = validate_diagnosis_output(
        diagnosis_data=diagnosis_data,
        evidence=evidence,
    )

    root_cause = consistency_result[
        "root_cause"
    ]

    debugging_steps = consistency_result[
        "debugging_steps"
    ]

    likely_locations = consistency_result[
        "likely_locations"
    ]

    confidence = str(
        diagnosis_data.get(
            "confidence",
            "Low",
        )
    ).strip()

    # A root cause cannot exist without at least one confirmed
    # hypothesis.
    if not confirmed_hypotheses:
        root_cause = ""
        confidence = "Low"

    if root_cause and confidence not in {
        "High",
        "Medium",
    }:
        confidence = "Medium"

    if not root_cause:
        confidence = "Low"

    # ------------------------------------------------------------------
    # Final structured output
    # ------------------------------------------------------------------

    final_output = {
        "proven_facts": proven_facts,
        "confirmed_hypotheses": confirmed_hypotheses,
        "unresolved_hypotheses": unresolved_hypotheses,
        "likely_locations": likely_locations,
        "root_cause": root_cause,
        "debugging_steps": debugging_steps,
        "verification_queries": verification_queries,
        "confidence": confidence,
    }

    diagnosis_text = json.dumps(
        final_output,
        indent=2,
    )

    return {
        "diagnosis": diagnosis_text,
        "root_cause": root_cause,
        "debugging_steps": debugging_steps,
        "confidence": confidence,
        "verification_queries": verification_queries,
        "hypotheses": (
            confirmed_hypotheses
            + unresolved_hypotheses
        ),
        "likely_locations": likely_locations,
    }