# LLM-Powered Financial Operations Risk Analyzer

A research project that uses large language models to help identify potential risk patterns in **synthetic** financial transaction logs. All data is simulated; no real bank or customer data is used.

## Architecture

```
Transaction Logs (synthetic)
    → Data Preprocessing
    → Feature Summarization
    → LLM Risk Analysis (GPT-4)
    → Validation Layer
    → Risk Flags (or Rule-based Fallback)
```

- **Preprocessing**: Parses and normalizes transaction records; skips malformed rows.
- **Summarization**: Builds human-readable summaries per account (frequency, amounts, time window, same-amount repeats, status consistency).
- **LLM**: Sends summaries to the OpenAI API with a structured prompt; expects JSON with `risk_flag`, `risk_type`, `confidence`, `explanation`.
- **Validation**: Ensures valid JSON and required fields; triggers retry or fallback on failure.
- **Retry**: Up to `MAX_RETRIES` with a stricter prompt if validation fails.
- **Fallback**: Rule-based anomaly detection (duplicate-like patterns, abnormal frequency, mixed statuses) when the LLM is unavailable or validation fails after retries.

Guardrails: validation, retries, fallback, and human review of flags are central to the design.

## Setup

1. **Clone or create project directory** and enter it.

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   ```

3. **Install dependencies** (from project root):
   ```bash
   pip install -e ".[dev]"
   ```
   Or only runtime: `pip install -e .`  
   Alternatively: `pip install -r requirements.txt` (then run as `python -m financial_risk_analyzer` from project root).

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```
   Set `OPENAI_API_KEY` in `.env`. Optional: `OPENAI_MODEL`, `MAX_RETRIES`, `LOG_LEVEL`.

## Logging and metrics

- **Logging**: Structured format with timestamp, level, logger name, and message. Level is controlled by `LOG_LEVEL` (default `INFO`; use `DEBUG` for verbose). No secrets or PII are logged.
- **Metrics**: Each run records counters (transactions loaded/skipped, accounts processed, LLM calls, retries, validation failures, fallbacks used, accounts flagged) and timers (pipeline duration, LLM call duration). A metrics summary is logged at the end of each CLI run. Use `get_metrics()` and `metrics.to_dict()` in code to export or integrate with monitoring.

## Generating synthetic data

Generate sample transaction JSON (rapid same-amount transfers, mixed statuses, normal activity):

```bash
python3 scripts/generate_synthetic_data.py
```

This writes `data/sample_transactions.json`.

## Running the pipeline

**Run from the project root** so that default path `data/sample_transactions.json` resolves.

- **With LLM** (requires `OPENAI_API_KEY`):
  ```bash
  python -m financial_risk_analyzer data/sample_transactions.json
  ```
  Or after `pip install -e .`:
  ```bash
  financial-risk-analyzer data/sample_transactions.json
  ```

- **Rule-based fallback only** (no API calls):
  ```bash
  python -m financial_risk_analyzer data/sample_transactions.json --no-llm
  ```

- **Write results to a file**:
  ```bash
  python -m financial_risk_analyzer data/sample_transactions.json -o results.json
  ```

## Example output

Example risk flag for an account with multiple high-value transfers in a short window:

```json
{
  "account_id": "A102",
  "risk_flag": true,
  "risk_type": "abnormal_transaction_frequency",
  "confidence": 0.86,
  "explanation": "Multiple high-value transfers occurred within a short time window."
}
```

Accounts with no detected risk will have `risk_flag: false` and an explanation. All results are intended for human review.

## Tests

```bash
pytest
```

Tests use mocked OpenAI client where applicable; no real API calls in CI.

## Project structure

```
financial-risk-analyzer/
├── pyproject.toml
├── README.md
├── .env.example
├── src/financial_risk_analyzer/
│   ├── config.py
│   ├── models.py
│   ├── preprocessing.py
│   ├── summarization.py
│   ├── llm_analyzer.py
│   ├── validation.py
│   ├── fallback.py
│   ├── pipeline.py
│   └── cli.py
├── tests/
├── data/
│   └── sample_transactions.json
└── scripts/
    └── generate_synthetic_data.py
```

## License

MIT.
