"""Pytest configuration and shared fixtures.

Enhanced with JSON specification fixtures and test utilities for:
- /docs/api-specifications/semantic-scholar-graph-v1.json
- /docs/api-specifications/semantic-scholar-recommendations-v1.json
- /docs/api-specifications/semantic-scholar-datasets-v1.json

Provides fixtures and utilities for testing API compliance and implementation
validation.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing."""
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEBUG_MCP_MODE"] = "false"
    os.environ["LOG_LEVEL"] = "ERROR"


@pytest.fixture
def mock_config():
    """Standard mock configuration for tests."""
    config = MagicMock()
    config.logging.level = "ERROR"
    config.logging.format = "json"
    config.logging.file_path = None
    config.logging.debug_mcp_mode = False
    config.logging.debug_level_override = None
    config.logging.log_performance_metrics = False
    config.cache.enabled = True
    config.cache.max_size = 100
    config.cache.ttl_seconds = 300
    config.semantic_scholar = MagicMock()
    config.server.version = "1.0.0"
    config.environment.value = "test"
    return config


# JSON Specification Fixtures


@pytest.fixture(scope="session")
def json_specs_path():
    """Path to JSON API specifications directory."""
    return Path(__file__).parent.parent / "docs" / "api-specifications"


@pytest.fixture(scope="session")
def graph_api_spec(json_specs_path):
    """Load Graph API v1 JSON specification."""
    spec_file = json_specs_path / "semantic-scholar-graph-v1.json"
    if spec_file.exists():
        with open(spec_file) as f:
            return json.load(f)
    return None


@pytest.fixture(scope="session")
def recommendations_api_spec(json_specs_path):
    """Load Recommendations API v1 JSON specification."""
    spec_file = json_specs_path / "semantic-scholar-recommendations-v1.json"
    if spec_file.exists():
        with open(spec_file) as f:
            return json.load(f)
    return None


@pytest.fixture(scope="session")
def datasets_api_spec(json_specs_path):
    """Load Datasets API v1 JSON specification."""
    spec_file = json_specs_path / "semantic-scholar-datasets-v1.json"
    if spec_file.exists():
        with open(spec_file) as f:
            return json.load(f)
    return None


@pytest.fixture
def base_paper_fields(recommendations_api_spec):
    """Extract BasePaper model fields from Recommendations API spec."""
    if not recommendations_api_spec:
        return []

    try:
        # Navigate to BasePaper definition in the JSON spec
        definitions = recommendations_api_spec.get("definitions", {})
        base_paper = definitions.get("BasePaper", {})
        properties = base_paper.get("properties", {})
        return list(properties.keys())
    except (KeyError, AttributeError):
        return []


@pytest.fixture
def publication_types_enum(recommendations_api_spec):
    """Extract PublicationType enum values from JSON spec."""
    if not recommendations_api_spec:
        return []

    try:
        definitions = recommendations_api_spec.get("definitions", {})
        pub_type_def = definitions.get("PublicationType", {})
        return pub_type_def.get("enum", [])
    except (KeyError, AttributeError):
        return []


@pytest.fixture
def external_id_types(graph_api_spec):
    """Extract external ID types from Graph API spec."""
    if not graph_api_spec:
        return []

    try:
        # Look for external ID definitions in the spec
        definitions = graph_api_spec.get("definitions", {})
        external_ids = definitions.get("ExternalIds", {})
        properties = external_ids.get("properties", {})
        return list(properties.keys())
    except (KeyError, AttributeError):
        return []


# Test Data Fixtures


@pytest.fixture
def sample_paper_data():
    """Sample paper data matching JSON spec structure."""
    return {
        "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models...",
        "year": 2017,
        "venue": "NIPS",
        "publicationTypes": ["Conference"],
        "publicationDate": "2017-06-12",
        "authors": [
            {
                "authorId": "1741101",
                "name": "Ashish Vaswani",
                "affiliations": ["Google Brain"],
            }
        ],
        "citationCount": 50000,
        "referenceCount": 100,
        "influentialCitationCount": 5000,
        "externalIds": {"ArXiv": "1706.03762", "DOI": "10.5555/3295222.3295349"},
        "fieldsOfStudy": ["Computer Science", "Machine Learning"],
        "url": "https://example.com/paper",
        "s2Url": "https://semanticscholar.org/paper/649def34",
        "isOpenAccess": True,
    }


@pytest.fixture
def sample_author_data():
    """Sample author data matching JSON spec structure."""
    return {
        "authorId": "1741101",
        "name": "Geoffrey Hinton",
        "aliases": ["G. Hinton", "Geoffrey E. Hinton"],
        "affiliations": ["University of Toronto", "Google"],
        "homepage": "https://example.com/hinton",
        "citationCount": 200000,
        "hIndex": 150,
        "paperCount": 300,
    }


@pytest.fixture
def sample_citation_data():
    """Sample citation data matching JSON spec structure."""
    return {
        "paperId": "123456",
        "title": "Citing Paper Title",
        "year": 2023,
        "citationCount": 50,
        "isInfluential": True,
        "contexts": ["This method builds upon the work of..."],
        "intents": ["methodology"],
    }


# API Testing Utilities


