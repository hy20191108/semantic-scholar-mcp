"""Enterprise-grade Semantic Scholar API client with resilience patterns."""

import asyncio
import random
import time
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

import httpx

from core.config import SemanticScholarConfig
from core.exceptions import (
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)
from core.logging import RequestContext, get_logger, log_performance
from core.protocols import (
    ICache,
    ILogger,
    IMetricsCollector,
)
from core.types import (
    AUTHOR_FIELDS,
    BASIC_PAPER_FIELDS,
    CITATION_FIELDS,
    DETAILED_PAPER_FIELDS,
    AuthorId,
    Fields,
    PaperId,
)

from .base_models import PaginatedResponse
from .domain_models import Author, Citation, Paper, Reference, SearchQuery

T = TypeVar("T")


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception_types: list[type[Exception]] | None = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception_types = expected_exception_types or [
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            NetworkError
        ]

        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._state = CircuitBreakerState.CLOSED
        self._half_open_attempts = 0

    @property
    def state(self) -> CircuitBreakerState:
        """Get current state."""
        if self._state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if (
                self._last_failure_time and
                (datetime.utcnow() - self._last_failure_time).total_seconds() > self.recovery_timeout
            ):
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_attempts = 0

        return self._state

    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            raise ServiceUnavailableError(
                "Circuit breaker is open",
                service_name="SemanticScholar",
                retry_after=int(self.recovery_timeout)
            )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if any(isinstance(e, exc_type) for exc_type in self.expected_exception_types):
                self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_attempts += 1
            if self._half_open_attempts >= 3:  # Successful attempts to close
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()

        if self._failure_count >= self.failure_threshold or self._state == CircuitBreakerState.HALF_OPEN:
            self._state = CircuitBreakerState.OPEN

    def reset(self):
        """Reset circuit breaker."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitBreakerState.CLOSED
        self._half_open_attempts = 0


class TokenBucketRateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # Tokens per second
        self.burst = burst  # Maximum burst size
        self._tokens = float(burst)
        self._last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from bucket."""
        async with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            self._last_update = now

            # Add new tokens
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    async def wait_if_needed(self, tokens: int = 1) -> None:
        """Wait if rate limit would be exceeded."""
        while not await self.acquire(tokens):
            wait_time = (tokens - self._tokens) / self.rate
            await asyncio.sleep(wait_time)

    @property
    def available_tokens(self) -> int:
        """Get available tokens."""
        now = time.time()
        elapsed = now - self._last_update
        return int(min(self.burst, self._tokens + elapsed * self.rate))


class ExponentialBackoffRetryStrategy:
    """Exponential backoff with jitter retry strategy."""

    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter (±25%)
            delay = delay * (0.75 + random.random() * 0.5)

        return delay


