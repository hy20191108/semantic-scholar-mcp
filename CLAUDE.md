# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**CRITICAL**: Always update the "Important Information Tracking" section with:
- Current PyPI version when checking releases
- Any critical discoveries or issues found during development
- Important decisions made during implementation
- Known issues and their workarounds

## Core Development Rules

1. **Package Management**
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. **Code Quality**
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum

3. **Testing Requirements**
   - Framework: `uv run --frozen pytest tests`
   - Async testing: use anyio, not asyncio
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

## Important Information Tracking

**IMPORTANT**: Always update this section with critical information discovered during development.

### Current Status
- **PyPI Version**: 0.2.2 (last checked: 2025-07-18)
- **Local Version**: 0.2.3.dev1 (from dist/)
- **Test Coverage**: 22% (minimum required: 30%)

### Important Notes
<!-- Add important discoveries, issues, and decisions here -->
- **mypy issue**: Known import path conflict between `src.core` and `core` modules
- **Disabled tests**: `test_http_integration.py.disabled` and `test_real_api.py.disabled` need API adjustments
- **Coverage**: Currently below 30% threshold but all critical tests pass

### Release Process Analysis
- **Current git tag**: v0.2.2 (last PyPI release: 2025-07-08)
- **Uncommitted changes**: 1 commit ahead (bd7f465) - marked as dirty
- **Version management**: hatch-vcs (automatic from git tags)
- **Build system**: hatchling + hatch-vcs
- **Release triggers**: 
  - GitHub release creation
  - Git tag push (v*)
  - Manual workflow dispatch
- **Trusted publishing**: Configured for both PyPI and TestPyPI via OIDC

### Current CI/CD Status
- **CI Status**: FAILING (lint errors: 54 issues, mypy errors: 2 issues)
- **Test Status**: All 32 tests pass, but coverage is 0% due to --cov path mismatch
- **Blocking Issues**: 
  - Multiple ruff lint violations (line length, complexity, security)
  - mypy import path conflicts
  - Coverage reporting configuration issue
- **Release Readiness**: NOT READY - CI must pass before release

### Version Checking Commands
```bash
# Check current PyPI version
curl -s https://pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.info.version'

# Check local version
uv run python -c "from semantic_scholar_mcp import __version__; print(__version__)"

# Check all available versions on PyPI
curl -s https://pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.releases | keys[]' | sort -V

# Compare with TestPyPI version
curl -s https://test.pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.info.version'

# Check git version info
git describe --tags --dirty
git tag --list --sort=-version:refname | head -5
```

### Release Process Documentation
```bash
# 1. Create a new release (will auto-version from git tags)
git tag v0.2.3
git push origin v0.2.3

# 2. Or create GitHub release (triggers workflow)
gh release create v0.2.3 --title "Release v0.2.3" --notes "Release notes here"

# 3. Or trigger manual release
gh workflow run release.yml

# 4. Test release to TestPyPI (weekly or manual)
gh workflow run test-pypi.yml
```

### Complete Release Workflow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            RELEASE WORKFLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. PRE-RELEASE VALIDATION                                                   │
│    ├─── CI Pipeline (.github/workflows/ci.yml)                             │
│    │    ├─── Lint: ruff check + format                                     │
│    │    ├─── Type Check: mypy                                               │
│    │    └─── Test: pytest on Python 3.10, 3.11, 3.12                     │
│    ├─── Code Review: Claude Code Review (auto on PR)                       │
│    └─── Dependencies: Dependabot (weekly updates)                          │
│                                                                             │
│ 2. RELEASE TRIGGERS                                                         │
│    ├─── GitHub Release Creation                                             │
│    ├─── Git Tag Push (v*)                                                  │
│    └─── Manual Workflow Dispatch                                           │
│                                                                             │
│ 3. BUILD & PUBLISH PIPELINE (.github/workflows/release.yml)                │
│    ├─── Checkout with full git history (fetch-depth: 0)                   │
│    ├─── Setup uv + Python 3.10                                            │
│    ├─── Build packages (uv build)                                          │
│    ├─── Validate packages (wheel + tar.gz)                                 │
│    └─── Publish to PyPI (OIDC trusted publishing)                          │
│                                                                             │
│ 4. TEST PIPELINE (.github/workflows/test-pypi.yml)                         │
│    ├─── Weekly automated test releases                                     │
│    ├─── Manual test releases                                               │
│    └─── Publish to TestPyPI (skip existing)                               │
│                                                                             │
│ 5. VERSION MANAGEMENT                                                       │
│    ├─── hatch-vcs: Auto-version from git tags                             │
│    ├─── Development: 0.2.3.dev1+gSHA.date format                          │
│    └─── Release: Semantic versioning from git tags                        │
└─────────────────────────────────────────────────────────────────────────────┘

CURRENT STATUS: 🚫 NOT READY FOR RELEASE
- CI is failing with 54 lint errors and 2 mypy errors
- Coverage configuration needs fixing
- All code quality issues must be resolved first
```

## Common Development Commands

### Testing
```bash
# Run all tests
uv run --frozen pytest tests

