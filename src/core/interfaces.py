"""Essential interfaces for the semantic scholar MCP server.

This module contains only the essential interfaces needed for the application,
replacing the 110+ protocols from abstractions.py and protocols.py.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class ILogger(ABC):
    """Logger interface."""

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""


class IMetricsCollector(ABC):
    """Metrics collection interface."""

    @abstractmethod
    def increment(
        self, name: str, value: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        """Increment counter metric."""

    @abstractmethod
    def gauge(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Set gauge metric."""

    @abstractmethod
    def histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record histogram metric."""


class ICache(Generic[K, V], ABC):
    """Cache interface."""

    @abstractmethod
    def get(self, key: K) -> V | None:
        """Get value from cache."""

    @abstractmethod
    def set(self, key: K, value: V, ttl: int | None = None) -> None:
        """Set value in cache."""

    @abstractmethod
    def delete(self, key: K) -> None:
        """Delete value from cache."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries."""


class IValidator(Generic[T], ABC):
    """Validator interface."""

    @abstractmethod
    def validate(self, data: T) -> bool:
        """Validate data."""

    @abstractmethod
    def get_errors(self) -> list[str]:
        """Get validation errors."""


class IRateLimiter(ABC):
    """Rate limiter interface."""

    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""

    @abstractmethod
    def get_remaining(self, key: str) -> int:
        """Get remaining requests."""

    @abstractmethod
    def get_reset_time(self, key: str) -> float:
        """Get reset time."""


class ICircuitBreaker(ABC):
    """Circuit breaker interface."""

    @abstractmethod
    def call(self, func: callable, *args: Any, **kwargs: Any) -> Any:
        """Call function through circuit breaker."""

    @abstractmethod
    def is_open(self) -> bool:
        """Check if circuit is open."""

    @abstractmethod
    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""


class IRetryable(ABC):
    """Retryable operation interface."""

    @abstractmethod
    async def retry(self, func: callable, *args: Any, **kwargs: Any) -> Any:
        """Retry function call."""

    @abstractmethod
    def should_retry(self, exception: Exception) -> bool:
        """Check if should retry on exception."""


class IRepository(Generic[T], ABC):
    """Repository interface for data access."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Get entity by ID."""

    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> list[T]:
        """List entities."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create entity."""

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update entity."""

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity."""
