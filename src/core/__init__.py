"""Core package containing protocols, exceptions, and type definitions."""

from .exceptions import (
    APIError,
    CacheError,
    ConfigurationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    SemanticScholarMCPError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from .interfaces import (
    ICache,
    ICircuitBreaker,
    ILogger,
    IMetricsCollector,
    IRateLimiter,
    IRepository,
    IRetryable,
    IValidator,
)
from .types import (
    AuthorDetails,
    AuthorId,
    Fields,
    PaperDetails,
    PaperId,
    SearchResult,
)

__all__ = [
    # Exceptions
    "APIError",
    # Types
    "AuthorDetails",
    "AuthorId",
    "CacheError",
    "ConfigurationError",
    "Fields",
    # Protocols
    "ICache",
    "ICircuitBreaker",
    "ILogger",
    "IMetricsCollector",
    "IRateLimiter",
    "IRepository",
    "IRetryable",
    "IValidator",
    "NetworkError",
    "NotFoundError",
    "PaperDetails",
    "PaperId",
    "RateLimitError",
    "SearchResult",
    "SemanticScholarMCPError",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "ValidationError",
]
