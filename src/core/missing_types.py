"""Additional type definitions for completeness."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass
class PaginationParams:
    """Pagination parameters."""
    offset: int = 0
    limit: int = 10


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class MetricName(str, Enum):
    """Metric names for monitoring."""
    API_REQUEST_COUNT = "api.request.count"
    API_REQUEST_DURATION = "api.request.duration"
    API_REQUEST_ERROR = "api.request.error"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"


@dataclass
class SearchQuery:
    """Search query parameters."""
    query: str
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None
