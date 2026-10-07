from typing import Any

from app.services.agents.feature_plan_validation import (
    validate_existing_files,
    separate_existing_and_missing_files,
)


MAX_PLANNING_EVIDENCE_CHARS = 6000


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        return [value]

    if isinstance(value, list):
        result = []

        for item in value:
            if isinstance(item, str):
                item = item.strip()

                if item:
                    result.append(item)

        return result

    return []


def _normalize_file_list(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    result = []

    for item in value:

        if not isinstance(item, dict):
            continue

        file_path = item.get("file")

        if not isinstance(file_path, str):
            continue

        file_path = file_path.strip()

        if not file_path:
            continue

        result.append(
            {
                "file": file_path,
                "reason": str(
                    item.get(
                        "reason",
                        "",
                    )
                ).strip(),
            }
        )

    return result


def _normalize_new_files(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    result = []

    for item in value:

        if not isinstance(item, dict):
            continue

        file_path = item.get("file")

        if not isinstance(file_path, str):
            continue

        file_path = file_path.strip()

        if not file_path:
            continue

        result.append(
            {
                "file": file_path,
                "purpose": str(
                    item.get(
                        "purpose",
                        "",
                    )
                ).strip(),
            }
        )

    return result


def _extract_json_object(
    text: str,
) -> dict[str, Any]:

    import json

    text = text.strip()

    if not text:
        raise ValueError(
            "Planning model returned an empty response."
        )

    try:

        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if (
        start == -1
        or end == -1
        or end <= start
    ):
        raise ValueError(
            "Planning model did not return a valid JSON object."
        )

    candidate = text[
        start : end + 1
    ]

    try:

        parsed = json.loads(
            candidate
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Planning model returned malformed JSON."
        ) from exc

    if not isinstance(parsed, dict):

        raise ValueError(
            "Planning model response is not a JSON object."
        )

    return parsed


def _build_evidence(
    retrieval_results: list[dict[str, Any]],
) -> str:

    sections = []

    total_chars = 0

    for index, result in enumerate(
        retrieval_results,
        start=1,
    ):

        file_path = result.get(
            "file_path",
            "Unknown",
        )

        start_line = result.get(
            "start_line",
            "?",
        )

        end_line = result.get(
            "end_line",
            "?",
        )

        content = str(
            result.get(
                "content",
                "",
            )
        ).strip()

        if not content:
            continue

        section = (
            f"[Evidence {index}]\n"
            f"File: {file_path}\n"
            f"Lines: {start_line}-{end_line}\n"
            f"Code:\n{content}"
        )

        if (
            total_chars
            + len(section)
            > MAX_PLANNING_EVIDENCE_CHARS
        ):

            remaining = (
                MAX_PLANNING_EVIDENCE_CHARS
                - total_chars
            )

            if remaining <= 0:
                break

            section = section[
                :remaining
            ]

        sections.append(section)

        total_chars += len(section)

        if (
            total_chars
            >= MAX_PLANNING_EVIDENCE_CHARS
        ):
            break

    if not sections:
        return (
            "No repository evidence was retrieved."
        )

    return (
        "\n\n"
        + (
            "\n"
            + "=" * 80
            + "\n"
        ).join(sections)
    )


def _build_prompt(
    feature_request: str,
    evidence: str,
) -> str:

    return f"""
You are a senior software engineer planning a feature change in an
existing code repository.

FEATURE REQUEST:
{feature_request}

REPOSITORY EVIDENCE:
{evidence}

Your task is to produce a practical implementation plan grounded in
the repository evidence.

IMPORTANT RULES:

1. Do not invent existing files, functions, modules, APIs, database
   models, or behavior.

2. Only identify an existing file as an affected file when the
   repository evidence supports that it exists or is relevant.

3. A file that does not currently exist may be proposed as a NEW file.

4. Clearly distinguish existing files from proposed new files.

5. Do not claim that a specific function exists unless the evidence
   shows it.

6. Do not claim that the requested feature is already implemented.

7. Implementation steps must explain what should change and where.

8. Data flow should describe the expected request/data path using the
   existing architecture and proposed new components.

9. Include meaningful testing ideas.

10. Include assumptions when repository evidence is insufficient.

11. Do not assume a Redis configuration file exists merely because Redis
    is mentioned in the feature request.

12. Do not assume a function such as get_balance or update_balance exists
    unless repository evidence shows it.

13. If evidence is insufficient to identify an exact file, say so in
    assumptions instead of inventing a path.

14. Confidence must be one of:
    - High
    - Medium
    - Low

15. Return ONLY valid JSON.

Return exactly this structure:

{{
  "feature": "{feature_request}",
  "implementation_overview": "",
  "affected_files": [
    {{
      "file": "",
      "reason": ""
    }}
  ],
  "affected_modules": [],
  "new_files": [
    {{
      "file": "",
      "purpose": ""
    }}
  ],
  "implementation_steps": [],
  "data_flow": [],
  "risks": [],
  "tests": [],
  "assumptions": [],
  "confidence": "Low"
}}
""".strip()


def _deduplicate_files(
    files: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result = []

    seen: set[str] = set()

    for item in files:

        file_path = item.get(
            "file",
            "",
        )

        if not isinstance(
            file_path,
            str,
        ):
            continue

        key = file_path.lower()

        if key in seen:
            continue

        seen.add(key)

        result.append(item)

    return result


def _validate_and_classify_files(
    repository_root: str,
    affected_files: list[dict[str, Any]],
    new_files: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:

    validated_affected = (
        validate_existing_files(
            repository_root=repository_root,
            affected_files=affected_files,
        )
    )

    existing_files, missing_files = (
        separate_existing_and_missing_files(
            validated_affected
        )
    )

    final_existing_files = []

    for item in existing_files:

        final_existing_files.append(
            {
                "file": item["file"],
                "status": "existing",
                "reason": item.get(
                    "reason",
                    "",
                ),
            }
        )

    final_new_files = []

    for item in new_files:

        file_path = item.get(
            "file",
            "",
        )

        if not isinstance(
            file_path,
            str,
        ):
            continue

        file_path = file_path.strip()

        if not file_path:
            continue

        validated = validate_existing_files(
            repository_root=repository_root,
            affected_files=[
                {
                    "file": file_path,
                    "reason": item.get(
                        "purpose",
                        "",
                    ),
                }
            ],
        )

        if validated and validated[0].get(
            "exists"
        ) is True:

            # The LLM proposed this as a new file,
            # but the filesystem proves that it already exists.
            final_existing_files.append(
                {
                    "file": file_path,
                    "status": "existing",
                    "reason": (
                        "This file was proposed as new by "
                        "the planning model, but it already "
                        "exists in the repository."
                    ),
                }
            )

        else:

            final_new_files.append(
                {
                    "file": file_path,
                    "status": "new",
                    "purpose": item.get(
                        "purpose",
                        "",
                    ),
                }
            )

    for item in missing_files:

        file_path = item.get(
            "file"
        )

        if not isinstance(
            file_path,
            str,
        ):
            continue

        if not file_path.strip():
            continue

        already_present = any(
            existing.get("file") == file_path
            for existing in final_new_files
        )

        if already_present:
            continue

        final_new_files.append(
            {
                "file": file_path,
                "status": "new",
                "purpose": item.get(
                    "reason",
                    "Proposed new file.",
                ),
            }
        )

    final_existing_files = (
        _deduplicate_files(
            final_existing_files
        )
    )

    final_new_files = (
        _deduplicate_files(
            final_new_files
        )
    )

    return (
        final_existing_files,
        final_new_files,
    )


def plan_feature(
    state: dict[str, Any],
    llm_provider,
) -> dict[str, Any]:

    feature_request = str(
        state.get(
            "feature_request",
            "",
        )
    ).strip()

    if not feature_request:
        raise ValueError(
            "Feature request cannot be empty."
        )

    retrieval_results = state.get(
        "retrieval_results",
        [],
    )

    evidence = _build_evidence(
        retrieval_results
    )

    prompt = _build_prompt(
        feature_request=feature_request,
        evidence=evidence,
    )

    response = llm_provider.generate(
        prompt
    )

    parsed = _extract_json_object(
        response
    )

    affected_files = (
        _normalize_file_list(
            parsed.get(
                "affected_files"
            )
        )
    )

    new_files = (
        _normalize_new_files(
            parsed.get(
                "new_files"
            )
        )
    )

    repository_root = state.get(
        "repository_root"
    )

    if repository_root:

        (
            affected_files,
            new_files,
        ) = _validate_and_classify_files(
            repository_root=repository_root,
            affected_files=affected_files,
            new_files=new_files,
        )

    else:

        affected_files = [
            {
                **item,
                "status": "unverified",
            }
            for item in affected_files
        ]

        new_files = [
            {
                **item,
                "status": "unverified",
            }
            for item in new_files
        ]

    implementation_steps = (
        _normalize_list(
            parsed.get(
                "implementation_steps"
            )
        )
    )

    data_flow = (
        _normalize_list(
            parsed.get(
                "data_flow"
            )
        )
    )

    tests = (
        _normalize_list(
            parsed.get(
                "tests"
            )
        )
    )

    risks = (
        _normalize_list(
            parsed.get(
                "risks"
            )
        )
    )

    assumptions = (
        _normalize_list(
            parsed.get(
                "assumptions"
            )
        )
    )

    affected_modules = (
        _normalize_list(
            parsed.get(
                "affected_modules"
            )
        )
    )

    confidence = str(
        parsed.get(
            "confidence",
            "Low",
        )
    ).strip()

    if confidence not in {
        "High",
        "Medium",
        "Low",
    }:
        confidence = "Low"

    return {
        **state,

        "affected_files":
            affected_files,

        "affected_modules":
            affected_modules,

        "new_files":
            new_files,

        "implementation_overview":
            str(
                parsed.get(
                    "implementation_overview",
                    "",
                )
            ).strip(),

        "implementation_steps":
            implementation_steps,

        "data_flow":
            data_flow,

        "risks":
            risks,

        "tests":
            tests,

        "assumptions":
            assumptions,

        "confidence":
            confidence,

        "plan":
            response,
    }