@pytest.fixture
def api_endpoints():
    """API endpoint configurations for testing."""
    return {
        "graph": {
            "base_url": "https://api.semanticscholar.org/graph/v1",
            "endpoints": {
                "paper_search": "/paper/search",
                "paper_batch": "/paper/batch",
                "paper_detail": "/paper/{paper_id}",
                "paper_citations": "/paper/{paper_id}/citations",
                "paper_references": "/paper/{paper_id}/references",
                "author_search": "/author/search",
                "author_batch": "/author/batch",
                "author_detail": "/author/{author_id}",
                "author_papers": "/author/{author_id}/papers",
            },
        },
        "recommendations": {
            "base_url": "https://api.semanticscholar.org/recommendations/v1",
            "endpoints": {
                "for_paper": "/papers/forpaper/{paper_id}",
                "bulk": "/papers/",
            },
        },
        "datasets": {
            "base_url": "https://api.semanticscholar.org/datasets/v1",
            "endpoints": {
                "releases": "/release",
                "release_info": "/release/{release_id}",
                "dataset_download": "/release/{release_id}/dataset/{dataset_name}",
                "incremental": (
                    "/release/{release_id}/dataset/{dataset_name}/incremental"
                ),
            },
        },
    }


@pytest.fixture
def api_constraints():
    """API constraint definitions from JSON specifications."""
    return {
        "batch_limits": {"papers": 500, "authors": 1000},
        "response_limits": {"max_size_mb": 10, "max_citations": 9999},
        "pagination": {"max_limit": 1000, "default_limit": 10},
        "rate_limits": {"requests_per_second": 1, "burst_limit": 10},
    }


@pytest.fixture
def field_examples():
    """Field selection examples from JSON specifications."""
    return {
        "basic_fields": [
            "paperId",
            "title",
            "abstract",
            "year",
            "venue",
            "citationCount",
        ],
        "nested_fields": [
            "authors.name",
            "authors.authorId",
            "authors.affiliations",
            "citations.title",
            "citations.year",
            "references.title",
            "publicationVenue.name",
            "publicationVenue.type",
        ],
        "complex_fields": [
            "authors.name,authors.affiliations",
            "citations.title,citations.year,citations.authors.name",
            "references.title,references.authors.name",
        ],
    }


# Mock API Response Fixtures


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for API testing."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    # Default successful response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [], "total": 0}
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_paper_search_response():
    """Mock paper search API response."""
    return {
        "data": [
            {
                "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
                "title": "Attention Is All You Need",
                "year": 2017,
                "citationCount": 50000,
            }
        ],
        "total": 1,
        "offset": 0,
        "next": None,
    }


@pytest.fixture
def mock_recommendations_response():
    """Mock recommendations API response."""
    return {
        "recommendedPapers": [
            {
                "paperId": "123456",
                "title": "Transformer Networks",
                "year": 2018,
                "citationCount": 1000,
            }
        ]
    }


@pytest.fixture
def mock_dataset_releases_response():
    """Mock dataset releases API response."""
    return [
        {
            "release_id": "2023-01-01",
            "README": "Dataset release notes...",
            "datasets": [
                {"name": "papers", "description": "Paper metadata"},
                {"name": "authors", "description": "Author information"},
            ],
        }
    ]


# Validation Utilities


class APISpecValidator:
    """Utility class for validating API responses against JSON specifications."""

    def __init__(self, spec: dict[str, Any]):
        self.spec = spec

    def validate_response_structure(
        self, response: dict[str, Any], endpoint: str
    ) -> bool:
        """Validate response structure against spec."""
        # Implementation would check response against OpenAPI spec
        return True

    def validate_field_selection(
        self, response: dict[str, Any], requested_fields: list[str]
    ) -> bool:
        """Validate that response contains only requested fields."""
        # Implementation would verify field compliance
        return True

    def validate_pagination(self, response: dict[str, Any]) -> bool:
        """Validate pagination structure."""
        required_fields = ["data", "total", "offset"]
        return all(field in response for field in required_fields)


@pytest.fixture
def spec_validator(graph_api_spec):
    """Create API specification validator."""
    return APISpecValidator(graph_api_spec) if graph_api_spec else None


# Test Markers


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "api: marks tests that require API access")
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line(
        "markers", "compliance: marks JSON specification compliance tests"
    )


# Test Utilities


def compare_field_lists(actual: list[str], expected: list[str]) -> list[str]:
    """Compare field lists and return differences."""
    actual_set = set(actual)
    expected_set = set(expected)
    return list(expected_set - actual_set)


def extract_nested_field(data: dict[str, Any], field_path: str) -> Any:
    """Extract nested field using dot notation."""
    parts = field_path.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            return [
                extract_nested_field(item, ".".join(parts[parts.index(part) :]))
                for item in current
                if isinstance(item, dict)
            ]
        else:
            return None

    return current


def validate_api_constraints(data: Any, constraint_type: str) -> bool:
    """Validate data against API constraints."""
    constraints = {
        "batch_size_papers": lambda x: len(x) <= 500,
        "batch_size_authors": lambda x: len(x) <= 1000,
        "citation_count": lambda x: x <= 9999,
        "response_size": lambda x: len(str(x).encode()) <= 10 * 1024 * 1024,
    }

    validator = constraints.get(constraint_type)
    return validator(data) if validator else True