class SemanticScholarClient:
    """Enterprise-grade Semantic Scholar API client."""

    def __init__(
        self,
        config: SemanticScholarConfig,
        logger: ILogger | None = None,
        cache: ICache | None = None,
        metrics: IMetricsCollector | None = None
    ):
        self.config = config
        self.logger = logger or get_logger(__name__)
        self.cache = cache
        self.metrics = metrics

        # Initialize resilience components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker.failure_threshold if hasattr(config, 'circuit_breaker') else 5,
            recovery_timeout=config.circuit_breaker.recovery_timeout if hasattr(config, 'circuit_breaker') else 60.0
        )

        self.rate_limiter = TokenBucketRateLimiter(
            rate=config.rate_limit.requests_per_second if hasattr(config, 'rate_limit') else 1.0,
            burst=config.rate_limit.burst_size if hasattr(config, 'rate_limit') else 10
        )

        self.retry_strategy = ExponentialBackoffRetryStrategy(
            initial_delay=config.retry.initial_delay if hasattr(config, 'retry') else 1.0,
            max_delay=config.retry.max_delay if hasattr(config, 'retry') else 60.0,
            exponential_base=config.retry.exponential_base if hasattr(config, 'retry') else 2.0,
            jitter=config.retry.jitter if hasattr(config, 'retry') else True
        )

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Enter async context."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._build_headers(),
            timeout=self.config.timeout,
            limits=httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_keepalive_connections
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._client:
            await self._client.aclose()

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": f"{self.config.server.name}/{self.config.server.version}" if hasattr(self.config, 'server') else "semantic-scholar-mcp/0.1.0",
            "Accept": "application/json",
        }

        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key.get_secret_value()

        return headers

    @log_performance(log_args=False, log_result=False)
    async def _make_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry_count: int = 0
    ) -> dict[str, Any]:
        """Make HTTP request with resilience patterns."""
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        # Rate limiting
        await self.rate_limiter.wait_if_needed()

        # Build request context
        request_id = f"{method}:{path}:{time.time()}"

        async def _execute_request():
            """Execute the actual request."""
            with RequestContext(request_id=request_id):
                self.logger.debug(
                    f"Making request to {path}",
                    method=method,
                    params=params,
                    retry_attempt=retry_count
                )

                try:
                    response = await self._client.request(
                        method=method,
                        url=path,
                        params=params,
                        json=json
                    )

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", "60"))
                        raise RateLimitError(
                            "Rate limit exceeded",
                            retry_after=retry_after,
                            limit=response.headers.get("X-RateLimit-Limit"),
                            remaining=response.headers.get("X-RateLimit-Remaining")
                        )

                    # Handle not found
                    if response.status_code == 404:
                        raise NotFoundError(
                            "Resource not found",
                            resource_type="API endpoint",
                            resource_id=path
                        )

                    # Handle server errors
                    if response.status_code >= 500:
                        raise ServiceUnavailableError(
                            f"Server error: {response.status_code}",
                            service_name="SemanticScholar"
                        )

                    response.raise_for_status()

                    data = response.json()

                    # Metrics
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "success"}
                        )

                    return data

                except httpx.TimeoutException as e:
                    self.logger.error(
                        "Request timeout",
                        url=str(e.request.url) if e.request else None,
                        timeout=self.config.timeout
                    )
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "timeout"}
                        )
                    raise NetworkError(
                        "Request timed out",
                        url=path,
                        timeout=self.config.timeout
                    )

                except httpx.NetworkError as e:
                    self.logger.error(
                        "Network error",
                        exception=e
                    )
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "network_error"}
                        )
                    raise NetworkError(
                        "Network error occurred",
                        url=path
                    )

        # Execute with circuit breaker
        try:
            return await self.circuit_breaker.call(_execute_request)
        except (RateLimitError, ServiceUnavailableError, NetworkError) as e:
            # Retry with exponential backoff
            if retry_count < self.config.retry.max_attempts if hasattr(self.config, 'retry') else 3:
                delay = self.retry_strategy.get_delay(retry_count + 1)
                self.logger.warning(
                    f"Retrying request after {delay:.2f}s",
                    retry_count=retry_count + 1,
                    error=str(e)
                )
                await asyncio.sleep(delay)
                return await self._make_request(
                    method, path, params, json, retry_count + 1
                )
            raise

    async def search_papers(
        self,
        query: SearchQuery,
        fields: Fields | None = None
    ) -> PaginatedResponse[Paper]:
        """Search for papers with advanced query support."""
        # Validate query
        if not query.query.strip():
            raise ValidationError("Search query cannot be empty", field="query")

        # Use cache if available
        cache_key = f"search:{query.query}:{query.offset}:{query.limit}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                self.logger.debug("Cache hit for search", query=query.query)
                return cached

        # Prepare request
        fields = fields or self.config.default_fields
        params = {
            "query": query.query,
            "fields": ",".join(fields),
            "limit": query.limit,
            "offset": query.offset
        }

        if query.sort:
            params["sort"] = query.sort

        # Apply filters
        if query.filters:
            if query.filters.year:
                params["year"] = str(query.filters.year)
            if query.filters.fields_of_study:
                params["fieldsOfStudy"] = ",".join(query.filters.fields_of_study)

        # Make request
        data = await self._make_request("GET", "/paper/search", params=params)

        # Parse response
        papers = [Paper(**paper_data) for paper_data in data.get("data", [])]
        response = PaginatedResponse[Paper](
            items=papers,
            total=data.get("total", 0),
            offset=query.offset,
            limit=query.limit
        )

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, response, ttl=300)  # 5 minutes

        return response

    async def get_paper(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        include_citations: bool = False,
        include_references: bool = False
    ) -> Paper:
        """Get paper details with optional citations and references."""
        # Validate paper ID
        if not paper_id:
            raise ValidationError("Paper ID cannot be empty", field="paper_id")

        # Use cache
        cache_key = f"paper:{paper_id}"
        if self.cache and not (include_citations or include_references):
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Prepare request
        fields = fields or DETAILED_PAPER_FIELDS
        params = {"fields": ",".join(fields)}

        # Make request
        data = await self._make_request("GET", f"/paper/{paper_id}", params=params)

        # Create paper object
        paper = Paper(**data)

        # Fetch additional data if requested
        if include_citations:
            citations = await self.get_paper_citations(paper_id)
            paper.citations = citations

        if include_references:
            references = await self.get_paper_references(paper_id)
            paper.references = references

        # Cache result
        if self.cache and not (include_citations or include_references):
            await self.cache.set(cache_key, paper, ttl=3600)  # 1 hour

        return paper

    async def get_paper_citations(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        offset: int = 0,
        limit: int = 100
    ) -> list[Citation]:
        """Get citations for a paper."""
        fields = fields or CITATION_FIELDS
        params = {
            "fields": ",".join(fields),
            "offset": offset,
            "limit": limit
        }

        data = await self._make_request(
            "GET",
            f"/paper/{paper_id}/citations",
            params=params
        )

        return [Citation(**cite) for cite in data.get("data", [])]

    async def get_paper_references(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        offset: int = 0,
        limit: int = 100
    ) -> list[Reference]:
        """Get references for a paper."""
        fields = fields or CITATION_FIELDS
        params = {
            "fields": ",".join(fields),
            "offset": offset,
            "limit": limit
        }

        data = await self._make_request(
            "GET",
            f"/paper/{paper_id}/references",
            params=params
        )

        return [Reference(**ref) for ref in data.get("data", [])]

    async def batch_get_papers(
        self,
        paper_ids: list[PaperId],
        fields: Fields | None = None
    ) -> list[Paper]:
        """Get multiple papers in a single request."""
        if not paper_ids:
            return []

        if len(paper_ids) > 500:
            raise ValidationError(
                "Too many paper IDs",
                field="paper_ids",
                value=len(paper_ids)
            )

        fields = fields or BASIC_PAPER_FIELDS

        # Ensure fields is iterable
        if isinstance(fields, str):
            fields = [fields]

        # Batch request
        data = await self._make_request(
            "POST",
            "/paper/batch",
            json={"ids": paper_ids},
            params={"fields": ",".join(fields)} if fields else {}
        )

        return [Paper(**paper_data) for paper_data in data if paper_data]

    async def get_author(
        self,
        author_id: AuthorId,
        fields: Fields | None = None
    ) -> Author:
        """Get author details."""
        # Validate author ID
        if not author_id:
            raise ValidationError("Author ID cannot be empty", field="author_id")

        # Use cache
        cache_key = f"author:{author_id}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Prepare request
        fields = fields or AUTHOR_FIELDS
        params = {"fields": ",".join(fields)}

        # Make request
        data = await self._make_request("GET", f"/author/{author_id}", params=params)

        # Create author object
        author = Author(**data)

        # Cache result
        if self.cache:
            await self.cache.set(cache_key, author, ttl=3600)  # 1 hour

        return author

    async def get_author_papers(
        self,
        author_id: AuthorId,
        fields: Fields | None = None,
        offset: int = 0,
        limit: int = 100
    ) -> PaginatedResponse[Paper]:
        """Get papers by an author."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {
            "fields": ",".join(fields),
            "offset": offset,
            "limit": limit
        }

        data = await self._make_request(
            "GET",
            f"/author/{author_id}/papers",
            params=params
        )

        papers = [Paper(**paper_data) for paper_data in data.get("data", [])]

        return PaginatedResponse[Paper](
            items=papers,
            total=data.get("total", 0),
            offset=offset,
            limit=limit
        )

    async def search_authors(
        self,
        query: str,
        fields: Fields | None = None,
        offset: int = 0,
        limit: int = 10
    ) -> PaginatedResponse[Author]:
        """Search for authors."""
        if not query.strip():
            raise ValidationError("Search query cannot be empty", field="query")

        fields = fields or AUTHOR_FIELDS
        params = {
            "query": query,
            "fields": ",".join(fields),
            "offset": offset,
            "limit": limit
        }

        data = await self._make_request("GET", "/author/search", params=params)

        authors = [Author(**author_data) for author_data in data.get("data", [])]

        return PaginatedResponse[Author](
            items=authors,
            total=data.get("total", 0),
            offset=offset,
            limit=limit
        )

    async def get_recommendations(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        limit: int = 10
    ) -> list[Paper]:
        """Get paper recommendations based on a paper."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {
            "fields": ",".join(fields),
            "limit": limit
        }

        data = await self._make_request(
            "GET",
            f"/recommendations/v1/papers/forpaper/{paper_id}",
            params=params
        )

        return [Paper(**paper_data) for paper_data in data.get("recommendedPapers", [])]

    def get_circuit_breaker_state(self) -> str:
        """Get current circuit breaker state."""
        return self.circuit_breaker.state.value

    def get_rate_limiter_status(self) -> dict[str, Any]:
        """Get rate limiter status."""
        return {
            "available_tokens": self.rate_limiter.available_tokens,
            "rate": self.rate_limiter.rate,
            "burst": self.rate_limiter.burst
        }

    async def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        try:
            # Try a simple search
            await self.search_papers(
                SearchQuery(query="test", limit=1)
            )

            return {
                "status": "healthy",
                "circuit_breaker": self.get_circuit_breaker_state(),
                "rate_limiter": self.get_rate_limiter_status(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker": self.get_circuit_breaker_state(),
                "rate_limiter": self.get_rate_limiter_status(),
                "timestamp": datetime.utcnow().isoformat()
            }
