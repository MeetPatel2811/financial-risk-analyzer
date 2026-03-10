"""Build human-readable summaries from transaction lists for LLM input."""

from collections import defaultdict
from datetime import datetime
from typing import DefaultDict

from financial_risk_analyzer.models import Transaction


def _minutes_between(ts1: str, ts2: str) -> float:
    """Approximate minutes between two ISO-like timestamps (naive parse). Returns 0.0 on parse error."""
    try:
        t1 = datetime.fromisoformat(ts1.replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
        delta = abs((t2 - t1).total_seconds())
        return delta / 60.0
    except (ValueError, TypeError):
        return 0.0


def _format_amount(amount: float) -> str:
    return f"${amount:,.2f}"


def summarize_transactions(transactions: list[Transaction]) -> str:
    """
    Produce a single human-readable summary for a batch of transactions.
    Uses fixed template for consistent, deterministic-style prompts.
    """
    if not transactions:
        return "No transactions to summarize."

    account_id = transactions[0].account_id
    count = len(transactions)
    amounts = [t.transaction_amount for t in transactions]
    min_amt = min(amounts)
    max_amt = max(amounts)
    types = [t.transaction_type for t in transactions]
    type_counts: DefaultDict[str, int] = defaultdict(int)
    for ty in types:
        type_counts[ty] += 1
    type_desc = ", ".join(f"{k}: {v}" for k, v in sorted(type_counts.items()))

    # Time window
    sorted_ts = sorted(t.timestamp for t in transactions)
    time_window_min = 0.0
    if len(sorted_ts) >= 2:
        time_window_min = _minutes_between(sorted_ts[0], sorted_ts[-1])

    # Same-amount repeats (possible duplicate pattern)
    amount_counts: DefaultDict[float, int] = defaultdict(int)
    for a in amounts:
        amount_counts[round(a, 2)] += 1
    max_same = max(amount_counts.values()) if amount_counts else 0
    same_amount_note = ""
    if max_same >= 2:
        same_amount_note = f" Same amount repeated {max_same} times."

    # Status consistency
    statuses = [t.status for t in transactions]
    unique_statuses = set(statuses)
    inconsistent_note = ""
    if len(unique_statuses) > 1:
        inconsistent_note = " Mixed statuses: " + ", ".join(sorted(unique_statuses)) + "."

    # Frequency note
    frequency_note = ""
    if count >= 3 and time_window_min > 0 and time_window_min < 60:
        frequency_note = " This pattern is significantly higher than typical transaction frequency."

    summary = (
        f"Account {account_id} performed {count} transaction(s) "
        f"(types: {type_desc}). "
        f"Amount range: {_format_amount(min_amt)} to {_format_amount(max_amt)}. "
        f"Time window: {time_window_min:.1f} minutes."
        f"{same_amount_note}{inconsistent_note}{frequency_note}"
    )
    return summary.strip()


def summarize_by_account(transactions: list[Transaction]) -> dict[str, str]:
    """Group transactions by account_id and return one summary per account."""
    by_account: DefaultDict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        by_account[t.account_id].append(t)
    return {aid: summarize_transactions(txs) for aid, txs in by_account.items()}
