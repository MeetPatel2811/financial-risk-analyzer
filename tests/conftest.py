"""Pytest configuration and shared fixtures."""

import os

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "llm: mark test as requiring real OpenAI API (set OPENAI_API_KEY or RUN_LLM_TESTS=1 to run)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip 'llm' tests unless OPENAI_API_KEY is set or RUN_LLM_TESTS=1."""
    run_llm = os.environ.get("RUN_LLM_TESTS", "").strip() in ("1", "true", "yes")
    has_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if run_llm or has_key:
        return
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Set OPENAI_API_KEY or RUN_LLM_TESTS=1 to run LLM tests"))
