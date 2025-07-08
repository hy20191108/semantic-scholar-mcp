"""Semantic Scholar API client."""

from datetime import datetime, timedelta
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import AuthorDetails, Paper, SearchResult


class RateLimitError(Exception):
    """Raised when API rate limit is exceeded."""



class SemanticScholarClient:
    """Client for Semantic Scholar API."""

    BASE_URL = "https://api.semanticscholar.org/v1"
    GRAPH_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize the client.

        Args:
            api_key: Optional API key for higher rate limits
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._rate_limit_reset: datetime | None = None
        self._request_count = 0
        self._request_window_start = datetime.now()

    async def __aenter__(self):
        """Enter async context."""
        self._client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "User-Agent": "semantic-scholar-mcp/0.1.0",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limits."""
        # Reset counter every minute
        if datetime.now() - self._request_window_start > timedelta(minutes=1):
            self._request_count = 0
            self._request_window_start = datetime.now()

        # Basic rate limit: 100 requests per minute without API key
        max_requests = 100 if not self.api_key else 1000
        if self._request_count >= max_requests:
            wait_time = 60 - (datetime.now() - self._request_window_start).seconds
            raise RateLimitError(f"Rate limit exceeded. Wait {wait_time} seconds.")

        self._request_count += 1

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request with retry logic."""
        await self._check_rate_limit()

        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        response = await self._client.request(
            method=method,
            url=url,
            params=params,
            json=json,
        )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after}s.")

        response.raise_for_status()
        return response.json()

    async def search_papers(
        self,
        query: str,
        fields: list[str] | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResult:
        """Search for papers.

        Args:
            query: Search query
            fields: Fields to include in response
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            SearchResult with papers
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "year",
                "authors",
                "venue",
                "citationCount",
                "referenceCount",
                "url",
                "arxivId",
                "doi",
                "fieldsOfStudy",
            ]

        params = {
            "query": query,
            "fields": ",".join(fields),
            "limit": limit,
            "offset": offset,
        }

        data = await self._make_request(
            "GET",
            f"{self.GRAPH_URL}/paper/search",
            params=params,
        )

        return SearchResult(**data)

    async def get_paper(
        self,
        paper_id: str,
        fields: list[str] | None = None,
    ) -> Paper:
        """Get paper details by ID.

        Args:
            paper_id: Paper ID (Semantic Scholar ID, DOI, or ArXiv ID)
            fields: Fields to include in response

        Returns:
            Paper details
        """
        if fields is None:
            fields = [
                "paperId",
                "title",
                "abstract",
                "year",
                "authors",
                "venue",
                "citationCount",
                "referenceCount",
                "url",
                "arxivId",
                "doi",
                "fieldsOfStudy",
            ]

        params = {"fields": ",".join(fields)}

        data = await self._make_request(
            "GET",
            f"{self.GRAPH_URL}/paper/{paper_id}",
            params=params,
        )

        return Paper(**data)

    async def get_author(
        self,
        author_id: str,
        fields: list[str] | None = None,
        papers_limit: int = 10,
    ) -> AuthorDetails:
        """Get author details by ID.

        Args:
            author_id: Author ID
            fields: Fields to include in response
            papers_limit: Maximum number of papers to include

        Returns:
            Author details
        """
        if fields is None:
            fields = [
                "authorId",
                "name",
                "aliases",
                "affiliations",
                "homepage",
                "paperCount",
                "citationCount",
                "hIndex",
            ]

        params = {
            "fields": ",".join(fields),
        }

        # Get author details
        author_data = await self._make_request(
            "GET",
            f"{self.GRAPH_URL}/author/{author_id}",
            params=params,
        )

        # Get author's papers
        papers_params = {
            "fields": "paperId,title,year,citationCount,authors",
            "limit": papers_limit,
        }
        papers_data = await self._make_request(
            "GET",
            f"{self.GRAPH_URL}/author/{author_id}/papers",
            params=papers_params,
        )

        author_data["papers"] = papers_data.get("data", [])
        return AuthorDetails(**author_data)
