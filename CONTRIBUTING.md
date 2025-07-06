# Contributing to Semantic Scholar MCP

Thank you for your interest in contributing to Semantic Scholar MCP! We welcome contributions from the community and are grateful for any help you can provide.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)
9. [Release Process](#release-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to [maintainers@example.com].

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- A Semantic Scholar API key (optional, but recommended)

### First Steps

1. Fork the repository on GitHub
2. Clone your fork locally
3. Add the upstream repository as a remote
4. Create a new branch for your feature or bug fix

```bash
git clone https://github.com/YOUR_USERNAME/semantic-scholar-mcp.git
cd semantic-scholar-mcp
git remote add upstream https://github.com/ORIGINAL_OWNER/semantic-scholar-mcp.git
git checkout -b feature/your-feature-name
```

## Development Setup

### 1. Create Virtual Environment

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install package in development mode with all dependencies
uv pip install -e ".[dev]"
```

### 3. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
# Optional: Add your Semantic Scholar API key
SEMANTIC_SCHOLAR_API_KEY=your-api-key-here

# Development settings
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### 5. Verify Installation

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Run type checking
uv run mypy src
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When reporting bugs, include:**

1. **Clear title and description**
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **System information** (OS, Python version, package versions)
6. **Relevant logs or error messages**
7. **Code snippets** (if applicable)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues.

**When suggesting enhancements, include:**

1. **Use case** - Why is this enhancement needed?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - What other solutions did you consider?
4. **Additional context** - Any other relevant information

### Your First Code Contribution

1. **Find an issue** - Look for issues labeled `good first issue` or `help wanted`
2. **Comment on the issue** - Let others know you're working on it
3. **Ask questions** - If anything is unclear, ask for clarification
4. **Submit early** - Open a draft PR early to get feedback

### Code Contributions

1. **Write tests first** - Follow TDD principles when possible
2. **Keep changes focused** - One feature/fix per PR
3. **Update documentation** - Include relevant doc updates
4. **Follow coding standards** - Use the project's style guide

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests**
   ```bash
   uv run pytest
   uv run pytest --cov=semantic_scholar_mcp --cov-report=html
   ```

3. **Run code quality checks**
   ```bash
   uv run black src tests
   uv run isort src tests
   uv run ruff check src tests
   uv run mypy src
   ```

4. **Update documentation**
   - Update README.md if needed
   - Update API documentation
   - Add usage examples

### Submitting the PR

1. **Write a clear PR description**
   - Reference the issue being fixed
   - Describe the changes made
   - Include any breaking changes
   - Add screenshots for UI changes

2. **PR Title Format**
   ```
   type(scope): description
   
   Examples:
   feat(tools): add author search by affiliation
   fix(cache): resolve memory leak in LRU cache
   docs(api): update rate limit documentation
   test(client): add integration tests for batch operations
   ```

3. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Related Issue
   Fixes #(issue number)
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows project style
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   ```

### After Submitting

1. **Respond to feedback** - Address reviewer comments promptly
2. **Keep PR updated** - Rebase if needed
3. **Be patient** - Reviews may take time
4. **Iterate** - Make requested changes

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use type hints for all public functions
- Use descriptive variable names
- Prefer f-strings for formatting

### Type Hints

```python
from typing import List, Optional, Dict, Any
from semantic_scholar_mcp.models import Paper, Author

async def search_papers(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Paper]:
    """
    Search for papers matching the query.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        filters: Optional search filters
        
    Returns:
        List of matching papers
        
    Raises:
        ValidationError: If query is invalid
        APIError: If API request fails
    """
    ...
```

### Error Handling

```python
try:
    result = await api_call()
except httpx.TimeoutException as e:
    logger.error(f"Request timeout: {e}")
    raise NetworkError("Request timed out", inner_exception=e)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        raise RateLimitError("Rate limit exceeded", retry_after=60)
    raise APIError(f"API error: {e.response.status_code}")
```

### Async/Await

- Use `async`/`await` for all I/O operations
- Use `asyncio.gather` for concurrent operations
- Properly handle cleanup with `async with`

### Logging

```python
logger = logging.getLogger(__name__)

# Use structured logging
logger.info(
    "API request completed",
    extra={
        "endpoint": "/papers/search",
        "query": query,
        "duration_ms": duration,
        "result_count": len(results)
    }
)
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests with external services
├── fixtures/       # Test fixtures and mock data
└── conftest.py     # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_search_papers_success():
    """Test successful paper search."""
    # Arrange
    mock_client = AsyncMock()
    mock_client.search.return_value = [...]
    
    # Act
    results = await search_papers("machine learning", client=mock_client)
    
    # Assert
    assert len(results) == 10
    mock_client.search.assert_called_once_with(
        query="machine learning",
        limit=10
    )

@pytest.mark.asyncio
async def test_search_papers_rate_limit():
    """Test rate limit handling."""
    # Test rate limit error handling
    ...
```

### Test Coverage

- Aim for >90% code coverage
- Test edge cases and error conditions
- Include integration tests for critical paths
- Mock external dependencies in unit tests

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=semantic_scholar_mcp

# Run specific test file
uv run pytest tests/unit/test_api_client.py

# Run tests matching pattern
uv run pytest -k "search"

# Run integration tests only
uv run pytest tests/integration/
```

## Documentation

### Code Documentation

- Use Google-style docstrings
- Document all public APIs
- Include usage examples
- Document exceptions raised

```python
def process_papers(papers: List[Paper], filters: Dict[str, Any]) -> List[Paper]:
    """
    Process and filter a list of papers.
    
    Args:
        papers: List of Paper objects to process
        filters: Dictionary of filter criteria
            - year_min: Minimum publication year
            - year_max: Maximum publication year
            - min_citations: Minimum citation count
            
    Returns:
        Filtered list of papers
        
    Raises:
        ValidationError: If filters are invalid
        
    Example:
        >>> papers = await client.search_papers("AI")
        >>> filtered = process_papers(
        ...     papers,
        ...     {"year_min": 2020, "min_citations": 10}
        ... )
    """
```

### API Documentation

- Update API_REFERENCE.md for new endpoints
- Include request/response examples
- Document error codes
- Update OpenAPI schema if applicable

### User Documentation

- Update README.md for new features
- Add usage examples to USAGE_EXAMPLES.md
- Update configuration docs
- Include migration guides for breaking changes

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- MAJOR: Breaking API changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes

### Release Checklist

1. **Update version**
   ```bash
   # Update version in pyproject.toml
   # Update CHANGELOG.md
   ```

2. **Create release PR**
   - Title: `Release v{version}`
   - Include changelog in description

3. **After merge**
   ```bash
   git tag v{version}
   git push origin v{version}
   ```

4. **GitHub Release**
   - Create release from tag
   - Include changelog
   - Attach built artifacts

5. **PyPI Release**
   ```bash
   uv build
   twine upload dist/*
   ```

### Changelog Format

```markdown
## [1.2.0] - 2024-01-15

### Added
- New author search by affiliation
- Batch paper retrieval endpoint

### Changed
- Improved rate limit handling
- Updated to httpx 0.27.0

### Fixed
- Memory leak in cache implementation
- Unicode handling in paper titles

### Deprecated
- Old search_by_keyword function (use search_papers)

### Security
- Updated dependencies for CVE-2024-xxxxx
```

## Getting Help

- **Discord**: [Join our server](https://discord.gg/example)
- **GitHub Discussions**: Ask questions and share ideas
- **Issue Tracker**: Report bugs and request features
- **Email**: maintainers@example.com

Thank you for contributing to Semantic Scholar MCP! 🎉