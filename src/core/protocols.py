"""Protocol definitions for dependency injection and abstraction."""

from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T")
TModel = TypeVar("TModel")
TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


@runtime_checkable
class IDisposable(Protocol):
    """Protocol for disposable resources."""

    async def dispose(self) -> None:
        """Dispose of resources."""
        ...


@runtime_checkable
class ILogger(Protocol):
    """Protocol for logging services."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(self, message: str, exception: Exception | None = None, **kwargs: Any) -> None:
        """Log error message."""
        ...

    def with_context(self, **context: Any) -> "ILogger":
        """Create logger with additional context."""
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """Protocol for metrics collection."""

    def increment(self, metric: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        ...

    def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge metric."""
        ...

    def histogram(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram value."""
        ...

    async def flush(self) -> None:
        """Flush pending metrics."""
        ...


@runtime_checkable
class ICache(Protocol, Generic[TKey, TValue]):
    """Protocol for caching services."""

    async def get(self, key: TKey) -> TValue | None:
        """Get value from cache."""
        ...

    async def set(self, key: TKey, value: TValue, ttl: int | None = None) -> None:
        """Set value in cache."""
        ...

    async def delete(self, key: TKey) -> bool:
        """Delete value from cache."""
        ...

    async def exists(self, key: TKey) -> bool:
        """Check if key exists."""
        ...

    async def clear(self) -> None:
        """Clear all cache entries."""
        ...


@runtime_checkable
class IHealthCheckable(Protocol):
    """Protocol for health checkable services."""

    async def check_health(self) -> dict[str, Any]:
        """Check service health."""
        ...


@runtime_checkable
class IConfigurable(Protocol, Generic[T]):
    """Protocol for configurable services."""

    def configure(self, config: T) -> None:
        """Configure the service."""
        ...

    def get_config(self) -> T:
        """Get current configuration."""
        ...


@runtime_checkable
class IRetryable(Protocol):
    """Protocol for retryable operations."""

    async def execute_with_retry(
        self,
        operation: Any,
        max_attempts: int = 3,
        backoff_factor: float = 2.0
    ) -> Any:
        """Execute operation with retry logic."""
        ...


@runtime_checkable
class IRateLimiter(Protocol):
    """Protocol for rate limiting."""

    async def acquire(self, key: str, cost: int = 1) -> bool:
        """Acquire rate limit token."""
        ...

    async def wait_if_needed(self, key: str, cost: int = 1) -> None:
        """Wait if rate limit is exceeded."""
        ...

    def get_remaining(self, key: str) -> int:
        """Get remaining tokens."""
        ...


@runtime_checkable
class ICircuitBreaker(Protocol):
    """Protocol for circuit breaker pattern."""

    async def call(self, operation: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute operation through circuit breaker."""
        ...

    def get_state(self) -> str:
        """Get circuit breaker state."""
        ...

    def reset(self) -> None:
        """Reset circuit breaker."""
        ...


@runtime_checkable
class IRepository(Protocol, Generic[T, TKey]):
    """Protocol for repository pattern."""

    async def get_by_id(self, id: TKey) -> T | None:
        """Get entity by ID."""
        ...

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination."""
        ...

    async def create(self, entity: T) -> T:
        """Create new entity."""
        ...

    async def update(self, entity: T) -> T:
        """Update existing entity."""
        ...

    async def delete(self, id: TKey) -> bool:
        """Delete entity by ID."""
        ...

    async def exists(self, id: TKey) -> bool:
        """Check if entity exists."""
        ...


@runtime_checkable
class IUnitOfWork(Protocol):
    """Protocol for unit of work pattern."""

    async def __aenter__(self) -> "IUnitOfWork":
        """Enter unit of work context."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit unit of work context."""
        ...

    async def commit(self) -> None:
        """Commit changes."""
        ...

    async def rollback(self) -> None:
        """Rollback changes."""
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """Protocol for event publishing."""

    async def publish(self, event_name: str, data: Any) -> None:
        """Publish an event."""
        ...

    def subscribe(self, event_name: str, handler: Any) -> None:
        """Subscribe to an event."""
        ...

    def unsubscribe(self, event_name: str, handler: Any) -> None:
        """Unsubscribe from an event."""
        ...


@runtime_checkable
class IValidator(Protocol, Generic[T]):
    """Protocol for validation services."""

    def validate(self, value: T) -> list[str]:
        """Validate value and return errors."""
        ...

    def is_valid(self, value: T) -> bool:
        """Check if value is valid."""
        ...


@runtime_checkable
class ISerializer(Protocol, Generic[T]):
    """Protocol for serialization services."""

    def serialize(self, obj: T) -> str:
        """Serialize object to string."""
        ...

    def deserialize(self, data: str, type_hint: type[T]) -> T:
        """Deserialize string to object."""
        ...
