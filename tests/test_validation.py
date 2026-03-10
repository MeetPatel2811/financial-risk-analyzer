"""Tests for validation module."""

import pytest

from financial_risk_analyzer.models import RiskResult
from financial_risk_analyzer.validation import validate_risk_response


def test_valid_response() -> None:
    raw = '''{"risk_flag": true, "risk_type": "abnormal_transaction_frequency", "confidence": 0.86, "explanation": "Multiple high-value transfers in short window."}'''
    result, err = validate_risk_response(raw)
    assert err is None
    assert result is not None
    assert result.risk_flag is True
    assert result.risk_type == "abnormal_transaction_frequency"
    assert result.confidence == 0.86
    assert "Multiple high-value" in result.explanation


def test_valid_no_risk() -> None:
    raw = '''{"risk_flag": false, "risk_type": null, "confidence": 0.1, "explanation": "No significant pattern."}'''
    result, err = validate_risk_response(raw)
    assert err is None
    assert result is not None
    assert result.risk_flag is False
    assert result.confidence == 0.1


def test_invalid_json() -> None:
    result, err = validate_risk_response("not json at all")
    assert result is None
    assert err is not None
    assert "JSON" in err


def test_missing_keys() -> None:
    raw = '{"risk_flag": true}'
    result, err = validate_risk_response(raw)
    assert result is None
    assert err is not None
    assert "Missing" in err or "key" in err.lower()


def test_confidence_out_of_range() -> None:
    raw = '''{"risk_flag": false, "risk_type": null, "confidence": 1.5, "explanation": "x"}'''
    result, err = validate_risk_response(raw)
    assert result is None
    assert err is not None


def test_risk_flag_true_requires_non_empty_type_and_explanation() -> None:
    raw = '''{"risk_flag": true, "risk_type": "", "confidence": 0.8, "explanation": "something"}'''
    result, err = validate_risk_response(raw)
    assert result is None
    assert err is not None

    raw2 = '''{"risk_flag": true, "risk_type": "dup", "confidence": 0.8, "explanation": ""}'''
    result2, err2 = validate_risk_response(raw2)
    assert result2 is None
    assert err2 is not None


def test_strips_markdown_fence() -> None:
    raw = '''```json
{"risk_flag": false, "risk_type": null, "confidence": 0.0, "explanation": "ok"}
```'''
    result, err = validate_risk_response(raw)
    assert err is None
    assert result is not None
    assert result.risk_flag is False
