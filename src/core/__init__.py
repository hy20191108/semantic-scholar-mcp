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
from .protocols import (
    ICache,
    IConfigurable,
    IHealthCheckable,
    ILogger,
    IMetricsCollector,
    IRepository,
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
    "IConfigurable",
    "IHealthCheckable",
    "ILogger",
    "IMetricsCollector",
    "IRepository",
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
