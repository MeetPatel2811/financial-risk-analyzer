"""CLI entrypoint for the risk analyzer. Run from project root for default paths."""

import argparse
import json
import logging
import sys
from pathlib import Path

from financial_risk_analyzer.config import Settings
from financial_risk_analyzer.exceptions import LoadError
from financial_risk_analyzer.metrics import get_metrics
from financial_risk_analyzer.pipeline import run_pipeline_from_file

logger = logging.getLogger(__name__)
EXIT_SUCCESS = 0
EXIT_INPUT_ERROR = 1


def main() -> None:
    """Run the risk analyzer CLI. Exits process with 0 on success, 1 on error."""
    parser = argparse.ArgumentParser(
        description="LLM-powered financial operations risk analyzer (synthetic data only)",
        epilog="Run from project root so default path data/sample_transactions.json resolves.",
    )
    parser.add_argument(
        "input",
        type=Path,
        default=Path("data/sample_transactions.json"),
        nargs="?",
        help="Path to JSON file with transaction records",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Write results to JSON file (default: print to stdout)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Use rule-based fallback only (no API calls)",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    settings.configure_logging()

    if not args.input.exists():
        logger.error("Input file not found: %s", args.input)
        sys.exit(EXIT_INPUT_ERROR)

    if not settings.openai_api_key and not args.no_llm:
        logger.warning("OPENAI_API_KEY not set; using rule-based fallback only.")

    get_metrics().reset()
    use_llm = not args.no_llm and bool(settings.openai_api_key)
    try:
        results = run_pipeline_from_file(args.input, settings, use_llm=use_llm)
    except LoadError as e:
        logger.error("Load failed: %s", e)
        sys.exit(EXIT_INPUT_ERROR)
    except (FileNotFoundError, ValueError, OSError, TypeError) as e:
        logger.error("Pipeline failed: %s", e)
        sys.exit(EXIT_INPUT_ERROR)

    out = [
        {
            "account_id": account_id,
            "risk_flag": r.risk_flag,
            "risk_type": r.risk_type,
            "confidence": r.confidence,
            "explanation": r.explanation,
        }
        for account_id, r in results
    ]

    if args.output:
        try:
            args.output.write_text(json.dumps(out, indent=2), encoding="utf-8")
            logger.info("Wrote results to %s", args.output)
        except OSError as e:
            logger.error("Cannot write output file %s: %s", args.output, e)
            sys.exit(EXIT_INPUT_ERROR)
    else:
        try:
            print(json.dumps(out, indent=2))
        except (TypeError, ValueError) as e:
            logger.error("Failed to serialize results: %s", e)
            sys.exit(EXIT_INPUT_ERROR)

    flagged = sum(1 for _, r in results if r.risk_flag)
    if flagged:
        logger.info("%d account(s) flagged for review.", flagged)
    get_metrics().log_summary()
    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()
