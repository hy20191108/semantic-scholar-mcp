"""Core package containing protocols, exceptions, and type definitions."""

from .protocols import (
    IRepository,
    ILogger,
    IMetricsCollector,
    ICache,
    IHealthCheckable,
    IConfigurable,
)
from .exceptions import (
    SemanticScholarMCPError,
    APIError,
    ValidationError,
    ConfigurationError,
    RateLimitError,
    NetworkError,
    CacheError,
    NotFoundError,
    UnauthorizedError,
    ServiceUnavailableError,
)
from .types import (
    PaperId,
    AuthorId,
    Fields,
    SearchResult,
    PaperDetails,
    AuthorDetails,
)

__all__ = [
    # Protocols
    "IRepository",
    "ILogger",
    "IMetricsCollector",
    "ICache",
    "IHealthCheckable",
    "IConfigurable",
    # Exceptions
    "SemanticScholarMCPError",
    "APIError",
    "ValidationError",
    "ConfigurationError",
    "RateLimitError",
    "NetworkError",
    "CacheError",
    "NotFoundError",
    "UnauthorizedError",
    "ServiceUnavailableError",
    # Types
    "PaperId",
    "AuthorId",
    "Fields",
    "SearchResult",
    "PaperDetails",
    "AuthorDetails",
]