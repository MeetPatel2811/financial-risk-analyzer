#!/usr/bin/env python3
"""Generate synthetic transaction JSON for testing and demos. No real bank data."""

import json
from datetime import datetime, timedelta
from pathlib import Path

# Scenario types for variety (used in docstrings / generation logic)
SCENARIOS = (
    "rapid_same_amount",   # 3+ same-amount transfers in minutes
    "mixed_status",        # same account, mixed completed/pending/failed
    "normal_activity",     # spaced-out, varied amounts
)


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generate_rapid_same_amount(account_id: str, base_time: datetime) -> list[dict]:
    """Multiple identical transfers in a short window (duplicate/automation risk)."""
    amount = 5000.0
    return [
        {
            "transaction_id": f"T-{account_id}-{i}",
            "account_id": account_id,
            "transaction_amount": amount,
            "transaction_type": "transfer",
            "timestamp": _ts(base_time + timedelta(minutes=i * 2)),
            "status": "completed",
        }
        for i in range(3)
    ]


def generate_mixed_status(account_id: str, base_time: datetime) -> list[dict]:
    """Same logical period, mixed statuses (inconsistent state risk)."""
    amount = 1000.0
    statuses = ["completed", "pending", "failed"]
    return [
        {
            "transaction_id": f"T-{account_id}-mixed-{i}",
            "account_id": account_id,
            "transaction_amount": amount,
            "transaction_type": "transfer",
            "timestamp": _ts(base_time + timedelta(minutes=i)),
            "status": statuses[i % 3],
        }
        for i in range(3)
    ]


def generate_normal_activity(account_id: str, base_time: datetime) -> list[dict]:
    """Spaced-out, varied amounts (low risk)."""
    amounts = [50.0, 120.0, 35.0]
    types = ["payment", "transfer", "payment"]
    return [
        {
            "transaction_id": f"T-{account_id}-norm-{i}",
            "account_id": account_id,
            "transaction_amount": amounts[i],
            "transaction_type": types[i],
            "timestamp": _ts(base_time + timedelta(hours=i * 2)),
            "status": "completed",
        }
        for i in range(3)
    ]


def generate_all() -> list[dict]:
    base = datetime(2024, 3, 1, 10, 0, 0)
    out: list[dict] = []
    out.extend(generate_rapid_same_amount("A102", base))
    out.extend(generate_mixed_status("A103", base))
    out.extend(generate_normal_activity("A104", base))
    return out


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "sample_transactions.json"
    records = generate_all()
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} synthetic transactions to {path}")


if __name__ == "__main__":
    main()
