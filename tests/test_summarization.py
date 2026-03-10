"""Tests for summarization module."""

from financial_risk_analyzer.models import Transaction
from financial_risk_analyzer.summarization import (
    summarize_by_account,
    summarize_transactions,
)


def _tx(account_id: str, amount: float, ts: str, type_: str = "transfer", status: str = "completed") -> Transaction:
    return Transaction(
        transaction_id=f"T-{account_id}-{ts}",
        account_id=account_id,
        transaction_amount=amount,
        transaction_type=type_,
        timestamp=ts,
        status=status,
    )


def test_summarize_empty() -> None:
    assert "No transactions" in summarize_transactions([])


def test_summarize_single() -> None:
    txs = [_tx("A102", 100.0, "2024-03-01 10:00:00")]
    s = summarize_transactions(txs)
    assert "A102" in s
    assert "1 transaction" in s
    assert "100" in s


def test_summarize_rapid_same_amount() -> None:
    txs = [
        _tx("A102", 5000.0, "2024-03-01 10:05:00"),
        _tx("A102", 5000.0, "2024-03-01 10:07:00"),
        _tx("A102", 5000.0, "2024-03-01 10:09:00"),
    ]
    s = summarize_transactions(txs)
    assert "A102" in s
    assert "3" in s
    assert "5,000" in s or "5000" in s
    assert "Same amount repeated" in s
    assert "typical transaction frequency" in s or "minutes" in s


def test_summarize_by_account() -> None:
    txs = [
        _tx("A1", 50.0, "2024-03-01 10:00:00"),
        _tx("A1", 60.0, "2024-03-01 12:00:00"),
        _tx("A2", 100.0, "2024-03-01 11:00:00"),
    ]
    by_account = summarize_by_account(txs)
    assert set(by_account.keys()) == {"A1", "A2"}
    assert "A1" in by_account["A1"]
    assert "A2" in by_account["A2"]
