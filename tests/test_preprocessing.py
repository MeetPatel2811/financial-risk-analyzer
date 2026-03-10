"""Tests for preprocessing module."""

import json
import tempfile
from pathlib import Path

import pytest

from financial_risk_analyzer.models import Transaction
from financial_risk_analyzer.preprocessing import (
    load_transactions_from_dicts,
    load_transactions_from_file,
)


def test_load_from_dicts_valid() -> None:
    data = [
        {
            "transaction_id": "T1",
            "account_id": "A102",
            "transaction_amount": 5000.0,
            "transaction_type": "transfer",
            "timestamp": "2024-03-01 10:05:00",
            "status": "completed",
        },
    ]
    out = load_transactions_from_dicts(data)
    assert len(out) == 1
    assert out[0].transaction_id == "T1"
    assert out[0].account_id == "A102"
    assert out[0].transaction_amount == 5000.0
    assert out[0].transaction_type == "transfer"
    assert out[0].status == "completed"


def test_load_from_dicts_skips_negative_amount() -> None:
    data = [
        {
            "transaction_id": "T1",
            "account_id": "A102",
            "transaction_amount": -100,
            "transaction_type": "transfer",
            "timestamp": "2024-03-01 10:05:00",
            "status": "completed",
        },
    ]
    out = load_transactions_from_dicts(data)
    assert len(out) == 0


def test_load_from_dicts_skips_malformed() -> None:
    data = [
        {"transaction_id": "T1"},  # missing required
        {
            "transaction_id": "T2",
            "account_id": "A102",
            "transaction_amount": "not_a_number",
            "transaction_type": "transfer",
            "timestamp": "2024-03-01 10:05:00",
            "status": "completed",
        },
    ]
    out = load_transactions_from_dicts(data)
    assert len(out) == 0


def test_load_from_file() -> None:
    payload = [
        {
            "transaction_id": "T1",
            "account_id": "A102",
            "transaction_amount": 100.0,
            "transaction_type": "payment",
            "timestamp": "2024-03-01 10:00:00",
            "status": "completed",
        },
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        path = f.name
    try:
        out = load_transactions_from_file(path)
        assert len(out) == 1
        assert out[0].account_id == "A102"
    finally:
        Path(path).unlink(missing_ok=True)


def test_load_from_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        load_transactions_from_file("/nonexistent/path.json")
