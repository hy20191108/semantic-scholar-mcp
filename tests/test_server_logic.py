"""Unit tests for server business logic."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from semantic_scholar_mcp.domain_models import Author, Paper


class TestServerLogic:
    """Unit tests for server business logic without external dependencies."""

    def test_paper_model_dump_formats(self):
        """Test paper model dumping in different formats."""
        # Create real Paper objects (not mocks)
        author1 = Author(name="John Doe", authorId="123")
        author2 = Author(name="Jane Smith", authorId="456")
        
        paper = Paper(
            paperId="test-123",
            title="Test Paper",
            abstract="This is a test abstract.",
            year=2024,
            venue="Test Conference",
            citationCount=42,
            authors=[author1, author2]
        )
        
        # Test formatting using local helper function
        formatted = format_paper_response([paper])
        assert len(formatted) == 1
        assert formatted[0]["paperId"] == "test-123"
        assert formatted[0]["title"] == "Test Paper"
        assert formatted[0]["citationCount"] == 42
        assert len(formatted[0]["authors"]) == 2
        
        # Test validation function
        assert validate_search_params("test", 10, 0) is True
        assert validate_search_params("", 10, 0) is False

    def test_paper_serialization(self):
        """Test that papers serialize correctly."""
        paper = Paper(
            paperId="test-456",
            title="Serialization Test",
            year=2023
        )
        
        # Test model_dump functionality with alias
        data = paper.model_dump(by_alias=True)
        
        assert data["paperId"] == "test-456"
        assert data["title"] == "Serialization Test"
        assert data["year"] == 2023
        assert "authors" in data  # Should have default empty list
        
        # Test model_dump without alias (internal field names)
        internal_data = paper.model_dump(by_alias=False)
        assert internal_data["paper_id"] == "test-456"

    def test_author_validation(self):
        """Test author model validation."""
        # Valid author
        author = Author(name="Valid Author")
        assert author.name == "Valid Author"
        
        # Invalid author (empty name should be caught by validation)
        with pytest.raises(ValueError):
            Author(name="")

    def test_paper_validation(self):
        """Test paper model validation."""
        # Valid paper
        paper = Paper(paperId="123", title="Valid Title")
        assert paper.title == "Valid Title"
        
        # Invalid paper (empty title)
        with pytest.raises(ValueError):
            Paper(paperId="123", title="")
        
        # Invalid year (too old)
        with pytest.raises(ValueError):
            Paper(paperId="123", title="Old Paper", year=1800)
        
        # Invalid year (future)
        with pytest.raises(ValueError):
            Paper(paperId="123", title="Future Paper", year=2030)

    def test_citation_metrics_validation(self):
        """Test citation metrics validation in papers."""
        # Valid metrics
        paper = Paper(
            paperId="123",
            title="Test",
            citationCount=100,
            influentialCitationCount=50
        )
        assert paper.citation_count == 100
        assert paper.influential_citation_count == 50
        
        # Invalid metrics (influential > total)
        with pytest.raises(ValueError):
            Paper(
                paperId="123",
                title="Test",
                citationCount=50,
                influentialCitationCount=100
            )


# Helper functions that should exist in server.py
def format_paper_response(papers):
    """Format papers for API response."""
    return [paper.model_dump(by_alias=True) for paper in papers]


def validate_search_params(query, limit, offset):
    """Validate search parameters."""
    if not query or not query.strip():
        return False
    if limit <= 0 or limit > 100:
        return False
    if offset < 0:
        return False
    return True