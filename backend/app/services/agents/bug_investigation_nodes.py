import re
from typing import Any

from app.services.agents.bug_investigation_state import (
    BugInvestigationState,
)


def _extract_error_type(bug_report: str) -> str:
    """
    Extract a common error/exception type from the bug report.
    """

    patterns = [
        r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b",
        r"\b([A-Za-z_][A-Za-z0-9_]*Error)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, bug_report)
        if match:
            return match.group(1)

    return ""


def _extract_files(bug_report: str) -> list[str]:
    """
    Extract likely source filenames from the bug report or stack trace.
    """

    patterns = [
        r"\b[\w./\\-]+\.(?:py|ts|tsx|js|jsx|java|cpp|cc|c|h|hpp|go|rs)\b",
    ]

    files: list[str] = []

    for pattern in patterns:
        for match in re.findall(pattern, bug_report):
            if match not in files:
                files.append(match)

    return files


def _extract_functions(bug_report: str) -> list[str]:
    """
    Extract likely function names from stack-trace-style lines.

    Examples:
        at processRefund (...)
        at paymentService.payOrder (...)
    """

    functions: list[str] = []

    patterns = [
        # JavaScript / TypeScript stack traces:
        # at processRefund (...)
        r"\bat\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(",

        # Python-style:
        # in process_refund
        r"\bin\s+([A-Za-z_][A-Za-z0-9_]*)",

        # Generic function call:
        # processRefund(...)
        r"\b([A-Za-z_$][\w$]*)\s*\(",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, bug_report):
            function_name = match.strip()

            if function_name and function_name not in functions:
                functions.append(function_name)

    return functions


def _extract_error_message(
    bug_report: str,
    error_type: str,
) -> str:
    """
    Extract a useful error message from the bug report.

    This intentionally stays heuristic for now.
    A later LLM-based extraction step can improve this.
    """

    if not error_type:
        return ""

    lines = [
        line.strip()
        for line in bug_report.splitlines()
        if line.strip()
    ]

    for line in lines:
        if error_type in line:
            message = line

            # Remove common stack-trace prefixes.
            message = re.sub(
                r"^(?:Error:|Exception:)\s*",
                "",
                message,
                flags=re.IGNORECASE,
            )

            return message.strip()

    return ""


def extract_bug_signals(
    state: BugInvestigationState,
) -> dict[str, Any]:
    """
    Extract structured signals from the user's bug report.

    This is the first node of the Bug Investigation workflow.
    """

    bug_report = state.get("bug_report", "").strip()

    if not bug_report:
        return {
            "error_type": "",
            "error_message": "",
            "stack_trace": "",
            "extracted_files": [],
            "extracted_functions": [],
            "extracted_symbols": [],
        }

    error_type = _extract_error_type(bug_report)
    error_message = _extract_error_message(
        bug_report,
        error_type,
    )

    files = _extract_files(bug_report)
    functions = _extract_functions(bug_report)

    # Symbols are currently the union of useful identifiers
    # extracted from the report.
    symbols: list[str] = []

    for value in functions + files:
        if value not in symbols:
            symbols.append(value)

    return {
        "error_type": error_type,
        "error_message": error_message,
        "stack_trace": bug_report,
        "extracted_files": files,
        "extracted_functions": functions,
        "extracted_symbols": symbols,
    }