"""Pytest configuration and shared fixtures."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_paper_data():
    """Mock paper data for tests."""
    return {
        "paperId": "test123",
        "title": "Test Paper: A Comprehensive Study",
        "abstract": "This is a test abstract for unit testing purposes.",
        "year": 2024,
        "venue": "Test Conference 2024",
        "citationCount": 42,
        "referenceCount": 30,
        "influentialCitationCount": 5,
        "url": "https://example.com/paper/test123",
        "authors": [
            {"authorId": "author1", "name": "John Doe"},
            {"authorId": "author2", "name": "Jane Smith"}
        ],
        "fieldsOfStudy": ["Computer Science", "Machine Learning"],
        "externalIds": {
            "DOI": "10.1234/test.2024.123",
            "ArXiv": "2024.12345"
        }
    }


@pytest.fixture
def mock_author_data():
    """Mock author data for tests."""
    return {
        "authorId": "1234567",
        "name": "Dr. Test Author",
        "aliases": ["T. Author", "Test A."],
        "affiliations": ["Test University", "Research Lab"],
        "homepage": "https://example.com/author",
        "paperCount": 150,
        "citationCount": 5000,
        "hIndex": 35
    }
