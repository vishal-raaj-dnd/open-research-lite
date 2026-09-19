"""Centralized exception hierarchy for open-research-lite.

Provides structured, typed exceptions for production error handling and observability.
"""

from typing import Optional


class OpenResearchError(Exception):
    """Base exception for all open-research-lite runtime errors."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(OpenResearchError):
    """Raised when configuration, API keys, or provider parameters are invalid."""
    pass


class SearchProviderError(OpenResearchError):
    """Raised when web search APIs (Tavily, DuckDuckGo, or custom) fail or time out."""
    pass


class FactExtractionError(OpenResearchError):
    """Raised when fact extraction fails, returns malformed structures, or violates rate limits."""
    pass


class ReportSynthesisError(OpenResearchError):
    """Raised when report writing / LLM synthesis fails or times out."""
    pass


class KnowledgeGraphError(OpenResearchError):
    """Raised when graph operations encounter structural or constraint errors."""
    pass
