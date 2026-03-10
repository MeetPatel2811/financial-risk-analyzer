"""Integration tests that call the real OpenAI API. Run with OPENAI_API_KEY set or RUN_LLM_TESTS=1."""

import os

import pytest

from financial_risk_analyzer.config import Settings
from financial_risk_analyzer.models import Transaction
from financial_risk_analyzer.pipeline import run_pipeline


def _tx(account_id: str, amount: float, ts: str, status: str = "completed") -> Transaction:
    return Transaction(
        transaction_id=f"T-{account_id}",
        account_id=account_id,
        transaction_amount=amount,
        transaction_type="transfer",
        timestamp=ts,
        status=status,
    )


@pytest.mark.llm
def test_pipeline_real_llm_returns_valid_results() -> None:
    """Call real OpenAI API; assert we get valid RiskResult shape and no crash."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        pytest.skip("OPENAI_API_KEY not set")
    settings = Settings(openai_api_key=key, openai_model=os.environ.get("OPENAI_MODEL", "gpt-4"), max_retries=2, log_level="INFO")
    # Small input: one account, a few transactions (minimal tokens)
    txs = [
        _tx("A1", 100.0, "2024-03-01 10:00:00"),
        _tx("A1", 50.0, "2024-03-01 12:00:00"),
    ]
    results = run_pipeline(txs, settings, use_llm=True)
    assert len(results) == 1
    account_id, risk_result = results[0]
    assert account_id == "A1"
    assert hasattr(risk_result, "risk_flag")
    assert hasattr(risk_result, "risk_type")
    assert hasattr(risk_result, "confidence")
    assert hasattr(risk_result, "explanation")
    assert isinstance(risk_result.risk_flag, bool)
    assert 0 <= risk_result.confidence <= 1
    assert isinstance(risk_result.explanation, str)
