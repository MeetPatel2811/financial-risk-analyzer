"""Configuration loaded from environment variables."""

import logging
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = "gpt-4"
DEFAULT_MAX_RETRIES = 3
DEFAULT_LOG_LEVEL = "INFO"
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


@dataclass(frozen=True)
class Settings:
    """Application settings from environment. Immutable after creation."""

    openai_api_key: str
    openai_model: str
    max_retries: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment. Uses safe defaults for invalid values."""
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        try:
            max_retries = int(os.environ.get("MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
            max_retries = max(1, min(max_retries, 10))
        except (TypeError, ValueError):
            max_retries = DEFAULT_MAX_RETRIES
        raw_level = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
        log_level = raw_level if raw_level in VALID_LOG_LEVELS else DEFAULT_LOG_LEVEL
        return cls(
            openai_api_key=key,
            openai_model=model,
            max_retries=max_retries,
            log_level=log_level,
        )

    def configure_logging(self) -> None:
        """Configure root logger with structured format. Idempotent; safe to call once at startup."""
        from financial_risk_analyzer.logging_config import configure as configure_logging
        level = getattr(logging, self.log_level, logging.INFO)
        configure_logging(level=level)
