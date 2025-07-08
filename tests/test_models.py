"""Unit tests for domain models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from semantic_scholar_mcp.domain_models import (
    Author,
    Citation,
    Paper,
    Reference,
    SearchFilters,
    SearchQuery,
    SearchResult,
)


class TestPaper:
    """Tests for Paper model."""

    def test_paper_creation(self):
        """Test creating a valid paper."""
        paper = Paper(
            paperId="123",
            title="Test Paper",
            abstract="This is a test abstract.",
            year=2023,
            venue="Test Conference"
        )

        assert paper.paper_id == "123"
        assert paper.title == "Test Paper"
        assert paper.abstract == "This is a test abstract."
        assert paper.year == 2023
        assert paper.venue == "Test Conference"

    def test_paper_without_optional_fields(self):
        """Test creating paper with only required fields."""
        paper = Paper(
            paperId="123",
            title="Test Paper"
        )

        assert paper.paper_id == "123"
        assert paper.title == "Test Paper"
        assert paper.abstract is None
        assert paper.year is None
        assert paper.venue is None

    def test_paper_title_validation(self):
        """Test paper title validation."""
        # Empty title should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(
                paperId="123",
                title=""
            )

        assert "Paper title cannot be empty" in str(exc_info.value)

    def test_paper_year_validation(self):
        """Test paper year validation."""
        current_year = datetime.now(tz=timezone.utc).year

        # Future year should fail
        with pytest.raises(ValidationError) as exc_info:
            Paper(
                paperId="123",
                title="Future Paper",
                year=current_year + 10
            )

        assert "Invalid publication year" in str(exc_info.value)

        # Valid current year should pass
        paper = Paper(
            paperId="123",
            title="Current Paper",
            year=current_year
        )
        assert paper.year == current_year


class TestAuthor:
    """Tests for Author model."""

    def test_author_creation(self):
        """Test creating a valid author."""
        author = Author(
            authorId="1234567",
            name="John Doe",
            affiliations=["University of Example"],
            hIndex=15,
            citationCount=250
        )

        assert author.author_id == "1234567"
        assert author.name == "John Doe"
        assert author.affiliations == ["University of Example"]
        assert author.h_index == 15
        assert author.citation_count == 250

    def test_author_without_optional_fields(self):
        """Test creating author with only required fields."""
        author = Author(name="Jane Smith")

        assert author.name == "Jane Smith"
        assert author.author_id is None
        assert author.affiliations == []
        assert author.h_index is None
        assert author.citation_count is None

    def test_author_name_validation(self):
        """Test author name validation."""
        # Empty name should fail
        with pytest.raises(ValidationError) as exc_info:
            Author(name="")

        assert "Author name cannot be empty" in str(exc_info.value)


class TestSearchQuery:
    """Tests for SearchQuery model."""

    def test_search_query_creation(self):
        """Test creating a valid search query."""
        query = SearchQuery(
            query="machine learning",
            limit=20,
            offset=10
        )

        assert query.query == "machine learning"
        assert query.limit == 20
        assert query.offset == 10

    def test_search_query_defaults(self):
        """Test search query default values."""
        query = SearchQuery(query="test")

        assert query.query == "test"
        assert query.limit == 10
        assert query.offset == 0

    def test_search_query_validation(self):
        """Test search query validation."""
        # Empty query should fail
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(query="")

        assert "Search query cannot be empty" in str(exc_info.value)

        # Limit too high should fail
        with pytest.raises(ValidationError) as exc_info:
            SearchQuery(query="test", limit=101)

        assert "less than or equal to 100" in str(exc_info.value)


class TestSearchResult:
    """Tests for SearchResult model."""

    def test_search_result_creation(self):
        """Test creating a valid search result."""
        papers = [
            Paper(paperId="1", title="Paper 1"),
            Paper(paperId="2", title="Paper 2")
        ]

        result = SearchResult(
            items=papers,
            total=2,
            offset=0,
            has_more=False
        )

        assert len(result.items) == 2
        assert result.total == 2
        assert result.offset == 0
        assert result.has_more is False


class TestSearchFilters:
    """Tests for SearchFilters model."""

    def test_search_filters_creation(self):
        """Test creating search filters."""
        filters = SearchFilters(
            year=2024,
            fieldsOfStudy=["Computer Science", "Mathematics"],
            minCitationCount=5
        )

        assert filters.year == 2024
        assert len(filters.fields_of_study) == 2
        assert filters.min_citation_count == 5

    def test_search_filters_year_range(self):
        """Test search filters with year range."""
        # Invalid year range (start > end)
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(yearRange=(2024, 2020))

        expected_msg = "Year range start must be before end"
        assert expected_msg in str(exc_info.value)

        # Valid year range
        filters = SearchFilters(yearRange=(2020, 2024))
        assert filters.year_range == (2020, 2024)


class TestCitation:
    """Tests for Citation model."""

    def test_citation_creation(self):
        """Test creating a citation."""
        citation = Citation(
            paperId="cited123",
            title="Cited Paper",
            year=2023,
            isInfluential=True,
            intents=["background"]
        )

        assert citation.paper_id == "cited123"
        assert citation.is_influential is True


class TestReference:
    """Tests for Reference model."""

    def test_reference_creation(self):
        """Test creating a reference."""
        reference = Reference(
            paperId="ref123",
            title="Reference Paper",
            year=2022,
            authors=[Author(name="Reference Author")],
            citationCount=25
        )

        assert reference.paper_id == "ref123"
        assert reference.year == 2022

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
