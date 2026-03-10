# LLM-Powered Financial Risk Analyzer (synthetic data only)
FROM python:3.11-slim

WORKDIR /app

# Install package and runtime dependencies (no dev)
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/
RUN pip install --no-cache-dir -e . \
    && mkdir -p data && python scripts/generate_synthetic_data.py

# Default: run with bundled sample data, rule-based only (no API key required)
ENTRYPOINT ["financial-risk-analyzer"]
CMD ["data/sample_transactions.json", "--no-llm"]
