"""Simple cache implementation for the MCP server."""

import asyncio
import hashlib
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, TypeVar

from .protocols import ICache

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
            if datetime.utcnow() > expiry:
                del self._cache[key]
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        expiry = datetime.utcnow() + timedelta(seconds=ttl)

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

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        async with self._lock:
            if key not in self._cache:
                return False

            _, expiry = self._cache[key]
            if datetime.utcnow() > expiry:
                del self._cache[key]
                return False

            return True

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()

    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]
        for key in expired_keys:
            del self._cache[key]


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    # Create a string representation of args and kwargs
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)

    # Hash for consistent length
    return hashlib.md5(key_string.encode()).hexdigest()
