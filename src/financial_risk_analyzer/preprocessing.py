"""Parse and normalize transaction logs into structured records."""

import json
import logging
from pathlib import Path
from typing import Any

from financial_risk_analyzer.metrics import get_metrics
from financial_risk_analyzer.models import Transaction

logger = logging.getLogger(__name__)


def _parse_one(raw: dict[str, Any]) -> Transaction | None:
    """Parse a single raw record; return None if invalid (log and skip)."""
    try:
        amount = raw.get("transaction_amount")
        if amount is not None:
            amount = float(amount)
        else:
            logger.warning("Missing transaction_amount, skipping row: %s", raw)
            return None
        if amount < 0:
            logger.warning("Negative amount %s, skipping row: %s", amount, raw)
            return None
        return Transaction(
            transaction_id=str(raw.get("transaction_id", "")),
            account_id=str(raw.get("account_id", "")),
            transaction_amount=amount,
            transaction_type=str(raw.get("transaction_type", "")).strip() or "unknown",
            timestamp=str(raw.get("timestamp", "")),
            status=str(raw.get("status", "")).strip() or "unknown",
        )
    except (TypeError, ValueError) as e:
        logger.warning("Malformed row %s: %s", raw, e)
        return None


def load_transactions_from_dicts(data: list[dict[str, Any]]) -> list[Transaction]:
    """Convert a list of transaction dicts into structured Transaction objects."""
    out: list[Transaction] = []
    for raw in data:
        t = _parse_one(raw)
        if t is not None:
            out.append(t)
    metrics = get_metrics()
    metrics.transactions_loaded = len(out)
    metrics.transactions_skipped = len(data) - len(out)
    if metrics.transactions_skipped:
        logger.debug("Preprocessing: loaded=%s skipped=%s", len(out), metrics.transactions_skipped)
    return out


def load_transactions_from_file(path: str | Path) -> list[Transaction]:
    """Load transactions from a JSON file. Expects a list of transaction objects or dict with 'transactions' key."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise OSError(f"Cannot read file {path}: {e}") from e
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, list):
        data = data.get("transactions", data) if isinstance(data, dict) else [data]
    if not isinstance(data, list):
        data = [data]
    return load_transactions_from_dicts(data)
