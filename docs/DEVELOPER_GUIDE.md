# Semantic Scholar MCP Server Developer Guide

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Code Architecture](#code-architecture)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Debugging Guide](#debugging-guide)
7. [Performance Profiling](#performance-profiling)
8. [Deployment](#deployment)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Docker (optional, for containerized development)
- Redis (optional, for distributed caching)

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/hy20191108/semantic-scholar-mcp.git
cd semantic-scholar-mcp
```

2. **Create a virtual environment:**
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Using conda
conda create -n semantic-scholar python=3.9
conda activate semantic-scholar
```

3. **Install development dependencies:**
```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or using pip-tools
pip-compile requirements.in
pip-compile requirements-dev.in
pip-sync requirements.txt requirements-dev.txt
```

4. **Set up pre-commit hooks:**
```bash
pre-commit install
pre-commit run --all-files  # Run on all files to verify setup
```

5. **Configure environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.analysis.typeCheckingMode": "strict",
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true
  }
}
```

#### PyCharm

1. Set Python interpreter to virtual environment
2. Enable type checking: Settings → Editor → Inspections → Python → Type checker
3. Configure Black: Settings → Tools → External Tools → Add Black
4. Enable pytest: Settings → Tools → Python Integrated Tools → Testing → pytest

## Project Structure

```
semantic-scholar-mcp/
├── src/                           # Source code
│   ├── semantic_scholar_mcp/      # Main package
│   │   ├── __init__.py           # Package initialization
│   │   ├── server.py             # MCP server implementation
│   │   ├── api_client.py         # Semantic Scholar API client
│   │   ├── models.py             # Pydantic models
│   │   ├── domain_models.py      # Domain-specific models
│   │   ├── base_models.py        # Base model classes
│   │   ├── tools.py              # MCP tool implementations
│   │   ├── resources.py          # MCP resource providers
│   │   ├── prompts.py            # MCP prompt templates
│   │   ├── cache.py              # Caching implementation
│   │   ├── rate_limiter.py       # Rate limiting logic
│   │   └── utils.py              # Utility functions
│   └── core/                     # Core abstractions
│       ├── abstractions.py       # Abstract interfaces
│       ├── exceptions.py         # Custom exceptions
│       ├── types.py              # Type definitions
│       └── constants.py          # Constants and enums
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   ├── performance/              # Performance tests
│   ├── fixtures/                 # Test fixtures
│   └── conftest.py              # Pytest configuration
├── docs/                         # Documentation
├── examples/                     # Usage examples
├── scripts/                      # Utility scripts
├── docker/                       # Docker configuration
├── .github/                      # GitHub Actions workflows
├── pyproject.toml               # Project configuration
├── Makefile                     # Common commands
└── tox.ini                      # Tox configuration
```

### Key Directories

- **src/semantic_scholar_mcp/**: Main application code
- **src/core/**: Shared abstractions and utilities
- **tests/**: All test code organized by type
- **docs/**: Documentation and guides
- **examples/**: Example usage and tutorials
- **scripts/**: Development and deployment scripts

## Code Architecture

### Layered Architecture

```python
# Layer 1: MCP Interface Layer
class SemanticScholarMCPServer:
    """Main MCP server handling protocol communication."""
    
    async def handle_tool_call(self, name: str, arguments: dict) -> dict:
        """Route tool calls to appropriate handlers."""

# Layer 2: Service Layer
class PaperService:
    """Business logic for paper operations."""
    
    async def search_papers(self, query: SearchQuery) -> SearchResult:
        """Search papers with business rules applied."""

# Layer 3: Repository Layer
class PaperRepository:
    """Data access for papers."""
    
    async def find_by_query(self, query: str) -> List[Paper]:
        """Query papers from data source."""

# Layer 4: Infrastructure Layer
class SemanticScholarClient:
    """External API client."""
    
    async def search(self, query: str) -> dict:
        """Make API request."""
```

### Dependency Injection

```python
# Use dependency injection for testability
class PaperService:
    def __init__(
        self,
        repository: PaperRepository,
        cache: CacheManager,
        logger: Logger
    ):
        self.repository = repository
        self.cache = cache
        self.logger = logger

# Factory pattern for creation
class ServiceFactory:
    @staticmethod
    def create_paper_service() -> PaperService:
        return PaperService(
            repository=PaperRepository(...),
            cache=CacheManager(...),
            logger=get_logger(__name__)
        )
```

### Async Patterns

```python
# Concurrent operations
async def get_paper_with_metadata(paper_id: str) -> EnrichedPaper:
    # Run multiple async operations concurrently
    paper_task = get_paper(paper_id)
    citations_task = get_citations(paper_id)
    references_task = get_references(paper_id)
    
    paper, citations, references = await asyncio.gather(
        paper_task,
        citations_task,
        references_task,
        return_exceptions=True
    )
    
    return EnrichedPaper(
        paper=paper,
        citations=citations if not isinstance(citations, Exception) else [],
        references=references if not isinstance(references, Exception) else []
    )

# Async context managers
class AsyncAPIClient:
    async def __aenter__(self):
        self.session = httpx.AsyncClient()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

# Usage
async with AsyncAPIClient() as client:
    result = await client.search("machine learning")
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/add-recommendation-engine

# Make changes and test
code .  # Open in editor
pytest tests/unit/test_recommendations.py

# Commit with conventional commits
git add .
git commit -m "feat: add paper recommendation engine

- Implement content-based filtering
- Add collaborative filtering option
- Include hybrid recommendation mode"

# Push and create PR
git push origin feature/add-recommendation-engine
```

### 2. Code Style

```python
# Follow PEP 8 with Black formatting
# Good
async def search_papers(
    query: str,
    limit: int = 10,
    offset: int = 0,
    fields: Optional[List[str]] = None,
) -> SearchResult:
    """
    Search for papers matching the query.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        offset: Pagination offset
        fields: Fields to include in response
        
    Returns:
        SearchResult with matching papers
        
    Raises:
        ValidationError: If parameters are invalid
        APIError: If API request fails
    """
    if not query or not query.strip():
        raise ValidationError("Query cannot be empty")
        
    # Implementation...

# Bad
async def searchPapers(q,l=10,o=0,f=None):
    if not q: raise Exception("bad query")
    # ...
```

### 3. Type Annotations

```python
# Always use type annotations
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

T = TypeVar('T')

class PagedResponse(Generic[T]):
    """Generic paged response container."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        offset: int = 0,
        limit: int = 10
    ) -> None:
        self.items = items
        self.total = total
        self.offset = offset
        self.limit = limit
        
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.offset + len(self.items) < self.total
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'items': [item.dict() if hasattr(item, 'dict') else item 
                     for item in self.items],
            'total': self.total,
            'offset': self.offset,
            'limit': self.limit,
            'has_next': self.has_next
        }
```

## Testing Strategy

### Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_models.py      # Model validation tests
│   ├── test_services.py    # Service logic tests
│   └── test_utils.py       # Utility function tests
├── integration/            # Tests with external dependencies
│   ├── test_api_client.py  # API client tests
│   └── test_mcp_server.py  # MCP protocol tests
├── performance/            # Performance benchmarks
│   └── test_benchmarks.py  # Speed and memory tests
└── fixtures/               # Shared test data
    ├── papers.json         # Sample paper data
    └── authors.json        # Sample author data
```

### Unit Testing

```python
# tests/unit/test_paper_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from semantic_scholar_mcp.services import PaperService
from semantic_scholar_mcp.models import Paper, SearchQuery

@pytest.fixture
def mock_repository():
    """Create mock repository."""
    repo = Mock()
    repo.search = AsyncMock()
    return repo

@pytest.fixture
def paper_service(mock_repository):
    """Create paper service with mocked dependencies."""
    return PaperService(
        repository=mock_repository,
        cache=Mock(),
        logger=Mock()
    )

@pytest.mark.asyncio
async def test_search_papers_success(paper_service, mock_repository):
    """Test successful paper search."""
    # Arrange
    query = SearchQuery(query="machine learning", limit=5)
    expected_papers = [
        Paper(paperId="123", title="ML Paper 1"),
        Paper(paperId="456", title="ML Paper 2"),
    ]
    mock_repository.search.return_value = expected_papers
    
    # Act
    result = await paper_service.search_papers(query)
    
    # Assert
    assert len(result.items) == 2
    assert result.items[0].title == "ML Paper 1"
    mock_repository.search.assert_called_once_with(query)

@pytest.mark.asyncio
async def test_search_papers_empty_query(paper_service):
    """Test search with empty query raises error."""
    with pytest.raises(ValidationError) as exc_info:
        await paper_service.search_papers(SearchQuery(query=""))
    
    assert "Query cannot be empty" in str(exc_info.value)
```

### Integration Testing

```python
# tests/integration/test_api_client.py
import pytest
import respx
from httpx import Response
from semantic_scholar_mcp.api_client import SemanticScholarClient

@pytest.fixture
async def api_client():
    """Create API client for testing."""
    async with SemanticScholarClient() as client:
        yield client

@respx.mock
@pytest.mark.asyncio
async def test_search_papers_integration(api_client):
    """Test paper search with mocked HTTP responses."""
    # Mock the API response
    mock_response = {
        "total": 100,
        "offset": 0,
        "data": [
            {
                "paperId": "123",
                "title": "Test Paper",
                "year": 2023,
                "authors": [{"name": "John Doe"}]
            }
        ]
    }
    
    respx.get(
        "https://api.semanticscholar.org/graph/v1/paper/search"
    ).mock(return_value=Response(200, json=mock_response))
    
    # Make the request
    result = await api_client.search_papers("test query")
    
    # Verify
    assert result.total == 100
    assert len(result.data) == 1
    assert result.data[0].title == "Test Paper"
```

### Performance Testing

```python
# tests/performance/test_benchmarks.py
import pytest
import asyncio
from memory_profiler import profile
from semantic_scholar_mcp.cache import LRUCache

@pytest.mark.benchmark
def test_cache_performance(benchmark):
    """Benchmark cache operations."""
    cache = LRUCache(maxsize=1000)
    
    def cache_operations():
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
            cache.get(f"key_{i % 100}")
    
    result = benchmark(cache_operations)
    assert result is not None

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling multiple concurrent requests."""
    async def make_request(i):
        # Simulate API request
        await asyncio.sleep(0.1)
        return i
    
    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[
        make_request(i) for i in range(100)
    ])
    duration = asyncio.get_event_loop().time() - start
    
    assert len(results) == 100
    assert duration < 1.0  # Should complete in under 1 second
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from typing import Generator
from semantic_scholar_mcp.models import Paper, Author

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_paper() -> Paper:
    """Create sample paper for testing."""
    return Paper(
        paperId="649def34f8be52c8b66281af98ae884c09aef38b",
        title="Attention Is All You Need",
        year=2017,
        authors=[
            Author(authorId="1741101", name="Ashish Vaswani"),
            Author(authorId="2116939", name="Noam Shazeer")
        ],
        citationCount=45832,
        abstract="The dominant sequence transduction models..."
    )

