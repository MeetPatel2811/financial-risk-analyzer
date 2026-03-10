"""Rule-based anomaly detection fallback when LLM validation fails.

Output shape matches RiskResult so downstream (alerts, review queue) is unchanged.
"""

from collections import defaultdict
from datetime import datetime
from typing import DefaultDict

from financial_risk_analyzer.models import RiskResult, Transaction

# Thresholds (tunable)
MIN_TRANSACTIONS_FOR_FREQUENCY = 3
MAX_MINUTES_FOR_ABNORMAL_FREQUENCY = 60
MIN_SAME_AMOUNT_REPEAT = 2
MIN_TRANSACTIONS_MIXED_STATUS = 2
MINUTES_DUPLICATE_WINDOW = 60


def _minutes_span(transactions: list[Transaction]) -> float:
    """Return time span in minutes between first and last transaction. 0.0 if fewer than 2 txs or parse error."""
    if len(transactions) < 2:
        return 0.0
    try:
        ts = sorted(t.timestamp for t in transactions)
        t1 = datetime.fromisoformat(ts[0].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(ts[-1].replace("Z", "+00:00"))
        return abs((t2 - t1).total_seconds()) / 60.0
    except (ValueError, TypeError):
        return 0.0


def rule_based_risk(transactions: list[Transaction]) -> RiskResult:
    """
    Apply rule-based anomaly detection. Same output shape as LLM RiskResult
    so downstream (alerts, review queue) is unchanged.
    """
    if not transactions:
        return RiskResult(
            risk_flag=False,
            risk_type=None,
            confidence=0.0,
            explanation="No transactions to analyze.",
        )

    account_id = transactions[0].account_id
    n = len(transactions)
    amounts = [t.transaction_amount for t in transactions]
    statuses = [t.status for t in transactions]
    window_min = _minutes_span(transactions)

    # Same amount repeated in short window -> possible duplicate
    amount_counts: DefaultDict[float, int] = defaultdict(int)
    for a in amounts:
        amount_counts[round(a, 2)] += 1
    max_same = max(amount_counts.values()) if amount_counts else 0

    if max_same >= MIN_SAME_AMOUNT_REPEAT and n >= MIN_SAME_AMOUNT_REPEAT and window_min < MINUTES_DUPLICATE_WINDOW:
        return RiskResult(
            risk_flag=True,
            risk_type="possible_duplicate_transactions",
            confidence=0.75,
            explanation=f"Account {account_id}: {max_same} transactions of same amount within {window_min:.0f} minutes.",
        )

    # High count in short time -> abnormal frequency
    if n >= MIN_TRANSACTIONS_FOR_FREQUENCY and window_min > 0 and window_min < MAX_MINUTES_FOR_ABNORMAL_FREQUENCY:
        return RiskResult(
            risk_flag=True,
            risk_type="abnormal_transaction_frequency",
            confidence=0.7,
            explanation=f"Account {account_id}: {n} transactions within {window_min:.0f} minutes.",
        )

    # Mixed statuses -> inconsistent state
    unique_statuses = set(s.strip() for s in statuses if s)
    if len(unique_statuses) >= 2 and n >= MIN_TRANSACTIONS_MIXED_STATUS:
        return RiskResult(
            risk_flag=True,
            risk_type="inconsistent_transaction_states",
            confidence=0.65,
            explanation=f"Account {account_id}: mixed statuses {sorted(unique_statuses)}.",
        )

    return RiskResult(
        risk_flag=False,
        risk_type=None,
        confidence=0.5,
        explanation=f"Account {account_id}: no rule-based risk pattern detected ({n} transactions).",
    )
