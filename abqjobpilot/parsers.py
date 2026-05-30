"""Lightweight Abaqus status parsers for the MVP."""

from __future__ import annotations

import re


SUCCESS_PATTERN = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"
FATAL_PATTERNS = (
    "THE ANALYSIS HAS BEEN TERMINATED",
    "Abaqus/Standard aborted",
    "Too many attempts made for this increment",
    "Analysis Input File Processor exited with an error",
    "THE ANALYSIS HAS NOT BEEN COMPLETED",
    "Abaqus Error",
    "Error in job",
)
NON_FATAL_ERROR_PHRASES = (
    "CONTACT FORCE ERROR TOLERANCE",
    "force error tolerance",
    "residual error",
    "relative error",
)


def _contains_success(text: str) -> bool:
    return SUCCESS_PATTERN in text.upper()


def _fatal_matches(text: str) -> list[str]:
    matches: list[str] = []
    lines = text.splitlines() or [text]
    for line in lines:
        if any(phrase.lower() in line.lower() for phrase in NON_FATAL_ERROR_PHRASES):
            continue
        for pattern in FATAL_PATTERNS:
            if pattern.lower() in line.lower():
                matches.append(pattern)
                break
    return matches


def parse_sta_status(sta_text: str) -> dict:
    status = {
        "step": "",
        "increment": "",
        "analysis_time": "",
        "last_numeric_line": "",
        "completed_successfully": _contains_success(sta_text),
        "fatal_detected": False,
        "fatal_reason": "",
    }
    matches = _fatal_matches(sta_text)
    if matches:
        status["fatal_detected"] = True
        status["fatal_reason"] = matches[0]

    numeric_lines: list[list[str]] = []
    for line in sta_text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
            numeric_lines.append(parts)
            status["last_numeric_line"] = line.strip()
    if numeric_lines:
        latest = numeric_lines[-1]
        status["step"] = latest[0]
        status["increment"] = latest[1]
        for token in reversed(latest):
            if re.search(r"[0-9]", token):
                status["analysis_time"] = token
                break
    return status


def parse_console_status(log_text: str) -> dict:
    matches = _fatal_matches(log_text)
    warning_count = len(re.findall(r"\bWARNING\b", log_text, flags=re.IGNORECASE))
    return {
        "completed_successfully": _contains_success(log_text),
        "fatal_detected": bool(matches),
        "fatal_reason": matches[0] if matches else "",
        "warning_count": warning_count,
    }


def classify_final_verdict(
    sta_text: str = "",
    msg_text: str = "",
    dat_text: str = "",
    log_text: str = "",
    return_code: int | None = None,
) -> dict:
    combined = "\n".join([sta_text or "", msg_text or "", dat_text or "", log_text or ""])
    matches = _fatal_matches(combined)
    warning_count = len(re.findall(r"\bWARNING\b", combined, flags=re.IGNORECASE))

    if matches:
        return {
            "status": "FAILED_FATAL",
            "final_verdict": "FAILED",
            "fatal_reason": matches[0],
            "warning_count": warning_count,
        }
    if return_code not in (None, 0):
        return {
            "status": "UNKNOWN_INTERRUPTED",
            "final_verdict": "FAILED",
            "fatal_reason": f"non-zero return code: {return_code}",
            "warning_count": warning_count,
        }
    if _contains_success(combined):
        return {
            "status": "COMPLETED_WITH_WARNINGS" if warning_count else "COMPLETED_OK",
            "final_verdict": "SUCCESS",
            "fatal_reason": "",
            "warning_count": warning_count,
        }
    return {
        "status": "UNKNOWN_INTERRUPTED",
        "final_verdict": "UNKNOWN",
        "fatal_reason": "",
        "warning_count": warning_count,
    }