@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return {
        "total": 1,
        "offset": 0,
        "data": [{
            "paperId": "123",
            "title": "Test Paper",
            "year": 2023
        }]
    }
```

## Debugging Guide

### 1. Enable Debug Logging

```python
# Set up debug logging
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log')
    ]
)

# In your code
logger = logging.getLogger(__name__)

async def search_papers(query: str) -> SearchResult:
    logger.debug(f"Searching papers with query: {query}")
    
    try:
        result = await api_client.search(query)
        logger.debug(f"Found {result.total} papers")
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise
```

### 2. Interactive Debugging

```python
# Using ipdb for debugging
import ipdb

async def complex_function(data):
    processed = preprocess(data)
    ipdb.set_trace()  # Breakpoint here
    result = await api_call(processed)
    return result

# Using VS Code debugger
# launch.json configuration
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug MCP Server",
            "type": "python",
            "request": "launch",
            "module": "semantic_scholar_mcp.server",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src",
                "LOG_LEVEL": "DEBUG"
            },
            "justMyCode": false
        }
    ]
}
```

### 3. Async Debugging

```python
# Debug async code with asyncio
import asyncio

# Enable asyncio debug mode
asyncio.set_debug(True)

# Track slow callbacks
loop = asyncio.get_event_loop()
loop.set_debug(True)
loop.slow_callback_duration = 0.01  # 10ms

