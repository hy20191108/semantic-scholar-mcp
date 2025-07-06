"""Unit tests for API client."""

import asyncio
from datetime import datetime
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from semantic_scholar_mcp.domain_models import (
    Paper, Author, PaperId, AuthorId,
    SearchQuery
)
from semantic_scholar_mcp.base_models import PaginatedResponse
from core.exceptions import (
    APIError, RateLimitError, ValidationError,
    NetworkError, ServiceUnavailableError
)
from semantic_scholar_mcp.api_client_enhanced import CircuitBreakerState


class TestSemanticScholarClient:
    """Test SemanticScholarClient."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_api_client):
        """Test client initialization."""
        assert mock_api_client.config is not None
        assert mock_api_client.logger is not None
        assert mock_api_client.circuit_breaker is not None
        assert mock_api_client.rate_limiter is not None
        assert mock_api_client.retry_strategy is not None
    
    @pytest.mark.asyncio
    async def test_search_papers_success(
        self,
        mock_api_client,
        mock_http_response,
        sample_search_query
    ):
        """Test successful paper search."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = lambda: mock_http_response
        mock_response.headers = {}
        
        mock_api_client._client.request = AsyncMock(
            return_value=mock_response
        )
        
        # Execute search
        result = await mock_api_client.search_papers(sample_search_query)
        
        # Verify result
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 1
        assert result.items[0].paper_id == "test123"
        assert result.total == 100
        
        # Verify API call
        mock_api_client._client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_papers_with_cache_hit(
        self,
        mock_api_client,
        mock_cache,
        sample_search_query,
        sample_papers
    ):
        """Test paper search with cache hit."""
        # Setup cache hit with API format (by_alias=True)
        cached_response = PaginatedResponse(
            items=sample_papers,
            total=100,
            offset=0,
            limit=10
        )
        # Serialize papers with aliases for cache
        cache_data = {
            "items": [paper.model_dump(by_alias=True) for paper in sample_papers],
            "total": 100,
            "offset": 0,
            "limit": 10
        }
        mock_cache.get.return_value = cache_data
        
        # Execute search
        result = await mock_api_client.search_papers(sample_search_query)
        
        # Verify cache was checked
        mock_cache.get.assert_called_once()
        
        # Verify no API call was made
        mock_api_client._client.request.assert_not_called()
        
        # Verify result
        assert len(result.items) == 5
        assert result.total == 100
    
    @pytest.mark.asyncio
    async def test_search_papers_rate_limit(
        self,
        mock_api_client,
        sample_search_query,
        rate_limit_headers
    ):
        """Test paper search with rate limit error."""
        # Mock rate limit response
        mock_api_client._client.request = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited",
                request=MagicMock(),
                response=MagicMock(
                    status_code=429,
                    headers=rate_limit_headers,
                    json=lambda: {"error": "Rate limit exceeded"}
                )
            )
        )
        
        # Execute search and expect rate limit error
        with pytest.raises(RateLimitError) as exc_info:
            await mock_api_client.search_papers(sample_search_query)
        
        # Verify error details
        assert exc_info.value.retry_after == 60
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_paper_success(
        self,
        mock_api_client,
        sample_paper
    ):
        """Test successful paper retrieval."""
        # Mock HTTP response
        mock_response = {
            "paperId": sample_paper.paper_id,
            "title": sample_paper.title,
            "abstract": sample_paper.abstract,
            "year": sample_paper.year,
            "venue": sample_paper.venue,
            "authors": [
                {
                    "authorId": a.author_id,
                    "name": a.name
                }
                for a in sample_paper.authors
            ],
            "citationCount": sample_paper.citation_count,
            "referenceCount": sample_paper.reference_count,
            "influentialCitationCount": sample_paper.influential_citation_count,
            "externalIds": sample_paper.external_ids,
            "url": sample_paper.url,
            "fieldsOfStudy": sample_paper.fields_of_study,
            "isOpenAccess": sample_paper.is_open_access
        }
        
        mock_api_client._client.request = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                headers={}
            )
        )
        
        # Execute get
        result = await mock_api_client.get_paper(PaperId("test123"))
        
        # Verify result
        assert isinstance(result, Paper)
        assert result.paper_id == sample_paper.paper_id
        assert result.title == sample_paper.title
        assert result.citation_count == sample_paper.citation_count
    
    @pytest.mark.asyncio
    async def test_get_paper_not_found(self, mock_api_client):
        """Test paper not found error."""
        # Mock 404 response
        mock_api_client._client.request = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not found",
                request=MagicMock(),
                response=MagicMock(
                    status_code=404,
                    json=lambda: {"error": "Paper not found"}
                )
            )
        )
        
        # Execute and expect error
        with pytest.raises(APIError) as exc_info:
            await mock_api_client.get_paper(PaperId("invalid"))
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_batch_get_papers(
        self,
        mock_api_client,
        sample_papers
    ):
        """Test batch paper retrieval."""
        paper_ids = [p.paper_id for p in sample_papers[:3]]
        
        # Mock response
        mock_response = {
            "data": [
                {
                    "paperId": p.paper_id,
                    "title": p.title,
                    "year": p.year,
                    "authors": [{"name": a.name} for a in p.authors],
                    "citationCount": p.citation_count,
                    "referenceCount": p.reference_count,
                    "influentialCitationCount": p.influential_citation_count,
                    "externalIds": p.external_ids,
                    "fieldsOfStudy": p.fields_of_study,
                    "isOpenAccess": p.is_open_access
                }
                for p in sample_papers[:3]
            ]
        }
        
        mock_api_client._client.request = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                headers={}
            )
        )
        
        # Execute batch get
        result = await mock_api_client.batch_get_papers(paper_ids)
        
        # Verify result
        assert len(result) == 3
        assert all(isinstance(p, Paper) for p in result)
        assert [p.paper_id for p in result] == paper_ids
    
    @pytest.mark.asyncio
    async def test_batch_get_papers_validation(self, mock_api_client):
        """Test batch get papers validation."""
        # Too many IDs should fail
        paper_ids = [PaperId(f"paper{i}") for i in range(101)]
        
        with pytest.raises(ValidationError) as exc_info:
            await mock_api_client.batch_get_papers(paper_ids)
        
        assert "Maximum 100 paper IDs" in str(exc_info.value)
        
        # Empty list should fail
        with pytest.raises(ValidationError) as exc_info:
            await mock_api_client.batch_get_papers([])
        
        assert "At least one paper ID" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_author_success(
        self,
        mock_api_client,
        sample_author
    ):
        """Test successful author retrieval."""
        # Mock response
        mock_response = {
            "authorId": sample_author.author_id,
            "name": sample_author.name,
            "aliases": sample_author.aliases,
            "affiliations": sample_author.affiliations,
            "homepage": sample_author.homepage,
            "citationCount": sample_author.citation_count,
            "hIndex": sample_author.h_index,
            "paperCount": sample_author.paper_count
        }
        
        mock_api_client._client.request = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                headers={}
            )
        )
        
        # Execute get
        result = await mock_api_client.get_author(AuthorId("author123"))
        
        # Verify result
        assert isinstance(result, Author)
        assert result.author_id == sample_author.author_id
        assert result.name == sample_author.name
        assert result.h_index == sample_author.h_index
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_open(self, mock_api_client):
        """Test circuit breaker in open state."""
        # Force circuit breaker to open state
        mock_api_client.circuit_breaker._state = CircuitBreakerState.OPEN
        mock_api_client.circuit_breaker._last_failure_time = datetime.utcnow()
        
        # Try to make a request
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await mock_api_client.search_papers(
                SearchQuery(query="test")
            )
        
        assert "Circuit breaker is open" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(
        self,
        mock_api_client,
        sample_search_query
    ):
        """Test retry mechanism on transient failures."""
        # Mock responses: fail twice, then succeed
        call_count = 0
        
        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # Simulate transient failure
                raise httpx.ConnectTimeout("Connection timeout")
            else:
                # Success on third attempt
                return MagicMock(
                    status_code=200,
                    json=lambda: {"data": [], "total": 0},
                    headers={}
                )
        
        mock_api_client._client.request = mock_post
        
        # Execute search
        result = await mock_api_client.search_papers(sample_search_query)
        
        # Verify retries occurred
        assert call_count == 3
        assert isinstance(result, PaginatedResponse)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        mock_api_client,
        sample_search_query
    ):
        """Test request timeout handling."""
        # Mock timeout
        mock_api_client._client.request = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        
        # Execute and expect timeout error
        with pytest.raises(NetworkError) as exc_info:
            await mock_api_client.search_papers(sample_search_query)
        
        assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_api_client):
        """Test health check endpoint."""
        # Mock successful response
        mock_api_client._client.request = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"status": "healthy"},
                headers={}
            )
        )
        
        # Execute health check
        result = await mock_api_client.health_check()
        
        # Verify result
        assert result["status"] == "healthy"
        assert result["api_accessible"] is True
        assert "version" in result
        assert "uptime_seconds" in result
    
    @pytest.mark.asyncio
    async def test_rate_limiter_throttling(
        self,
        mock_api_client,
        sample_search_query
    ):
        """Test rate limiter throttling."""
        # Configure rate limiter for testing (1 request per second)
        mock_api_client.rate_limiter._rate = 1.0
        mock_api_client.rate_limiter._burst = 1
        mock_api_client.rate_limiter._tokens = 1.0
        
        # Mock successful responses
        mock_api_client._client.request = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: {"data": [], "total": 0},
                headers={}
            )
        )
        
        # Make rapid requests
        start_time = asyncio.get_event_loop().time()
        
        # First request should succeed immediately
        await mock_api_client.search_papers(sample_search_query)
        
        # Second request should be delayed
        await mock_api_client.search_papers(sample_search_query)
        
        end_time = asyncio.get_event_loop().time()
        
        # Verify throttling occurred (at least 0.5 seconds delay)
        assert end_time - start_time >= 0.5