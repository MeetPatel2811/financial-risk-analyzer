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

## Docker

Build and run with Docker (no local Python needed):

```bash
# Build
docker build -t financial-risk-analyzer .

# Run with bundled sample data, rule-based only (no API key)
docker run --rm financial-risk-analyzer

# Run with LLM (pass your API key)
docker run --rm -e OPENAI_API_KEY=your_key financial-risk-analyzer data/sample_transactions.json

# Run on your own file (mount it)
docker run --rm -v /path/to/your/transactions.json:/data/input.json financial-risk-analyzer /data/input.json --no-llm

# Write results out of the container
docker run --rm -v $(pwd)/out:/out financial-risk-analyzer data/sample_transactions.json -o /out/results.json --no-llm
```

The image includes generated sample data in `data/sample_transactions.json`. Use `-e OPENAI_API_KEY` for LLM mode or omit it for rule-based only.

With Docker Compose (loads `OPENAI_API_KEY` from `.env`):

```bash
docker compose run --rm analyzer
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

- **Unit tests** use a mocked OpenAI client (no API key needed).
- **LLM integration tests** call the real OpenAI API. Run them with an API key set:
  ```bash
  OPENAI_API_KEY=your_key pytest -m llm -v
  ```
  or set `RUN_LLM_TESTS=1` and `OPENAI_API_KEY` in the environment.

**CI (GitHub Actions):** The workflow runs unit tests on every push/PR. On push to `main`, it also runs LLM integration tests when the repository has an `OPENAI_API_KEY` secret configured (Settings → Secrets and variables → Actions). Add that secret to enable real API calls in CI.

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
