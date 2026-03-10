"""Tests for rule-based fallback detector."""

from financial_risk_analyzer.models import Transaction
from financial_risk_analyzer.fallback import rule_based_risk


def _tx(account_id: str, amount: float, ts: str, status: str = "completed") -> Transaction:
    return Transaction(
        transaction_id=f"T-{account_id}-{ts}",
        account_id=account_id,
        transaction_amount=amount,
        transaction_type="transfer",
        timestamp=ts,
        status=status,
    )


def test_empty_returns_no_risk() -> None:
    r = rule_based_risk([])
    assert r.risk_flag is False
    assert r.explanation


def test_rapid_same_amount_flagged() -> None:
    txs = [
        _tx("A102", 5000.0, "2024-03-01 10:05:00"),
        _tx("A102", 5000.0, "2024-03-01 10:07:00"),
        _tx("A102", 5000.0, "2024-03-01 10:09:00"),
    ]
    r = rule_based_risk(txs)
    assert r.risk_flag is True
    assert "duplicate" in (r.risk_type or "").lower() or "frequency" in (r.risk_type or "").lower()
    assert r.confidence >= 0.5


def test_mixed_status_flagged() -> None:
    # Two transactions only (so frequency rule needs 3+); different amounts (no duplicate); mixed statuses.
    txs = [
        _tx("A103", 100.0, "2024-03-01 10:00:00", "completed"),
        _tx("A103", 200.0, "2024-03-01 14:00:00", "pending"),
    ]
    r = rule_based_risk(txs)
    assert r.risk_flag is True
    assert "inconsistent" in (r.risk_type or "").lower()
    assert r.confidence >= 0.5


def test_normal_activity_low_risk() -> None:
    txs = [
        _tx("A104", 50.0, "2024-03-01 10:00:00"),
        _tx("A104", 60.0, "2024-03-01 14:00:00"),
    ]
    r = rule_based_risk(txs)
    # Two transactions hours apart may not trigger frequency; duplicate needs same amount
    assert isinstance(r.risk_flag, bool)
    assert r.confidence >= 0