# Run with coverage
uv run --frozen pytest tests --cov=src --cov-report=term-missing

# Run specific test file
uv run --frozen pytest tests/test_error_handling.py

# Run with debug output for pytest issues
PYTEST_DISABLE_PLUGIN_AUTOLOAD="" uv run --frozen pytest tests
```

### Code Quality
```bash
# Format code
uv run --frozen ruff format .

# Lint and fix issues
uv run --frozen ruff check . --fix --unsafe-fixes

# Type checking
uv run --frozen mypy

# Security scanning
uv run --frozen bandit -r src/
```

### Build and Release
```bash
# Build the package
uv build

# Install in development mode
uv sync

# Run the MCP server locally
uv run semantic-scholar-mcp

# Debug with MCP Inspector
uv run mcp dev server_standalone.py
```

### MCP Development
```bash
# Test MCP server directly
uv run semantic-scholar-mcp

# Run with debug mode
DEBUG_MCP_MODE=true uv run semantic-scholar-mcp

# Use standalone server for development
uv run server_standalone.py
```

## Architecture Overview

This is a **Semantic Scholar MCP Server** that provides access to millions of academic papers through the Model Context Protocol (MCP). The architecture follows enterprise-grade patterns with clean separation of concerns.

### Key Components

1. **MCP Server** (`src/semantic_scholar_mcp/server.py`)
   - FastMCP-based implementation
   - 22 tools, 2 resources, 3 prompts
   - Comprehensive error handling and logging

2. **API Client** (`src/semantic_scholar_mcp/api_client_enhanced.py`)
   - Circuit breaker pattern for fault tolerance
   - Rate limiting and retry logic
   - In-memory LRU caching with TTL

3. **Core Infrastructure** (`src/core/`)
   - `config.py`: Configuration management
   - `error_handler.py`: Centralized error handling
   - `logging.py`: Structured logging with correlation IDs
   - `cache.py`: In-memory caching layer
   - `metrics_collector.py`: Performance metrics

4. **Data Models** (`src/semantic_scholar_mcp/`)
   - `base_models.py`: Core entities (Paper, Author, etc.)
   - `domain_models.py`: Business logic models
   - `models.py`: API response models

### Package Structure
```
src/
├── semantic_scholar_mcp/    # Main package
│   ├── server.py           # MCP server implementation
│   ├── api_client_enhanced.py # HTTP client with resilience
│   ├── models.py           # Pydantic models
│   └── utils.py            # Utility functions
└── core/                   # Shared infrastructure
    ├── config.py           # Configuration
    ├── error_handler.py    # Error handling
    ├── logging.py          # Structured logging
    ├── cache.py            # Caching layer
    └── metrics_collector.py # Performance metrics
```

## MCP Configuration

The server supports two deployment modes:

### Development Mode (.mcp.json)
```json
{
  "mcpServers": {
    "semantic-scholar-dev": {
      "command": "uv",
      "args": ["run", "semantic-scholar-mcp"],
      "env": {
        "DEBUG_MCP_MODE": "true",
        "LOG_MCP_MESSAGES": "true",
        "LOG_API_PAYLOADS": "true"
      }
    }
  }
}
```

### Production Mode
```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": ["semantic-scholar-mcp"],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Error Handling Strategy

The codebase implements comprehensive error handling:

1. **Custom Exceptions** (`src/core/exceptions.py`)
   - 14 specialized exception classes
   - Detailed error codes and context
   - Structured error responses

2. **Error Recovery** (`src/core/error_handler.py`)
   - Exponential backoff with jitter
   - Circuit breaker pattern
   - Automatic retry strategies

3. **Logging** (`src/core/logging.py`)
   - Structured JSON logging
   - Correlation IDs for request tracking
   - MCP-safe logging modes

## Testing Guidelines

### Test Structure
- `tests/conftest.py`: Shared fixtures and configuration
- `tests/test_error_handling.py`: Error handling tests (32 tests)
- `tests/test_*.py.disabled`: Temporarily disabled integration tests

### Test Categories
- **Unit tests**: Core functionality testing
- **Integration tests**: API client testing
- **Performance tests**: Metrics and caching
- **Error handling tests**: Comprehensive error scenarios

### Coverage Requirements
- Minimum coverage: 30% (configured in pyproject.toml)
- Focus on critical paths and error conditions
- Test both success and failure scenarios

## Environment Variables

### Required
- `SEMANTIC_SCHOLAR_API_KEY`: API key for higher rate limits (optional)

### Debug Mode
- `DEBUG_MCP_MODE`: Enable detailed MCP logging
- `LOG_MCP_MESSAGES`: Log MCP protocol messages
- `LOG_API_PAYLOADS`: Log API request/response payloads
- `LOG_PERFORMANCE_METRICS`: Enable performance tracking

### Configuration
- `ENVIRONMENT`: test/development/production
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `CACHE_ENABLED`: Enable/disable caching (default: true)

