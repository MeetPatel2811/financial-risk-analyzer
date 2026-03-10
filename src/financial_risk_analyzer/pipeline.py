"""Orchestration: preprocess → summarize → LLM → validate → retry/fallback."""

import logging
from pathlib import Path

from financial_risk_analyzer.config import Settings
from financial_risk_analyzer.fallback import rule_based_risk
from financial_risk_analyzer.llm_analyzer import analyze_with_retry
from financial_risk_analyzer.metrics import get_metrics
from financial_risk_analyzer.models import RiskResult, Transaction
from financial_risk_analyzer.preprocessing import load_transactions_from_dicts, load_transactions_from_file
from financial_risk_analyzer.summarization import summarize_by_account

logger = logging.getLogger(__name__)


def run_pipeline(
    transactions: list[Transaction] | list[dict] | str | Path,
    settings: Settings,
    *,
    use_llm: bool = True,
) -> list[tuple[str, RiskResult]]:
    """
    Run the full pipeline.

    Args:
        transactions: List of Transaction, list of dicts, or path to JSON file.
        settings: Application settings (from Settings.from_env()).
        use_llm: If True and API key is set, use LLM; otherwise rule-based fallback only.

    Returns:
        List of (account_id, RiskResult) for each account in the input.
    """
    metrics = get_metrics()
    metrics.start_run()

    if isinstance(transactions, (str, Path)):
        path_str = str(transactions)
        logger.info("Loading transactions from file: %s", path_str)
        transactions = load_transactions_from_file(transactions)
    elif isinstance(transactions, list) and transactions and isinstance(transactions[0], dict):
        transactions = load_transactions_from_dicts(transactions)

    if not transactions:
        logger.warning("No transactions to analyze")
        metrics.end_run()
        return []

    summaries = summarize_by_account(transactions)
    by_account: dict[str, list[Transaction]] = {}
    for t in transactions:
        by_account.setdefault(t.account_id, []).append(t)
    logger.info("Summarized %s account(s) for analysis", len(summaries))

    results: list[tuple[str, RiskResult]] = []
    can_use_llm = use_llm and bool(settings.openai_api_key)
    if not can_use_llm:
        logger.info("Using rule-based fallback only (no LLM)")

    for account_id, summary in summaries.items():
        txs = by_account.get(account_id, [])
        if can_use_llm:
            risk_result, err = analyze_with_retry(summary, settings)
            if risk_result is not None:
                results.append((account_id, risk_result))
                logger.debug("Account %s: LLM analysis completed", account_id)
                continue
            metrics.fallbacks_used += 1
            logger.info("Fallback for account %s: %s", account_id, err)
        results.append((account_id, rule_based_risk(txs)))

    metrics.accounts_processed = len(results)
    metrics.accounts_flagged = sum(1 for _, r in results if r.risk_flag)
    metrics.end_run()
    logger.info("Pipeline complete: %s accounts processed, %s flagged", metrics.accounts_processed, metrics.accounts_flagged)
    return results


def run_pipeline_from_file(
    path: str | Path,
    settings: Settings | None = None,
    *,
    use_llm: bool = True,
) -> list[tuple[str, RiskResult]]:
    """Load from file and run pipeline. Uses Settings.from_env() if settings not provided."""
    if settings is None:
        settings = Settings.from_env()
    return run_pipeline(path, settings, use_llm=use_llm)
