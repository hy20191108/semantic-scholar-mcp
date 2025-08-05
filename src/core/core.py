"""Core infrastructure: cache, factories, and service management.

This module consolidates cache implementation and factory functions
for service creation, replacing the complex DI container with simple
factory functions that create properly configured service instances.
"""

import asyncio
from collections import OrderedDict
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar

from .config import get_config
from .interfaces import ICache
from .logging import get_logger
from .metrics_collector import MetricsCollector

T = TypeVar("T")


class InMemoryCache(ICache[str, Any]):
    """Simple in-memory LRU cache implementation."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            if key not in self._cache:
                return None

            value, expiry = self._cache[key]

            # Check if expired
            if datetime.now(timezone.utc) > expiry:
                del self._cache[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        async with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._cache.popitem(last=False)

            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()

    async def size(self) -> int:
        """Get cache size."""
        async with self._lock:
            return len(self._cache)

    async def contains(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self._lock:
            if key not in self._cache:
                return False

            _, expiry = self._cache[key]
            # Check if expired
            if datetime.now(timezone.utc) > expiry:
                del self._cache[key]
                return False

            return True

    def make_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments.

        Uses simple string concatenation for better performance than hashing.
        Format: arg1:arg2:...:key1=val1:key2=val2:...
        """
        parts = [str(arg) for arg in args]
        parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(parts)


# Factory functions for service creation


def create_cache() -> InMemoryCache:
    """Create configured cache instance."""
    config = get_config()
    return InMemoryCache(
        max_size=config.cache.max_size,
        default_ttl=config.cache.default_ttl,
    )


def create_metrics_collector() -> MetricsCollector:
    """Create metrics collector instance."""
    config = get_config()
    return MetricsCollector(max_history=1000, enabled=config.metrics.enabled)


def create_logger(name: str) -> Any:
    """Create logger instance."""
    return get_logger(name)


# Simple service registry
_services: dict[type, Callable[[], Any]] = {
    InMemoryCache: create_cache,
    MetricsCollector: create_metrics_collector,
}


def register_factory(service_type: type[T], factory: Callable[[], T]) -> None:
    """Register a factory function for a service type."""
    _services[service_type] = factory


def get_service(service_type: type[T]) -> T:
    """Get service instance from factory."""
    factory = _services.get(service_type)
    if not factory:
        raise ValueError(f"Service {service_type.__name__} not registered")
    return factory()


def create_api_client():
    """Create configured API client.

    Note: Import moved inside function to avoid circular dependency.
    """
    from ..semantic_scholar_mcp.api_client import SemanticScholarClient

    config = get_config()
    return SemanticScholarClient(
        api_key=config.semantic_scholar.api_key,
        base_url=config.semantic_scholar.base_url,
        timeout=config.semantic_scholar.timeout,
        max_retries=config.retry.max_attempts,
        backoff_factor=config.retry.backoff_factor,
        cache=get_service(InMemoryCache),
        metrics_collector=get_service(MetricsCollector),
    )


# Register API client factory after defining it
def _register_api_client():
    """Register API client factory."""
    try:
        from ..semantic_scholar_mcp.api_client import SemanticScholarClient

        register_factory(SemanticScholarClient, create_api_client)
    except ImportError:
        # API client not available during some tests
        pass


# Initialize factories
_register_api_client()