## Common Issues and Solutions

### CI Failures
1. **Formatting**: `uv run --frozen ruff format .`
2. **Type errors**: `uv run --frozen mypy`
3. **Linting**: `uv run --frozen ruff check . --fix --unsafe-fixes`

### Coverage Issues
- Current target: 30% minimum
- Focus on testing core functionality
- Some integration tests are disabled (`.disabled` files)

### MCP Debugging
- Use `DEBUG_MCP_MODE=true` for detailed logging
- Test with `uv run mcp dev server_standalone.py`
- Check `.mcp.json` configuration

## Development Workflow

1. **Setup**: `uv sync` to install dependencies
2. **Development**: Make changes following code quality rules
3. **Testing**: `uv run --frozen pytest tests`
4. **Quality**: Run ruff format, lint, and mypy
5. **Commit**: Follow conventional commit format
6. **PR**: Include tests and update documentation

## API Integration

The server implements all 22 Semantic Scholar API endpoints:

- **Paper Tools**: search, get details, citations, references
- **Author Tools**: search, profiles, paper lists
- **AI Tools**: recommendations, embeddings
- **Dataset Tools**: releases, downloads, incremental updates

Each tool includes proper error handling, rate limiting, and caching.

## Performance Considerations

- **Caching**: In-memory LRU cache with TTL
- **Rate Limiting**: Token bucket algorithm (1req/s default)
- **Circuit Breaker**: Protects against cascading failures
- **Batch Operations**: Efficient bulk processing
- **Metrics**: Performance tracking and alerting

## Security Notes

- Never commit API keys or sensitive data
- Use environment variables for configuration
- Validate all external inputs
- Follow security best practices in dependencies

## Contributing

- Follow existing code patterns
- Add tests for new features
- Update documentation
- Use conventional commit messages
- Respect the 88-character line limit

## Project Development Guidelines

### Development Environment Constraints
- Do NOT use pip or python commands directly - ONLY use uv
- Do NOT use emojis in code or documentation

### MCP Restart Requirements
- Restart MCP server appropriately during development
- Maintain src layout strictly - do not create files in root directory
- Clean up temporary test files after work (e.g., test_*_fix.py, /tmp/*.md)

### Code Quality Standards

#### Language and Documentation
- All code, comments, and docstrings must be in English only
- Use clear and descriptive variable and function names
- Add comprehensive docstrings to all public functions and classes
- Include type hints for all function parameters and return values

#### Type Safety
- Do not use `Any` type - always specify concrete types
- Use mypy to ensure type safety

#### Code Style and Linting
- Resolve all linter errors before task completion
- Follow PEP 8 style guidelines
- Use Ruff for code formatting and linting
- Use mypy for static type checking
- Maintain consistent import order (using isort)
- Prefer pathlib over os.path for file operations

#### Configuration and Constants
- Do not hardcode values - use config files, env vars, or constants
- Define all magic numbers and strings as named constants at module level
- Use environment variables for runtime configuration (API keys, URLs, paths)
- Store application settings in config files (YAML, TOML, JSON)
- Group related constants in dedicated modules or classes
- Make configuration values easily discoverable and documented

### Architecture and Design

#### Dependency Management
- Use `uv` for all dependency management (no pip, pip-tools, or poetry)
- Pin dependency versions in pyproject.toml
- Keep dependencies minimal and well-justified
- Separate development dependencies from runtime dependencies

#### Error Handling
- Use specific exception types rather than generic Exception
- Provide meaningful error messages with context
- Log errors appropriately with proper log levels
- Handle edge cases gracefully

#### Performance Considerations
- Implement caching where appropriate (follow existing cache system)
- Use efficient data structures and algorithms
- Profile performance-critical code paths
- Consider memory usage for large datasets

### Project-Specific Guidelines

#### File Structure and Layout
- Strict adherence to src layout
- Minimize files in root directory
- Clear module dependencies
- Proper test file placement

#### Security Considerations
- Never commit API keys or sensitive data
- Validate all external inputs
- Use secure file permissions for cache and output files
- Follow principle of least privilege for file operations

## Project Information

### Author
- **Name**: hy20191108
- **GitHub**: https://github.com/hy20191108
- **Email**: zwwp9976@gmail.com

### Package Publication
- **PyPI**: https://pypi.org/project/semantic-scholar-mcp/
- **TestPyPI**: https://test.pypi.org/project/semantic-scholar-mcp/
- **Installation**: `pip install semantic-scholar-mcp` (but use `uv add` for development)
- **Latest Version**: Check PyPI for current version

### GitHub Actions Workflows
- **test-pypi.yml**: Publishes to TestPyPI on every push
- **release.yml**: Publishes to PyPI on GitHub release creation or manual trigger
- **CI/CD**: Automated testing on pull requests

### Trusted Publisher Configuration
- **TestPyPI**: Configured (Workflow: test-pypi.yml)
- **PyPI**: Configured (Workflow: release.yml)
- **Authentication**: OIDC (no API tokens required)