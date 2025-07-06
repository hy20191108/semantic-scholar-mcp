"""Abstract base classes and interfaces for the Semantic Scholar MCP server.

This module defines the core abstractions that enable dependency injection,
testability, and extensibility throughout the application.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    Protocol,
    runtime_checkable,
)
from contextlib import asynccontextmanager
from dataclasses import dataclass

from pydantic import BaseModel

from .types import (
    PaginationParams,
    SortOrder,
    CacheKey,
    MetricName,
    SearchQuery,
)

# Type variables for generic interfaces
T = TypeVar("T", bound=BaseModel)
K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type
TEntity = TypeVar("TEntity", bound=BaseModel)
TID = TypeVar("TID", bound=Union[str, int])


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

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log error message with exception and context."""
        ...

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log critical message with exception and context."""
        ...

    @asynccontextmanager
    async def log_context(self, **kwargs: Any):
        """Context manager for adding context to all logs within the block."""
        yield


@runtime_checkable
class IMetricsCollector(Protocol):
    """Metrics collection interface for monitoring."""

    def increment(self, metric: MetricName, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        ...

    def gauge(self, metric: MetricName, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        ...

    def histogram(self, metric: MetricName, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a histogram metric."""
        ...

    @asynccontextmanager
    async def timer(self, metric: MetricName, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        yield


class IConfigurable(ABC):
    """Interface for configurable components."""

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the component with the given configuration."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate the configuration."""
        pass

    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the configuration."""
        pass


class IService(ABC):
    """Base interface for all services."""

    def __init__(self, logger: ILogger, metrics: IMetricsCollector) -> None:
        """Initialize service with logger and metrics collector."""
        self.logger = logger
        self.metrics = metrics

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service (e.g., establish connections)."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shutdown the service."""
        pass


@dataclass
class PagedResult(Generic[T]):
    """Generic paginated result container."""

    items: List[T]
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
    async def get_by_id(self, id: TID) -> Optional[TEntity]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_many(self, ids: List[TID]) -> List[TEntity]:
        """Get multiple entities by IDs."""
        pass

    @abstractmethod
    async def find(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[PaginationParams] = None,
        sort: Optional[SortOrder] = None,
    ) -> PagedResult[TEntity]:
        """Find entities with optional filtering, pagination, and sorting."""
        pass

    @abstractmethod
    async def create(self, entity: TEntity) -> TEntity:
        """Create a new entity."""
        pass

    @abstractmethod
    async def update(self, id: TID, entity: TEntity) -> Optional[TEntity]:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, id: TID) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    async def exists(self, id: TID) -> bool:
        """Check if entity exists."""
        pass

    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filtering."""
        pass


class ICacheable(ABC, Generic[K, V]):
    """Interface for cacheable components."""

    @abstractmethod
    async def get(self, key: K) -> Optional[V]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: K, value: V, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: K) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def exists(self, key: K) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def get_many(self, keys: List[K]) -> Dict[K, V]:
        """Get multiple values from cache."""
        pass

    @abstractmethod
    async def set_many(self, items: Dict[K, V], ttl: Optional[int] = None) -> None:
        """Set multiple values in cache."""
        pass


class ISearchable(ABC, Generic[T]):
    """Interface for searchable components."""

    @abstractmethod
    async def search(
        self,
        query: SearchQuery,
        pagination: Optional[PaginationParams] = None,
        sort: Optional[SortOrder] = None,
    ) -> PagedResult[T]:
        """Search for entities."""
        pass

    @abstractmethod
    async def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on prefix."""
        pass

    @abstractmethod
    async def index(self, entities: List[T]) -> None:
        """Index entities for searching."""
        pass

    @abstractmethod
    async def remove_from_index(self, ids: List[str]) -> None:
        """Remove entities from search index."""
        pass

    @abstractmethod
    async def reindex(self) -> None:
        """Rebuild the entire search index."""
        pass


class IEventPublisher(ABC):
    """Interface for event publishing."""

    @abstractmethod
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event."""
        pass

    @abstractmethod
    async def publish_batch(self, events: List[Dict[str, Any]]) -> None:
        """Publish multiple events."""
        pass


class IEventSubscriber(ABC):
    """Interface for event subscription."""

    @abstractmethod
    async def subscribe(self, event_type: str, handler: Any) -> None:
        """Subscribe to an event type."""
        pass

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: Any) -> None:
        """Unsubscribe from an event type."""
        pass


class ICircuitBreaker(ABC):
    """Interface for circuit breaker pattern."""

    @abstractmethod
    async def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection."""
        pass

    @abstractmethod
    def is_open(self) -> bool:
        """Check if circuit is open."""
        pass

    @abstractmethod
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset circuit breaker state."""
        pass


class IRateLimiter(ABC):
    """Interface for rate limiting."""

    @abstractmethod
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        pass

    @abstractmethod
    async def consume(self, key: str, tokens: int = 1) -> bool:
        """Consume tokens from rate limit bucket."""
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        pass

    @abstractmethod
    async def get_remaining(self, key: str) -> int:
        """Get remaining tokens for key."""
        pass


class IRetryStrategy(ABC):
    """Interface for retry strategies."""

    @abstractmethod
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if operation should be retried."""
        pass

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Get delay in seconds before next retry."""
        pass

    @abstractmethod
    def get_max_attempts(self) -> int:
        """Get maximum number of retry attempts."""
        pass


class IValidator(ABC, Generic[T]):
    """Interface for validation."""

    @abstractmethod
    def validate(self, data: T) -> bool:
        """Validate data."""
        pass

    @abstractmethod
    def get_errors(self, data: T) -> List[str]:
        """Get validation errors."""
        pass


class ISerializer(ABC, Generic[T]):
    """Interface for serialization."""

    @abstractmethod
    def serialize(self, obj: T) -> str:
        """Serialize object to string."""
        pass

    @abstractmethod
    def deserialize(self, data: str, target_type: Type[T]) -> T:
        """Deserialize string to object."""
        pass


class IFactory(ABC, Generic[T]):
    """Interface for factory pattern."""

    @abstractmethod
    def create(self, **kwargs: Any) -> T:
        """Create instance of type T."""
        pass

    @abstractmethod
    def register(self, key: str, creator: Any) -> None:
        """Register a creator function."""
        pass