"""OpenAI API call and prompt construction for risk analysis."""

import logging
import time
from typing import Any

from financial_risk_analyzer.config import Settings
from financial_risk_analyzer.metrics import get_metrics
from financial_risk_analyzer.models import RiskResult
from financial_risk_analyzer.validation import validate_risk_response

logger = logging.getLogger(__name__)

# API behavior constants for deterministic outputs
MAX_TOKENS = 500
TEMPERATURE = 0.2

SYSTEM_PROMPT = """You are a financial operations risk analyst. Analyze transaction summaries and identify risk indicators.
Return only valid JSON with exactly these keys: risk_flag (boolean), risk_type (string or null), confidence (float 0-1), explanation (string).
When risk_flag is true, risk_type and explanation must be non-empty. Risk types may include: abnormal_transaction_frequency, possible_duplicate_transactions, inconsistent_transaction_states."""

USER_PROMPT_TEMPLATE = """Analyze the following transaction summary and determine if it contains risk indicators such as duplicate transactions, abnormal frequency, or inconsistent states. Return the result in JSON format only.

Transaction summary:
{summary}"""

USER_PROMPT_RETRY_TEMPLATE = """Return only valid JSON with keys: risk_flag, risk_type, confidence, explanation. No other text.

Transaction summary:
{summary}"""


def build_messages(summary: str, *, strict_retry: bool = False) -> list[dict[str, str]]:
    template = USER_PROMPT_RETRY_TEMPLATE if strict_retry else USER_PROMPT_TEMPLATE
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": template.format(summary=summary)},
    ]


def call_llm(summary: str, settings: Settings, *, strict_retry: bool = False) -> str:
    """
    Call OpenAI API with the given summary. Returns raw response content string.
    Raises on API or network errors.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("openai package is required; install with: pip install openai") from None

    client = OpenAI(api_key=settings.openai_api_key)
    messages = build_messages(summary, strict_retry=strict_retry)
    # Do not use response_format={"type": "json_object"} — not all models support it (e.g. some return 400).
    # The prompt asks for JSON only; validation + retry + fallback handle non-JSON or malformed output.
    kwargs: dict[str, Any] = {
        "model": settings.openai_model,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }
    start = time.perf_counter()
    response = client.chat.completions.create(**kwargs)
    duration_sec = time.perf_counter() - start
    content = response.choices[0].message.content
    m = get_metrics()
    m.llm_calls_total += 1
    m.llm_calls_duration_sec += duration_sec
    logger.debug("LLM call completed in %.2fs", duration_sec)
    return content or ""


def analyze_with_retry(
    summary: str,
    settings: Settings,
) -> tuple[RiskResult | None, str | None]:
    """
    Call LLM with retries on validation failure. Returns (RiskResult, None) on success,
    or (None, error_message) after max retries (caller should use fallback).
    """
    metrics = get_metrics()
    for attempt in range(settings.max_retries):
        strict = attempt > 0
        if attempt > 0:
            metrics.llm_retries_total += 1
        try:
            raw = call_llm(summary, settings, strict_retry=strict)
        except Exception as e:
            logger.warning("LLM call failed (attempt %s): %s", attempt + 1, e)
            if attempt == settings.max_retries - 1:
                return None, str(e)
            continue
        result, err = validate_risk_response(raw)
        if result is not None:
            return result, None
        metrics.llm_validation_failures += 1
        logger.debug("Validation failed (attempt %s): %s", attempt + 1, err)
    return None, "Validation failed after max retries"