# Debug task creation
async def debug_tasks():
    tasks = asyncio.all_tasks()
    for task in tasks:
        print(f"Task: {task.get_name()}")
        print(f"Stack: {task.get_stack()}")
```

### 4. Memory Debugging

```python
# Memory profiling
from memory_profiler import profile
import tracemalloc

@profile
def memory_intensive_function():
    # Large data processing
    data = [i for i in range(1000000)]
    return sum(data)

# Trace memory allocations
tracemalloc.start()

# Your code here
result = process_large_dataset()

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 10**6:.1f} MB")
print(f"Peak memory: {peak / 10**6:.1f} MB")

tracemalloc.stop()
```

### 5. Common Issues

#### Issue: "Event loop is closed"
```python
# Solution: Properly manage event loops
import asyncio

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_function())
    finally:
        loop.close()
```

#### Issue: "Timeout errors"
```python
# Solution: Increase timeout and add retry logic
async def resilient_request(url: str):
    timeout = httpx.Timeout(30.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                return await client.get(url)
            except httpx.TimeoutException:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
```

## Performance Profiling

### 1. CPU Profiling

```python
# Using cProfile
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    result = expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
    
    return result

# Using line_profiler
# Install: pip install line_profiler
# Usage: kernprof -l -v script.py

@profile  # Decorator for line_profiler
def optimized_search(query: str) -> List[Paper]:
    # Each line will be profiled
    normalized = query.lower().strip()
    tokens = normalized.split()
    results = []
    for token in tokens:
        results.extend(search_by_token(token))
    return deduplicate(results)
```

### 2. Async Performance

```python
# Profile async operations
import asyncio
import time

async def measure_async_performance():
    operations = []
    
    # Measure individual operations
    start = time.perf_counter()
    result = await api_call()
    duration = time.perf_counter() - start
    operations.append(('api_call', duration))
    
    # Measure concurrent operations
    start = time.perf_counter()
    results = await asyncio.gather(*[
        api_call() for _ in range(10)
    ])
    duration = time.perf_counter() - start
    operations.append(('10_concurrent_calls', duration))
    
    # Report
    for name, duration in operations:
        print(f"{name}: {duration:.3f}s")
```

### 3. Memory Profiling

```python
# Track memory usage over time
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    
    def get_memory_info():
        return {
            'rss': process.memory_info().rss / 1024 / 1024,  # MB
            'vms': process.memory_info().vms / 1024 / 1024,  # MB
            'percent': process.memory_percent()
        }
    
    # Before operation
    before = get_memory_info()
    
    # Operation
    result = memory_intensive_operation()
    
    # After operation
    after = get_memory_info()
    
    print(f"Memory increase: {after['rss'] - before['rss']:.1f} MB")
    
    return result
```

## Deployment

### 1. Local Development

```bash
# Run server locally
python -m semantic_scholar_mcp.server

# Or with environment variables
LOG_LEVEL=DEBUG CACHE_ENABLED=false python -m semantic_scholar_mcp.server
```

### 2. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY pyproject.toml .

# Install package
RUN pip install --no-cache-dir -e .

# Run server
CMD ["python", "-m", "semantic_scholar_mcp.server"]
```

```bash
# Build and run
docker build -t semantic-scholar-mcp .
docker run -e SEMANTIC_SCHOLAR_API_KEY=your_key semantic-scholar-mcp
```

### 3. Production Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-server:
    build: .
    environment:
      - SEMANTIC_SCHOLAR_API_KEY=${SEMANTIC_SCHOLAR_API_KEY}
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    ports:
      - "8080:8080"
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    
volumes:
  redis_data:
```

### 4. Health Checks

```python
# Implement health check endpoint
async def health_check() -> Dict[str, Any]:
    """Check system health."""
    checks = {
        'api': await check_api_connection(),
        'cache': await check_cache_connection(),
        'rate_limit': check_rate_limit_status()
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return {
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
        'checks': checks,
        'version': __version__
    }
```

## Best Practices

### 1. Error Handling

```python
# Define custom exceptions
class SemanticScholarError(Exception):
    """Base exception for all errors."""
    pass

class APIError(SemanticScholarError):
    """API request failed."""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class RateLimitError(APIError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s", 429)
        self.retry_after = retry_after

# Use context-appropriate error handling
async def robust_api_call(endpoint: str) -> Dict[str, Any]:
    try:
        response = await client.get(endpoint)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            raise RateLimitError(retry_after)
        raise APIError(f"API request failed: {e}", e.response.status_code)
    except httpx.RequestError as e:
        raise APIError(f"Network error: {e}")
```

### 2. Logging Best Practices

```python
# Structured logging
import structlog

logger = structlog.get_logger()

async def process_request(request_id: str, query: str):
    log = logger.bind(request_id=request_id)
    
    log.info("Processing search request", query=query)
    
    try:
        result = await search(query)
        log.info("Search completed", 
                result_count=len(result.items),
                total=result.total)
        return result
    except Exception as e:
        log.error("Search failed", 
                 error=str(e),
                 error_type=type(e).__name__)
        raise
```

### 3. Configuration Management

```python
# Use pydantic for configuration
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    api_key: Optional[str] = Field(None, env='SEMANTIC_SCHOLAR_API_KEY')
    api_base_url: str = 'https://api.semanticscholar.org/v1'
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 1000
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Logging
    log_level: str = 'INFO'
    log_format: str = 'json'
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Global settings instance
settings = Settings()
```

### 4. Documentation

```python
def search_papers(
    query: str,
    *,
    limit: int = 10,
    offset: int = 0,
    fields: Optional[List[str]] = None,
    year: Optional[int] = None,
    venue: Optional[str] = None,
) -> SearchResult:
    """
    Search for academic papers.
    
    This function searches the Semantic Scholar database for papers
    matching the given query. Results can be filtered by various
    criteria and paginated.
    
    Args:
        query: Search query string. Can include:
            - Keywords: "machine learning"
            - Phrases: "neural networks"
            - Authors: "author:Hinton"
            - Title: "title:attention is all you need"
        limit: Maximum number of results (1-100).
        offset: Pagination offset.
        fields: Specific fields to include in response.
            If None, includes default fields.
        year: Filter by publication year.
        venue: Filter by publication venue.
    
    Returns:
        SearchResult containing:
            - items: List of matching papers
            - total: Total number of matches
            - offset: Current offset
            - has_next: Whether more results exist
    
    Raises:
        ValidationError: If query is empty or parameters invalid.
        APIError: If the API request fails.
        RateLimitError: If rate limit is exceeded.
    
    Examples:
        >>> # Simple search
        >>> results = search_papers("transformer architecture")
        
        >>> # Search with filters
        >>> results = search_papers(
        ...     "deep learning",
        ...     year=2023,
        ...     venue="NeurIPS",
        ...     limit=20
        ... )
        
        >>> # Search specific fields
        >>> results = search_papers(
        ...     "GPT",
        ...     fields=["title", "year", "citationCount"]
        ... )
    
    Note:
        Results are cached for 1 hour by default. Set cache_enabled=False
        in settings to disable caching.
    """
    # Implementation...
```

## Common Patterns

### 1. Retry Pattern

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def reliable_api_call(url: str) -> Dict[str, Any]:
    """Make API call with automatic retry."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### 2. Circuit Breaker Pattern

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'
            raise
```

### 3. Builder Pattern

```python
class SearchQueryBuilder:
    """Build complex search queries."""
    
    def __init__(self):
        self._query = ""
        self._filters = {}
        self._fields = []
        
    def with_keywords(self, *keywords: str) -> 'SearchQueryBuilder':
        self._query += " ".join(keywords)
        return self
        
    def with_author(self, author: str) -> 'SearchQueryBuilder':
        self._query += f" author:{author}"
        return self
        
    def with_year(self, year: int) -> 'SearchQueryBuilder':
        self._filters['year'] = year
        return self
        
    def with_fields(self, *fields: str) -> 'SearchQueryBuilder':
        self._fields.extend(fields)
        return self
        
    def build(self) -> SearchQuery:
        return SearchQuery(
            query=self._query.strip(),
            filters=self._filters,
            fields=self._fields or None
        )

# Usage
query = (SearchQueryBuilder()
    .with_keywords("machine", "learning")
    .with_author("Hinton")
    .with_year(2023)
    .with_fields("title", "abstract", "citationCount")
    .build())
```

### 4. Observer Pattern

```python
class EventBus:
    """Simple event bus for decoupled communication."""
    
    def __init__(self):
        self._subscribers = defaultdict(list)
        
    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers[event_type].append(handler)
        
    async def publish(self, event_type: str, data: Any):
        for handler in self._subscribers[event_type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Handler failed for {event_type}: {e}")

# Usage
event_bus = EventBus()

async def on_paper_fetched(paper: Paper):
    logger.info(f"Paper fetched: {paper.title}")
    await update_metrics(paper)

event_bus.subscribe('paper.fetched', on_paper_fetched)

# In your code
paper = await fetch_paper(paper_id)
await event_bus.publish('paper.fetched', paper)
```

## Conclusion

This developer guide provides comprehensive information for working with the Semantic Scholar MCP Server codebase. Key takeaways:

1. **Set up your environment properly** with virtual environments and pre-commit hooks
2. **Follow the layered architecture** for maintainable code
3. **Write comprehensive tests** at unit, integration, and performance levels
4. **Use proper debugging techniques** for async code
5. **Profile performance** to identify bottlenecks
6. **Deploy with Docker** for consistency
7. **Follow best practices** for error handling, logging, and documentation
8. **Use common patterns** for robust, maintainable code

For questions or issues, please refer to the project's issue tracker or contact the maintainers.