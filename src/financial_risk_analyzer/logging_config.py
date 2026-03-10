"""Structured logging configuration. Single place for format and handler setup."""

import logging
import sys
from typing import Any

# Log format with timestamp, level, logger name, and message. No secrets or PII in format.
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure(
    level: str | int = logging.INFO,
    format_string: str | None = None,
    stream: Any = None,
    *,
    force: bool = False,
) -> None:
    """
    Configure root logger. Idempotent unless force=True.

    Args:
        level: Log level name or constant (e.g. "INFO", logging.INFO).
        format_string: Format for log records; default includes timestamp, level, name, message.
        stream: Where to send logs (default sys.stderr).
        force: If True, re-add handler and overwrite format (e.g. for tests).
    """
    root = logging.getLogger()
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    fmt = format_string or DEFAULT_FORMAT
    if stream is None:
        stream = sys.stderr

    if force and root.handlers:
        for h in root.handlers[:]:
            root.removeHandler(h)

    if not root.handlers:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter(fmt, datefmt=DATE_FORMAT))
        root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name. Use __name__ in modules."""
    return logging.getLogger(name)


def log_with_extra(
    logger: logging.Logger,
    level: int,
    message: str,
    *args: Any,
    **extra: Any,
) -> None:
    """Log message at level with optional extra key-value context (e.g. account_id, duration_sec)."""
    if extra:
        # Standard logging supports extra= for custom keys if a Formatter is set up for them
        logger.log(level, message, *args, extra=extra)
    else:
        logger.log(level, message, *args)
