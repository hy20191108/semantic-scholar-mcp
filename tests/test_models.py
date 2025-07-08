"""Unit tests for domain models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from semantic_scholar_mcp.domain_models import (
    Paper, Author, Citation, Reference, SearchQuery, SearchFilters
)


class TestPaperModel:
    """Test cases for Paper model."""

    def test_paper_creation_minimal(self):
        """Test creating paper with minimal fields."""
        paper = Paper(
            paper_id="123",
            title="Test Paper"
        )
        
        assert paper.paper_id == "123"
        assert paper.title == "Test Paper"
        assert paper.citation_count == 0
        assert paper.authors == []

    def test_paper_creation_full(self, mock_paper_data):
        """Test creating paper with all fields."""
        paper = Paper(**mock_paper_data)
        
        assert paper.paper_id == "test123"
        assert paper.title == "Test Paper: A Comprehensive Study"
        assert paper.year == 2024
        assert paper.citation_count == 42
        assert len(paper.authors) == 2
        assert paper.fields_of_study == ["Computer Science", "Machine Learning"]

    def test_paper_title_validation(self):
        """Test paper title validation."""
        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(paper_id="123", title="")
        
        assert "Title cannot be empty" in str(exc_info.value)
        
        # Whitespace-only title should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(paper_id="123", title="   ")
        
        assert "Title cannot be empty" in str(exc_info.value)

    def test_paper_year_validation(self):
        """Test paper year validation."""
        current_year = datetime.now().year
        
        # Future year should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(
                paper_id="123",
                title="Test",
                year=current_year + 2
            )
        
        assert "Year cannot be in the future" in str(exc_info.value)
        
        # Very old year should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(
                paper_id="123",
                title="Test",
                year=1799
            )
        
        assert "Year must be 1800 or later" in str(exc_info.value)

    def test_paper_metrics_validation(self):
        """Test paper metrics validation."""
        # Negative citation count should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(
                paper_id="123",
                title="Test",
                citation_count=-1
            )
        
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_paper_cache_key_generation(self):
        """Test cache key generation."""
        paper = Paper(paper_id="test123", title="Test Paper")
        cache_key = paper.generate_cache_key()
        
        assert cache_key == "paper:test123"


class TestAuthorModel:
    """Test cases for Author model."""

    def test_author_creation_minimal(self):
        """Test creating author with minimal fields."""
        author = Author(name="John Doe")
        
        assert author.name == "John Doe"
        assert author.author_id is None
        assert author.aliases == []
        assert author.paper_count == 0

    def test_author_creation_full(self, mock_author_data):
        """Test creating author with all fields."""
        author = Author(**mock_author_data)
        
        assert author.author_id == "1234567"
        assert author.name == "Dr. Test Author"
        assert len(author.aliases) == 2
        assert author.h_index == 35

    def test_author_name_validation(self):
        """Test author name validation."""
        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            Author(name="")
        
        assert "Name cannot be empty" in str(exc_info.value)


class TestSearchQuery:
    """Test cases for SearchQuery model."""

    def test_search_query_minimal(self):
        """Test creating search query with minimal fields."""
        query = SearchQuery(query="machine learning")
        
        assert query.query == "machine learning"
        assert query.limit == 10
        assert query.offset == 0
        assert query.filters is None

    def test_search_query_with_filters(self):
        """Test creating search query with filters."""
        filters = SearchFilters(
            year=2024,
            fields_of_study=["Computer Science"],
            min_citation_count=10
        )
        
        query = SearchQuery(
            query="deep learning",
            limit=20,
            offset=10,
            filters=filters
        )
        
        assert query.query == "deep learning"
        assert query.limit == 20
        assert query.filters.year == 2024
        assert query.filters.min_citation_count == 10

    def test_search_query_validation(self):
        """Test search query validation."""
        # Empty query should fail
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(query="")
        
        assert "Query cannot be empty" in str(exc_info.value)
        
        # Invalid limit
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(query="test", limit=0)
        
        assert "greater than or equal to 1" in str(exc_info.value)
        
        # Limit too high
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(query="test", limit=101)
        
        assert "less than or equal to 100" in str(exc_info.value)


class TestSearchFilters:
    """Test cases for SearchFilters model."""

    def test_search_filters_creation(self):
        """Test creating search filters."""
        filters = SearchFilters(
            year=2024,
            fields_of_study=["AI", "ML"],
            open_access_only=True,
            min_citation_count=5
        )
        
        assert filters.year == 2024
        assert len(filters.fields_of_study) == 2
        assert filters.open_access_only is True
        assert filters.min_citation_count == 5

    def test_year_range_validation(self):
        """Test year range validation."""
        # Invalid year range (start > end)
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(year_range=(2024, 2020))
        
        assert "Start year must be less than or equal to end year" in str(exc_info.value)
        
        # Valid year range
        filters = SearchFilters(year_range=(2020, 2024))
        assert filters.year_range == (2020, 2024)


class TestCitationModel:
    """Test cases for Citation model."""

    def test_citation_creation(self):
        """Test creating citation."""
        citation = Citation(
            paper_id="cited123",
            title="Cited Paper",
            year=2023,
            authors=[Author(name="Author 1")],
            citation_count=15,
            is_influential=True,
            contexts=["This work builds on [1]..."],
            intents=["background"]
        )
        
        assert citation.paper_id == "cited123"
        assert citation.is_influential is True
        assert len(citation.contexts) == 1
        assert citation.intents == ["background"]


class TestReferenceModel:
    """Test cases for Reference model."""

    def test_reference_creation(self):
        """Test creating reference."""
        reference = Reference(
            paper_id="ref123",
            title="Referenced Paper",
            year=2022,
            authors=[Author(name="Ref Author")],
            venue="Conference 2022",
            citation_count=25
        )
        
        assert reference.paper_id == "ref123"
        assert reference.year == 2022
        assert reference.venue == "Conference 2022"

    def test_reference_without_paper_id(self):
        """Test creating reference without paper ID."""
        # Some references might not have paper IDs
        reference = Reference(
            title="Old Reference",
            year=1995,
            authors=[Author(name="Old Author")]
        )
        
        assert reference.paper_id is None
        assert reference.title == "Old Reference"