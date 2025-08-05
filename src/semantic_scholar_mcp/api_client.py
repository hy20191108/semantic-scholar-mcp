"""Enterprise-grade Semantic Scholar API client with resilience patterns."""

import asyncio
import random
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypeVar

import httpx

from core.config import SemanticScholarConfig
from core.exceptions import (
    CircuitBreakerError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)
from core.interfaces import (
    ICache,
    ILogger,
    IMetricsCollector,
)
from core.logging import (
    RequestContext,
    get_logger,
    log_performance,
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

from .models import Author, Citation, PaginatedResponse, Paper, Reference, SearchQuery

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
        expected_exception_types: list[type[Exception]] | None = None,
        logger: ILogger | None = None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception_types = expected_exception_types or [
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            NetworkError,
        ]
        self.logger = logger or get_logger("circuit_breaker")

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
                self._last_failure_time
                and (
                    datetime.now(timezone.utc) - self._last_failure_time
                ).total_seconds()
                > self.recovery_timeout
            ):
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_attempts = 0
                self.logger.log_circuit_breaker_state(
                    "half_open",
                    recovery_timeout=self.recovery_timeout,
                    failure_count=self._failure_count,
                )

        return self._state

    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == CircuitBreakerState.OPEN:
            error = CircuitBreakerError(
                "Circuit breaker is open",
                failure_count=self._failure_count,
                failure_threshold=self.failure_threshold,
                reset_timeout=self.recovery_timeout,
            )

            # Log circuit breaker error with context
            self.logger.log_error_with_context(
                error,
                context={
                    "circuit_breaker_state": self.state.value,
                    "failure_count": self._failure_count,
                    "failure_threshold": self.failure_threshold,
                    "recovery_timeout": self.recovery_timeout,
                    "last_failure_time": self._last_failure_time.isoformat()
                    if self._last_failure_time
                    else None,
                },
                recovery_actions=["wait_for_reset", "manual_reset"],
            )

            raise error

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            if any(
                isinstance(e, exc_type) for exc_type in self.expected_exception_types
            ):
                self._on_failure()

                # Log circuit breaker failure
                self.logger.log_error_with_context(
                    e,
                    context={
                        "circuit_breaker_failure": True,
                        "failure_count": self._failure_count,
                        "circuit_breaker_state": self.state.value,
                    },
                    recovery_actions=["retry", "circuit_breaker_open"],
                )

            raise

    def _on_success(self):
        """Handle successful call."""
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_attempts += 1
            if self._half_open_attempts >= 3:  # Successful attempts to close
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                self.logger.log_circuit_breaker_state(
                    "closed",
                    half_open_attempts=self._half_open_attempts,
                    reason="recovery_successful",
                )
        else:
            self._failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        previous_state = self._state
        self._failure_count += 1
        self._last_failure_time = datetime.now(timezone.utc)

        if (
            self._failure_count >= self.failure_threshold
            or self._state == CircuitBreakerState.HALF_OPEN
        ):
            self._state = CircuitBreakerState.OPEN
            if previous_state != CircuitBreakerState.OPEN:
                self.logger.log_circuit_breaker_state(
                    "open",
                    failure_count=self._failure_count,
                    failure_threshold=self.failure_threshold,
                    recovery_timeout=self.recovery_timeout,
                    reason="failure_threshold_exceeded"
                    if self._failure_count >= self.failure_threshold
                    else "half_open_failure",
                )

    def reset(self):
        """Reset circuit breaker."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitBreakerState.CLOSED
        self._half_open_attempts = 0


class TokenBucketRateLimiter:
    """Token bucket rate limiter implementation."""

    def __init__(self, rate: float, burst: int, logger: ILogger | None = None):
        self.rate = rate  # Tokens per second
        self.burst = burst  # Maximum burst size
        self._tokens = float(burst)
        self._last_update = time.time()
        self._lock = asyncio.Lock()
        self.logger = logger or get_logger("rate_limiter")

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

            # Log rate limit warning
            self.logger.log_resource_usage(
                resource_type="rate_limit_tokens",
                current_usage=self.burst - self._tokens,
                limit=self.burst,
                unit="tokens",
                wait_time_seconds=wait_time,
                requested_tokens=tokens,
                rate_per_second=self.rate,
            )

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
        jitter: bool = True,
    ):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay,
        )

        if self.jitter:
            # Add random jitter (±25%)
            delay = delay * (0.75 + random.random() * 0.5)

        return delay


class SemanticScholarClient:
    """Enterprise-grade Semantic Scholar API client."""

    # API endpoints
    GRAPH_URL = "https://api.semanticscholar.org/graph/v1"
    RECOMMENDATIONS_URL = "https://api.semanticscholar.org/recommendations/v1"
    DATASETS_URL = "https://api.semanticscholar.org/datasets/v1"

    def __init__(
        self,
        config: SemanticScholarConfig,
        logger: ILogger | None = None,
        cache: ICache | None = None,
        metrics: IMetricsCollector | None = None,
    ):
        self.config = config
        self.logger = logger or get_logger(__name__)
        self.cache = cache
        self.metrics = metrics

        # Initialize resilience components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=getattr(
                getattr(config, "circuit_breaker", None), "failure_threshold", 5
            ),
            recovery_timeout=getattr(
                getattr(config, "circuit_breaker", None), "recovery_timeout", 60.0
            ),
            logger=self.logger.with_context(component="circuit_breaker"),
        )

        self.rate_limiter = TokenBucketRateLimiter(
            rate=config.rate_limit.requests_per_second
            if hasattr(config, "rate_limit")
            else 1.0,
            burst=config.rate_limit.burst_size if hasattr(config, "rate_limit") else 10,
            logger=self.logger.with_context(component="rate_limiter"),
        )

        self.retry_strategy = ExponentialBackoffRetryStrategy(
            initial_delay=config.retry.initial_delay
            if hasattr(config, "retry")
            else 1.0,
            max_delay=config.retry.max_delay if hasattr(config, "retry") else 60.0,
            exponential_base=config.retry.exponential_base
            if hasattr(config, "retry")
            else 2.0,
            jitter=config.retry.jitter if hasattr(config, "retry") else True,
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
                max_keepalive_connections=self.config.max_keepalive_connections,
            ),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._client:
            await self._client.aclose()

    def _build_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": f"{self.config.server.name}/{self.config.server.version}"
            if hasattr(self.config, "server")
            else "semantic-scholar-mcp/0.1.0",
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
        retry_count: int = 0,
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
            start_time = time.time()

            with RequestContext(request_id=request_id):
                # Determine base URL based on path
                if path.startswith("/recommendations"):
                    base_url = self.RECOMMENDATIONS_URL
                    actual_path = path.replace("/recommendations/v1", "")
                elif path.startswith("/datasets"):
                    base_url = self.DATASETS_URL
                    actual_path = path.replace("/datasets/v1", "")
                else:
                    base_url = self.GRAPH_URL
                    actual_path = path

                full_url = f"{base_url}{actual_path}"

                # Log request details
                self.logger.log_api_request(
                    method=method,
                    url=full_url,
                    params=params,
                    retry_attempt=retry_count,
                    rate_limit_tokens=self.rate_limiter.available_tokens,
                )

                try:
                    response = await self._client.request(
                        method=method, url=full_url, params=params, json=json
                    )

                    response_time = time.time() - start_time

                    # Log response details
                    self.logger.log_api_response(
                        status_code=response.status_code,
                        response_time=response_time,
                        retry_attempt=retry_count,
                        content_length=len(response.content) if response.content else 0,
                    )

                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", "60"))
                        raise RateLimitError(
                            "Rate limit exceeded",
                            retry_after=retry_after,
                            limit=response.headers.get("X-RateLimit-Limit"),
                            remaining=response.headers.get("X-RateLimit-Remaining"),
                        )

                    # Handle not found
                    if response.status_code == 404:
                        raise NotFoundError(
                            "Resource not found",
                            resource_type="API endpoint",
                            resource_id=path,
                        )

                    # Handle server errors
                    if response.status_code >= 500:
                        raise ServiceUnavailableError(
                            f"Server error: {response.status_code}",
                            service_name="SemanticScholar",
                        )

                    response.raise_for_status()

                    data = response.json()

                    # Metrics
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "success"},
                        )

                    return data

                except httpx.TimeoutException as e:
                    self.logger.error(
                        "Request timeout",
                        url=str(e.request.url) if e.request else None,
                        timeout=self.config.timeout,
                    )
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "timeout"},
                        )
                    raise NetworkError(
                        "Request timed out", url=path, timeout=self.config.timeout
                    )

                except httpx.NetworkError as e:
                    self.logger.error("Network error", exception=e)
                    if self.metrics:
                        self.metrics.increment(
                            "api_requests_total",
                            tags={"method": method, "status": "network_error"},
                        )
                    raise NetworkError("Network error occurred", url=path)

        # Execute with circuit breaker
        try:
            return await self.circuit_breaker.call(_execute_request)
        except (RateLimitError, ServiceUnavailableError, NetworkError) as e:
            # Retry with exponential backoff
            max_attempts = (
                self.config.retry.max_attempts if hasattr(self.config, "retry") else 3
            )
            if retry_count < max_attempts:
                delay = self.retry_strategy.get_delay(retry_count + 1)
                self.logger.debug_mcp(
                    f"Retrying request after {delay:.2f}s",
                    retry_attempt=retry_count + 1,
                    max_attempts=max_attempts,
                    delay_seconds=delay,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    method=method,
                    path=path,
                    exponential_base=self.retry_strategy.exponential_base,
                    max_delay=self.retry_strategy.max_delay,
                )
                await asyncio.sleep(delay)
                return await self._make_request(
                    method, path, params, json, retry_count + 1
                )
            raise

    async def search_papers(
        self, query: SearchQuery, fields: Fields | None = None
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
            "offset": query.offset,
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
            limit=query.limit,
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
        include_references: bool = False,
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
        limit: int = 100,
    ) -> list[Citation]:
        """Get citations for a paper."""
        fields = fields or CITATION_FIELDS
        params = {"fields": ",".join(fields), "offset": offset, "limit": limit}

        data = await self._make_request(
            "GET", f"/paper/{paper_id}/citations", params=params
        )

        return [Citation(**cite) for cite in data.get("data", [])]

    async def get_paper_references(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Reference]:
        """Get references for a paper."""
        fields = fields or CITATION_FIELDS
        params = {"fields": ",".join(fields), "offset": offset, "limit": limit}

        data = await self._make_request(
            "GET", f"/paper/{paper_id}/references", params=params
        )

        return [Reference(**ref) for ref in data.get("data", [])]

    async def get_paper_authors(
        self,
        paper_id: PaperId,
        fields: Fields | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> PaginatedResponse[Author]:
        """Get paper authors with pagination support."""
        fields = fields or AUTHOR_FIELDS
        params = {
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset,
        }

        data = await self._make_request(
            "GET", f"/paper/{paper_id}/authors", params=params
        )

        authors = [Author(**author_data) for author_data in data.get("data", [])]

        return PaginatedResponse[Author](
            items=authors,
            total=data.get("total", 0),
            offset=offset,
            limit=limit,
        )

    async def batch_get_papers(
        self, paper_ids: list[PaperId], fields: Fields | None = None
    ) -> list[Paper]:
        """Get multiple papers in a single request with improved response handling."""
        if not paper_ids:
            return []

        if len(paper_ids) > 500:
            raise ValidationError(
                "Too many paper IDs", field="paper_ids", value=len(paper_ids)
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
            params={"fields": ",".join(fields)} if fields else {},
        )

        # Handle response format variations
        papers = []
        if isinstance(data, dict) and "data" in data:
            paper_list = data["data"]
        elif isinstance(data, list):
            paper_list = data
        else:
            paper_list = []

        # Parse papers, handling None values and validation errors
        for paper_data in paper_list:
            if paper_data:  # Skip None entries
                try:
                    papers.append(Paper(**paper_data))
                except Exception as e:
                    self.logger.warning(
                        "Failed to parse paper data in batch",
                        paper_data=paper_data,
                        error=str(e),
                    )
                    continue

        return papers

    async def get_author(
        self, author_id: AuthorId, fields: Fields | None = None
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
        limit: int = 100,
    ) -> PaginatedResponse[Paper]:
        """Get papers by an author."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {"fields": ",".join(fields), "offset": offset, "limit": limit}

        data = await self._make_request(
            "GET", f"/author/{author_id}/papers", params=params
        )

        papers = [Paper(**paper_data) for paper_data in data.get("data", [])]

        return PaginatedResponse[Paper](
            items=papers, total=data.get("total", 0), offset=offset, limit=limit
        )

    async def search_authors(
        self, query: str, fields: Fields | None = None, offset: int = 0, limit: int = 10
    ) -> PaginatedResponse[Author]:
        """Search for authors."""
        if not query.strip():
            raise ValidationError("Search query cannot be empty", field="query")

        fields = fields or AUTHOR_FIELDS
        params = {
            "query": query,
            "fields": ",".join(fields),
            "offset": offset,
            "limit": limit,
        }

        data = await self._make_request("GET", "/author/search", params=params)

        authors = [Author(**author_data) for author_data in data.get("data", [])]

        return PaginatedResponse[Author](
            items=authors, total=data.get("total", 0), offset=offset, limit=limit
        )

    async def get_recommendations_for_paper(
        self, paper_id: PaperId, fields: Fields | None = None, limit: int = 10
    ) -> list[Paper]:
        """Get paper recommendations based on a paper with improved response
        handling."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {
            "fields": ",".join(fields),
            "limit": min(limit, 100),  # Max 100 recommendations
        }

        try:
            # Use recommendations API endpoint
            data = await self._make_request(
                "GET", f"/recommendations/v1/papers/forpaper/{paper_id}", params=params
            )

            # Handle response format variations
            papers_data = []
            if isinstance(data, dict):
                # Try different possible keys for recommendations
                for key in ["recommendedPapers", "papers", "data"]:
                    if key in data:
                        papers_data = data[key]
                        break
            elif isinstance(data, list):
                papers_data = data

            # Parse papers with error handling
            papers = []
            for paper_data in papers_data:
                if paper_data:  # Skip None entries
                    try:
                        papers.append(Paper(**paper_data))
                    except Exception as e:
                        self.logger.warning(
                            "Failed to parse recommendation paper data",
                            paper_data=paper_data,
                            error=str(e),
                        )
                        continue

            return papers

        except Exception as e:
            # If recommendations endpoint fails, return empty list with warning
            self.logger.warning(
                "Recommendations endpoint failed, returning empty list",
                paper_id=paper_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def get_circuit_breaker_state(self) -> str:
        """Get current circuit breaker state."""
        return self.circuit_breaker.state.value

    def get_rate_limiter_status(self) -> dict[str, Any]:
        """Get rate limiter status."""
        return {
            "available_tokens": self.rate_limiter.available_tokens,
            "rate": self.rate_limiter.rate,
            "burst": self.rate_limiter.burst,
        }

    async def search_papers_bulk(
        self,
        query: str,
        fields: Fields | None = None,
        publication_types: list[str] | None = None,
        fields_of_study: list[str] | None = None,
        year_range: str | None = None,
        venue: str | None = None,
        min_citation_count: int | None = None,
        open_access_pdf: bool | None = None,
        sort: str | None = None,
        **kwargs,
    ) -> list[Paper]:
        """Bulk search papers with advanced filtering (unlimited results)."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {
            "query": query,
            "fields": ",".join(fields),
        }

        # Map filter parameters correctly
        if publication_types:
            params["publicationTypes"] = (
                ",".join(publication_types)
                if isinstance(publication_types, list)
                else publication_types
            )
        if fields_of_study:
            params["fieldsOfStudy"] = (
                ",".join(fields_of_study)
                if isinstance(fields_of_study, list)
                else fields_of_study
            )
        if year_range:
            params["year"] = year_range
        if venue:
            params["venue"] = venue
        if min_citation_count:
            params["minCitationCount"] = str(min_citation_count)
        if open_access_pdf is not None:
            params["openAccessPdf"] = str(open_access_pdf).lower()
        if sort:
            params["sort"] = sort

        # Handle additional kwargs but skip 'limit' as it's not supported by
        # bulk endpoint
        for key, value in kwargs.items():
            if key != "limit" and value is not None:
                params[key] = value

        data = await self._make_request("GET", "/paper/search/bulk", params=params)

        # Handle response format variations
        if isinstance(data, dict) and "data" in data:
            return [Paper(**paper_data) for paper_data in data["data"]]
        if isinstance(data, list):
            return [Paper(**paper_data) for paper_data in data]
        return []

    async def search_papers_match(
        self, title: str, fields: Fields | None = None
    ) -> list[Paper]:
        """Search papers by title matching."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {"query": title, "fields": ",".join(fields)}

        data = await self._make_request("GET", "/paper/search/match", params=params)

        # Convert raw data to Paper objects, handling matchScore field
        papers = []
        for paper_data in data.get("data", []):
            # Extract matchScore if present
            match_score = paper_data.pop("matchScore", None)

            # Create Paper object using model_validate to bypass constructor validation
            paper = Paper.model_validate(paper_data)

            # Set match_score if provided (field already exists in Paper model)
            if match_score is not None:
                paper.match_score = match_score

            papers.append(paper)

        return papers

    async def autocomplete_query(self, query: str, limit: int = 10) -> list[str]:
        """Get query autocompletion suggestions."""
        params = {"query": query, "limit": limit}

        data = await self._make_request("GET", "/paper/autocomplete", params=params)
        return data.get("suggestions", [])

    async def search_snippets(
        self,
        query: str,
        fields: Fields | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> PaginatedResponse[dict[str, Any]]:
        """Search text snippets in papers."""
        fields = fields or BASIC_PAPER_FIELDS
        params = {
            "query": query,
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset,
        }

        data = await self._make_request("GET", "/snippet/search", params=params)
        snippets = data.get("data", [])

        return PaginatedResponse[dict[str, Any]](
            items=snippets, total=data.get("total", 0), offset=offset, limit=limit
        )

    async def batch_get_authors(
        self, author_ids: list[AuthorId], fields: Fields | None = None
    ) -> list[Author]:
        """Get multiple authors by their IDs."""
        fields = fields or AUTHOR_FIELDS
        data = {
            "ids": author_ids,
            "fields": ",".join(fields),
        }

        response = await self._make_request("POST", "/author/batch", json=data)
        # Handle response format: batch endpoint returns a list directly
        if isinstance(response, list):
            return [Author(**author_data) for author_data in response]
        # Fallback to dict format with "data" key if needed
        return [Author(**author_data) for author_data in response.get("data", [])]

    async def get_recommendations_batch(
        self,
        positive_paper_ids: list[PaperId],
        negative_paper_ids: list[PaperId] | None = None,
        fields: Fields | None = None,
        limit: int = 10,
    ) -> list[Paper]:
        """Get recommendations based on positive and negative examples."""
        fields = fields or BASIC_PAPER_FIELDS
        data = {
            "positivePaperIds": positive_paper_ids,
            "negativePaperIds": negative_paper_ids or [],
            "fields": ",".join(fields),
            "limit": limit,
        }

        try:
            response = await self._make_request(
                "POST", "/recommendations/v1/papers/", json=data
            )
            papers_data = response.get("recommendedPapers", [])
            return [Paper(**paper_data) for paper_data in papers_data]
        except Exception as e:
            self.logger.warning(
                "Advanced recommendations endpoint failed",
                positive_papers=len(positive_paper_ids),
                negative_papers=len(negative_paper_ids or []),
                error=str(e),
            )
            return []

    async def get_dataset_releases(self) -> list[dict[str, Any]]:
        """Get available dataset releases."""
        data = await self._make_request("GET", "/datasets/v1/release/")
        # API returns a list directly, not a dict with "releases" key
        return data if isinstance(data, list) else []

    async def get_dataset_info(self, release_id: str) -> dict[str, Any]:
        """Get dataset release information."""
        return await self._make_request("GET", f"/datasets/v1/release/{release_id}")

    async def get_dataset_download_links(
        self, release_id: str, dataset_name: str
    ) -> dict[str, Any]:
        """Get download links for a specific dataset."""
        return await self._make_request(
            "GET", f"/datasets/v1/release/{release_id}/dataset/{dataset_name}"
        )

    async def get_paper_with_embeddings(
        self,
        paper_id: PaperId,
        embedding_type: str = "specter_v2",
        fields: Fields | None = None,
    ) -> Paper:
        """Get paper with embedding vectors."""
        base_fields = fields or DETAILED_PAPER_FIELDS
        embedding_fields = [f"embedding.{embedding_type}"]
        all_fields = list(base_fields) + embedding_fields

        params = {"fields": ",".join(all_fields)}

        data = await self._make_request("GET", f"/paper/{paper_id}", params=params)
        return Paper(**data)

    async def search_papers_with_embeddings(
        self,
        query: SearchQuery,
        embedding_type: str = "specter_v2",
        fields: Fields | None = None,
    ) -> PaginatedResponse[Paper]:
        """Search papers with embedding vectors."""
        base_fields = fields or BASIC_PAPER_FIELDS
        embedding_fields = [f"embedding.{embedding_type}"]
        all_fields = list(base_fields) + embedding_fields

        params = {
            "query": query.query,
            "fields": ",".join(all_fields),
            "limit": query.limit,
            "offset": query.offset,
        }

        if query.filters:
            if query.filters.publication_types:
                params["publicationTypes"] = ",".join(
                    [pt.value for pt in query.filters.publication_types]
                )
            if query.filters.fields_of_study:
                params["fieldsOfStudy"] = ",".join(query.filters.fields_of_study)
            if query.filters.year:
                params["year"] = str(query.filters.year)
            if query.filters.year_range:
                start, end = query.filters.year_range
                params["year"] = f"{start}-{end}"
            if query.filters.min_citation_count:
                params["minCitationCount"] = str(query.filters.min_citation_count)
            if query.filters.open_access_only:
                params["openAccessPdf"] = "true"

        data = await self._make_request("GET", "/paper/search", params=params)
        papers = [Paper(**paper_data) for paper_data in data.get("data", [])]

        return PaginatedResponse[Paper](
            items=papers,
            total=data.get("total", 0),
            offset=query.offset,
            limit=query.limit,
        )

    async def get_incremental_dataset_updates(
        self, start_release_id: str, end_release_id: str, dataset_name: str
    ) -> dict[str, Any]:
        """Get incremental dataset updates between releases."""
        return await self._make_request(
            "GET",
            f"/datasets/v1/diffs/{start_release_id}/to/{end_release_id}/{dataset_name}",
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        try:
            # Try a simple search
            await self.search_papers(SearchQuery(query="test", limit=1))

            return {
                "status": "healthy",
                "circuit_breaker": self.get_circuit_breaker_state(),
                "rate_limiter": self.get_rate_limiter_status(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker": self.get_circuit_breaker_state(),
                "rate_limiter": self.get_rate_limiter_status(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
