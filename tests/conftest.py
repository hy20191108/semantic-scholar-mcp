"""Pytest configuration and shared fixtures."""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio
from dotenv import load_dotenv

from semantic_scholar_mcp.domain_models import (
    Paper, Author, Citation, Reference,
    PaperId, AuthorId, SearchQuery, SearchFilters
)
from semantic_scholar_mcp.base_models import PaginatedResponse
from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from core.config import ApplicationConfig, SemanticScholarConfig
from core.exceptions import APIError, RateLimitError
from core.protocols import ILogger, ICache, IMetricsCollector

# Load test environment variables
load_dotenv(".env.test", override=True)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_logger() -> ILogger:
    """Create a mock logger."""
    logger = MagicMock(spec=ILogger)
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.with_context = MagicMock(return_value=logger)
    return logger


@pytest.fixture
def mock_cache() -> ICache:
    """Create a mock cache."""
    cache = AsyncMock(spec=ICache)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock(return_value=True)
    cache.exists = AsyncMock(return_value=False)
    cache.clear = AsyncMock()
    return cache


@pytest.fixture
def mock_metrics() -> IMetricsCollector:
    """Create a mock metrics collector."""
    metrics = MagicMock(spec=IMetricsCollector)
    metrics.increment = MagicMock()
    metrics.gauge = MagicMock()
    metrics.histogram = MagicMock()
    metrics.flush = MagicMock()
    return metrics


@pytest.fixture
def test_config() -> ApplicationConfig:
    """Create test configuration."""
    return ApplicationConfig(
        semantic_scholar=SemanticScholarConfig(
            api_key=os.getenv("TEST_SEMANTIC_SCHOLAR_API_KEY"),
            timeout=5.0,
            max_connections=10
        ),
        environment="test"
    )


@pytest.fixture
def sample_paper() -> Paper:
    """Create a sample paper for testing."""
    return Paper(
        paperId="test123",
        title="Test Paper: A Comprehensive Study",
        abstract="This is a test abstract for unit testing.",
        year=2024,
        venue="Test Conference",
        authors=[
            {
                "authorId": "author1",
                "name": "John Doe",
                "affiliations": ["Test University"]
            },
            {
                "authorId": "author2",
                "name": "Jane Smith",
                "affiliations": ["Research Institute"]
            }
        ],
        citationCount=42,
        referenceCount=30,
        influentialCitationCount=5,
        externalIds={"DOI": "10.1234/test.2024"},
        url="https://example.com/paper/test123",
        fieldsOfStudy=["Computer Science", "Machine Learning"],
        isOpenAccess=True
    )


@pytest.fixture
def sample_author() -> Author:
    """Create a sample author for testing."""
    return Author(
        authorId="author123",
        name="Dr. Test Author",
        aliases=["T. Author", "Test A. Author"],
        affiliations=["Test University", "Research Lab"],
        homepage="https://example.com/~testauthor",
        citationCount=1000,
        hIndex=25,
        paperCount=50
    )


@pytest.fixture
def sample_citation() -> Citation:
    """Create a sample citation for testing."""
    return Citation(
        paperId="citing123",
        title="Citing Paper Title",
        year=2024,
        authors=[
            {"name": "Citation Author", "authorId": "cite_author1"}
        ],
        venue="Citation Venue",
        citationCount=10,
        isInfluential=True,
        contexts=["The seminal work by [1] demonstrates..."],
        intents=["Background"]
    )


@pytest.fixture
def sample_papers() -> List[Paper]:
    """Create a list of sample papers."""
    papers = []
    for i in range(5):
        papers.append(Paper(
            paperId=f"paper{i}",
            title=f"Test Paper {i}",
            abstract=f"Abstract for paper {i}",
            year=2020 + i,
            venue=f"Venue {i}",
            authors=[
                {
                    "name": f"Author {i}",
                    "authorId": f"author{i}"
                }
            ],
            citationCount=i * 10,
            referenceCount=i * 5,
            influentialCitationCount=i,
            externalIds={},
            fieldsOfStudy=["Computer Science"],
            isOpenAccess=i % 2 == 0
        ))
    return papers


@pytest.fixture
def sample_search_query() -> SearchQuery:
    """Create a sample search query."""
    return SearchQuery(
        query="machine learning",
        limit=10,
        offset=0,
        filters=SearchFilters(
            yearRange=(2020, 2024),
            fieldsOfStudy=["Computer Science"]
        )
    )


@pytest_asyncio.fixture
async def mock_api_client(
    test_config: ApplicationConfig,
    mock_logger: ILogger,
    mock_cache: ICache,
    mock_metrics: IMetricsCollector
) -> AsyncGenerator[SemanticScholarClient, None]:
    """Create a mock API client."""
    client = SemanticScholarClient(
        config=test_config.semantic_scholar,
        logger=mock_logger,
        cache=mock_cache,
        metrics=mock_metrics
    )
    
    # Mock the HTTP client properly
    mock_http = AsyncMock(spec=httpx.AsyncClient)
    client._client = mock_http
    
    yield client
    
    await client.close()


@pytest.fixture
def mock_http_response() -> Dict[str, Any]:
    """Create a mock HTTP response."""
    return {
        "data": [
            {
                "paperId": "test123",
                "title": "Test Paper",
                "abstract": "Test abstract",
                "year": 2024,
                "venue": "Test Venue",
                "authors": [
                    {
                        "authorId": "author1",
                        "name": "Test Author"
                    }
                ],
                "citationCount": 10,
                "referenceCount": 5,
                "influentialCitationCount": 2,
                "externalIds": {"DOI": "10.1234/test"},
                "url": "https://example.com/paper",
                "fieldsOfStudy": ["Computer Science"],
                "isOpenAccess": True
            }
        ],
        "total": 100,
        "offset": 0,
        "next": 10
    }


@pytest.fixture
def rate_limit_headers() -> Dict[str, str]:
    """Create rate limit headers."""
    return {
        "x-rate-limit-limit": "100",
        "x-rate-limit-remaining": "99",
        "x-rate-limit-reset": str(int(datetime.utcnow().timestamp()) + 300),
        "retry-after": "60"
    }


@pytest.fixture
def api_error_response() -> Dict[str, Any]:
    """Create an API error response."""
    return {
        "error": "Bad Request",
        "message": "Invalid search query",
        "code": "INVALID_QUERY"
    }


# Environment-specific fixtures
@pytest.fixture
def integration_test_config() -> ApplicationConfig:
    """Configuration for integration tests (uses real API)."""
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if not api_key:
        pytest.skip("SEMANTIC_SCHOLAR_API_KEY not set for integration tests")
    
    return ApplicationConfig(
        semantic_scholar=SemanticScholarConfig(
            api_key=api_key,
            timeout=30.0
        ),
        environment="integration_test"
    )


@pytest_asyncio.fixture
async def real_api_client(
    integration_test_config: ApplicationConfig
) -> AsyncGenerator[SemanticScholarClient, None]:
    """Create a real API client for integration tests."""
    client = SemanticScholarClient(
        config=integration_test_config.semantic_scholar
    )
    
    yield client
    
    await client.close()


# Test helpers
class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        text: str = ""
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.headers = headers or {}
        self.text = text
    
    def json(self) -> Dict[str, Any]:
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise APIError(
                f"HTTP {self.status_code}",
                error_code="HTTP_ERROR",
                details={"status_code": self.status_code}
            )