"""Custom exceptions for the risk analyzer. Use these for clearer error handling and logging."""


class FinancialRiskAnalyzerError(Exception):
    """Base exception for this package. Catch this to handle any analyzer-specific error."""

    pass


class ConfigurationError(FinancialRiskAnalyzerError):
    """Raised when configuration is invalid or missing required values."""

    pass


class LoadError(FinancialRiskAnalyzerError):
    """Raised when transaction data cannot be loaded (file missing, invalid JSON, bad format)."""

    pass
