"""Abstract base classes and interfaces for the Semantic Scholar MCP server.

This module defines the core abstractions that enable dependency injection,
testability, and extensibility throughout the application.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from pydantic import BaseModel

from .types import (
    MetricName,
    PaginationParams,
    SearchQuery,
    SortOrder,
)

# Type variables for generic interfaces
T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type
TEntity = TypeVar("TEntity", bound=BaseModel)
TID = TypeVar("TID", bound=str | int)


@runtime_checkable
class ILogger(Protocol):
    """Logger interface for structured logging."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        ...

    def error(
        self, message: str, exception: Exception | None = None, **kwargs: Any
    ) -> None:
        """Log error message with exception and context."""
        ...

    def critical(
        self, message: str, exception: Exception | None = None, **kwargs: Any
    ) -> None:
        """Log critical message with exception and context."""
        ...

    @asynccontextmanager
    async def log_context(self, **_kwargs: Any):
        """Context manager for adding context to all logs within the block."""
        yield


@runtime_checkable
class IMetricsCollector(Protocol):
    """Metrics collection interface for monitoring."""

    def increment(
        self, metric: MetricName, value: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric."""
        ...

    def gauge(
        self, metric: MetricName, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric."""
        ...

    def histogram(
        self, metric: MetricName, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a histogram metric."""
        ...

    @asynccontextmanager
    async def timer(self, _metric: MetricName, _tags: dict[str, str] | None = None):
        """Context manager for timing operations."""
        yield


class IConfigurable(ABC):
    """Interface for configurable components."""

    @abstractmethod
    def configure(self, config: dict[str, Any]) -> None:
        """Configure the component with the given configuration."""

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate the configuration."""

    @abstractmethod
    def get_config_schema(self) -> dict[str, Any]:
        """Get the JSON schema for the configuration."""


class IService(ABC):
    """Base interface for all services."""

    def __init__(self, logger: ILogger, metrics: IMetricsCollector) -> None:
        """Initialize service with logger and metrics collector."""
        self.logger = logger
        self.metrics = metrics

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform health check and return status."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service (e.g., establish connections)."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""


@dataclass
class PagedResult(Generic[T]):
    """Generic paginated result container."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size


class IRepository(ABC, Generic[TEntity, TID]):
    """Generic repository interface following the Repository pattern."""

    def __init__(self, logger: ILogger, metrics: IMetricsCollector) -> None:
        """Initialize repository with logger and metrics collector."""
        self.logger = logger
        self.metrics = metrics

    @abstractmethod
    async def get_by_id(self, entity_id: TID) -> TEntity | None:
        """Get entity by ID."""

    @abstractmethod
    async def get_many(self, ids: list[TID]) -> list[TEntity]:
        """Get multiple entities by IDs."""

    @abstractmethod
    async def find(
        self,
        filters: dict[str, Any] | None = None,
        pagination: PaginationParams | None = None,
        sort: SortOrder | None = None,
    ) -> PagedResult[TEntity]:
        """Find entities with optional filtering, pagination, and sorting."""

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity:
        """Create a new entity."""

    @abstractmethod
    async def update(self, entity_id: TID, entity: TEntity) -> TEntity | None:
        """Update an existing entity."""

    @abstractmethod
    async def delete(self, entity_id: TID) -> bool:
        """Delete an entity by ID."""

    @abstractmethod
    async def exists(self, entity_id: TID) -> bool:
        """Check if entity exists."""

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count entities with optional filtering."""


class ICacheable(ABC, Generic[K, V]):
    """Interface for cacheable components."""

    @abstractmethod
    async def get(self, key: K) -> V | None:
        """Get value from cache."""

    @abstractmethod
    async def set(self, key: K, value: V, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL in seconds."""

    @abstractmethod
    async def delete(self, key: K) -> bool:
        """Delete value from cache."""

    @abstractmethod
    async def exists(self, key: K) -> bool:
        """Check if key exists in cache."""

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""

    @abstractmethod
    async def get_many(self, keys: list[K]) -> dict[K, V]:
        """Get multiple values from cache."""

    @abstractmethod
    async def set_many(self, items: dict[K, V], ttl: int | None = None) -> None:
        """Set multiple values in cache."""


class ISearchable(ABC, Generic[T]):
    """Interface for searchable components."""

    @abstractmethod
    async def search(
        self,
        query: SearchQuery,
        pagination: PaginationParams | None = None,
        sort: SortOrder | None = None,
    ) -> PagedResult[T]:
        """Search for entities."""

    @abstractmethod
    async def suggest(self, prefix: str, limit: int = 10) -> list[str]:
        """Get search suggestions based on prefix."""

    @abstractmethod
    async def index(self, entities: list[T]) -> None:
        """Index entities for searching."""

    @abstractmethod
    async def remove_from_index(self, ids: list[str]) -> None:
        """Remove entities from search index."""

    @abstractmethod
    async def reindex(self) -> None:
        """Rebuild the entire search index."""


class IEventPublisher(ABC):
    """Interface for event publishing."""

    @abstractmethod
    async def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event."""

    @abstractmethod
    async def publish_batch(self, events: list[dict[str, Any]]) -> None:
        """Publish multiple events."""


class IEventSubscriber(ABC):
    """Interface for event subscription."""

    @abstractmethod
    async def subscribe(self, event_type: str, handler: Any) -> None:
        """Subscribe to an event type."""

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: Any) -> None:
        """Unsubscribe from an event type."""


class ICircuitBreaker(ABC):
    """Interface for circuit breaker pattern."""

    @abstractmethod
    async def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection."""

    @abstractmethod
    def is_open(self) -> bool:
        """Check if circuit is open."""

    @abstractmethod
    def is_closed(self) -> bool:
        """Check if circuit is closed."""

    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker state."""


class IRateLimiter(ABC):
    """Interface for rate limiting."""

    @abstractmethod
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""

    @abstractmethod
    async def consume(self, key: str, tokens: int = 1) -> bool:
        """Consume tokens from rate limit bucket."""

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for key."""

    @abstractmethod
    async def get_remaining(self, key: str) -> int:
        """Get remaining tokens for key."""


class IRetryStrategy(ABC):
    """Interface for retry strategies."""

    @abstractmethod
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if operation should be retried."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds before next retry."""

    @abstractmethod
    def get_max_attempts(self) -> int:
        """Get maximum number of retry attempts."""


class IValidator(ABC, Generic[T]):
    """Interface for validation."""

    @abstractmethod
    def validate(self, data: T) -> bool:
        """Validate data."""

    @abstractmethod
    def get_errors(self, data: T) -> list[str]:
        """Get validation errors."""


class ISerializer(ABC, Generic[T]):
    """Interface for serialization."""

    @abstractmethod
    def serialize(self, obj: T) -> str:
        """Serialize object to string."""

    @abstractmethod
    def deserialize(self, data: str, target_type: type[T]) -> T:
        """Deserialize string to object."""


class IFactory(ABC, Generic[T]):
    """Interface for factory pattern."""

    @abstractmethod
    def create(self, **kwargs: Any) -> T:
        """Create instance of type T."""

    @abstractmethod
    def register(self, key: str, creator: Any) -> None:
        """Register a creator function."""
