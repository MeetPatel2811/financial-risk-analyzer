"""Lightweight run metrics: counters and timers for pipeline observability."""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    """
    In-memory metrics for a single pipeline run. Call reset() at start of run.
    Thread-unsafe; intended for single-threaded CLI use.
    """

    # Counters
    transactions_loaded: int = 0
    transactions_skipped: int = 0
    accounts_processed: int = 0
    llm_calls_total: int = 0
    llm_retries_total: int = 0
    llm_validation_failures: int = 0
    fallbacks_used: int = 0
    accounts_flagged: int = 0

    # Timers (seconds)
    pipeline_start_time: float | None = field(default=None, repr=False)
    pipeline_duration_sec: float = 0.0
    llm_calls_duration_sec: float = 0.0

    def reset(self) -> "Metrics":
        """Reset all counters and timers for a new run. Returns self for chaining."""
        self.transactions_loaded = 0
        self.transactions_skipped = 0
        self.accounts_processed = 0
        self.llm_calls_total = 0
        self.llm_retries_total = 0
        self.llm_validation_failures = 0
        self.fallbacks_used = 0
        self.accounts_flagged = 0
        self.pipeline_start_time = None
        self.pipeline_duration_sec = 0.0
        self.llm_calls_duration_sec = 0.0
        return self

    def start_run(self) -> None:
        """Mark pipeline run start (for duration)."""
        self.pipeline_start_time = time.perf_counter()

    def end_run(self) -> None:
        """Mark pipeline run end and compute duration."""
        if self.pipeline_start_time is not None:
            self.pipeline_duration_sec = time.perf_counter() - self.pipeline_start_time
            self.pipeline_start_time = None

    def to_dict(self) -> dict[str, Any]:
        """Return metrics as a dict for logging or export."""
        return {
            "transactions_loaded": self.transactions_loaded,
            "transactions_skipped": self.transactions_skipped,
            "accounts_processed": self.accounts_processed,
            "llm_calls_total": self.llm_calls_total,
            "llm_retries_total": self.llm_retries_total,
            "llm_validation_failures": self.llm_validation_failures,
            "fallbacks_used": self.fallbacks_used,
            "accounts_flagged": self.accounts_flagged,
            "pipeline_duration_sec": round(self.pipeline_duration_sec, 3),
            "llm_calls_duration_sec": round(self.llm_calls_duration_sec, 3),
        }

    def log_summary(self) -> None:
        """Log metrics summary at INFO level."""
        d = self.to_dict()
        logger.info(
            "Metrics: transactions_loaded=%s transactions_skipped=%s accounts_processed=%s "
            "llm_calls=%s llm_retries=%s llm_validation_failures=%s fallbacks=%s accounts_flagged=%s "
            "pipeline_duration_sec=%s llm_calls_duration_sec=%s",
            d["transactions_loaded"],
            d["transactions_skipped"],
            d["accounts_processed"],
            d["llm_calls_total"],
            d["llm_retries_total"],
            d["llm_validation_failures"],
            d["fallbacks_used"],
            d["accounts_flagged"],
            d["pipeline_duration_sec"],
            d["llm_calls_duration_sec"],
        )


# Module-level singleton for the current run; reset at start of each CLI run.
_metrics = Metrics()


def get_metrics() -> Metrics:
    """Return the global metrics instance for the current run."""
    return _metrics
