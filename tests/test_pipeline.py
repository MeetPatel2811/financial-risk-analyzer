"""Tests for pipeline orchestration with mocked LLM."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from financial_risk_analyzer.config import Settings
from financial_risk_analyzer.models import RiskResult, Transaction
from financial_risk_analyzer.pipeline import run_pipeline, run_pipeline_from_file


def _tx(account_id: str, amount: float, ts: str, status: str = "completed") -> Transaction:
    return Transaction(
        transaction_id=f"T-{account_id}",
        account_id=account_id,
        transaction_amount=amount,
        transaction_type="transfer",
        timestamp=ts,
        status=status,
    )


@pytest.fixture
def settings_no_key() -> Settings:
    return Settings(openai_api_key="", openai_model="gpt-4", max_retries=2, log_level="INFO")


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    return [
        _tx("A102", 5000.0, "2024-03-01 10:05:00"),
        _tx("A102", 5000.0, "2024-03-01 10:07:00"),
        _tx("A103", 100.0, "2024-03-01 10:00:00", "completed"),
        _tx("A103", 100.0, "2024-03-01 10:05:00", "pending"),
    ]


def test_pipeline_without_llm_uses_fallback(settings_no_key: Settings, sample_transactions: list[Transaction]) -> None:
    results = run_pipeline(sample_transactions, settings_no_key, use_llm=False)
    assert len(results) == 2  # A102, A103
    account_ids = {r[0] for r in results}
    assert account_ids == {"A102", "A103"}
    for account_id, r in results:
        assert isinstance(r, RiskResult)
        assert hasattr(r, "risk_flag")
        assert hasattr(r, "confidence")
        assert hasattr(r, "explanation")
        assert 0 <= r.confidence <= 1


def test_pipeline_with_mocked_llm_valid_response(
    sample_transactions: list[Transaction],
) -> None:
    settings = Settings(openai_api_key="sk-test", openai_model="gpt-4", max_retries=2, log_level="INFO")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = (
        '{"risk_flag": true, "risk_type": "abnormal_transaction_frequency", '
        '"confidence": 0.86, "explanation": "Multiple high-value transfers in short window."}'
    )

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        results = run_pipeline(sample_transactions, settings, use_llm=True)
    assert len(results) == 2
    # At least one result should come from LLM (risk_flag true with our mock)
    risk_results = [r for _, r in results]
    assert any(r.risk_flag and r.risk_type == "abnormal_transaction_frequency" for r in risk_results)


def test_pipeline_with_mocked_llm_invalid_then_fallback(
    sample_transactions: list[Transaction],
) -> None:
    settings = Settings(openai_api_key="sk-test", openai_model="gpt-4", max_retries=2, log_level="INFO")
    # First call returns invalid JSON, so after retries we fall back to rules
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "not valid json"

    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        results = run_pipeline(sample_transactions, settings, use_llm=True)
    assert len(results) == 2
    for _, r in results:
        assert isinstance(r, RiskResult)
        assert 0 <= r.confidence <= 1


def test_pipeline_from_file_uses_fallback_when_no_key(tmp_path: Path, settings_no_key: Settings) -> None:
    import json
    data = [
        {
            "transaction_id": "T1",
            "account_id": "A1",
            "transaction_amount": 100.0,
            "transaction_type": "transfer",
            "timestamp": "2024-03-01 10:00:00",
            "status": "completed",
        },
    ]
    path = tmp_path / "tx.json"
    path.write_text(json.dumps(data))
    results = run_pipeline_from_file(path, settings_no_key, use_llm=False)
    assert len(results) == 1
    assert results[0][0] == "A1"
    assert isinstance(results[0][1], RiskResult)
