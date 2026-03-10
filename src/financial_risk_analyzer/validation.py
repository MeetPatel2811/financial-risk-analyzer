"""Validate LLM response JSON and produce RiskResult or error.

Caller should use (RiskResult, None) for success and (None, error_message) to trigger retry or fallback.
"""

import json
import logging
import re

from financial_risk_analyzer.models import RiskResult

logger = logging.getLogger(__name__)

REQUIRED_KEYS = frozenset({"risk_flag", "risk_type", "confidence", "explanation"})
_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def validate_risk_response(raw: str) -> tuple[RiskResult | None, str | None]:
    """
    Validate raw LLM response. Returns (RiskResult, None) on success,
    or (None, error_message) on failure for retry/fallback.
    """
    raw = raw.strip()
    # Strip markdown code fence if present (e.g. ```json ... ```)
    match = _CODE_FENCE_PATTERN.match(raw)
    if match:
        raw = match.group(1).strip()
    elif raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.debug("Invalid JSON from LLM: %s", e)
        return None, f"Invalid JSON: {e}"

    if not isinstance(data, dict):
        return None, "Response is not a JSON object"

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        return None, f"Missing required keys: {sorted(missing)}"

    try:
        risk_flag = data["risk_flag"]
        if not isinstance(risk_flag, bool):
            risk_flag = str(risk_flag).lower() in ("true", "1", "yes")
    except (KeyError, TypeError):
        return None, "Invalid or missing risk_flag"

    try:
        confidence = data["confidence"]
        if isinstance(confidence, (int, float)):
            c = float(confidence)
        else:
            c = float(str(confidence))
        if not (0 <= c <= 1):
            return None, "confidence must be between 0 and 1"
    except (KeyError, ValueError, TypeError):
        return None, "Invalid or missing confidence"

    risk_type = data.get("risk_type")
    if risk_type is not None and not isinstance(risk_type, str):
        risk_type = str(risk_type)
    explanation = data.get("explanation")
    if not isinstance(explanation, str):
        explanation = str(explanation) if explanation is not None else ""

    if risk_flag and (not risk_type or not risk_type.strip()):
        return None, "risk_type must be non-empty when risk_flag is true"
    if risk_flag and (not explanation or not explanation.strip()):
        return None, "explanation must be non-empty when risk_flag is true"

    return (
        RiskResult(
            risk_flag=risk_flag,
            risk_type=risk_type.strip() if risk_type else None,
            confidence=c,
            explanation=explanation.strip() or "No explanation",
        ),
        None,
    )
