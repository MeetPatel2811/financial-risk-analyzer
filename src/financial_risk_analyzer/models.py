"""Data models for transactions and risk results."""

from typing import Any

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """A single synthetic transaction record."""

    transaction_id: str
    account_id: str
    transaction_amount: float = Field(ge=0, description="Non-negative amount")
    transaction_type: str
    timestamp: str
    status: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """Build from a raw dict (e.g. from JSON)."""
        return cls(
            transaction_id=str(data.get("transaction_id", "")),
            account_id=str(data.get("account_id", "")),
            transaction_amount=float(data.get("transaction_amount", 0)),
            transaction_type=str(data.get("transaction_type", "")),
            timestamp=str(data.get("timestamp", "")),
            status=str(data.get("status", "")),
        )


class RiskResult(BaseModel):
    """Structured risk analysis result (LLM or fallback output)."""

    risk_flag: bool
    risk_type: str | None = None
    confidence: float = Field(ge=0, le=1)
    explanation: str
