"""Unit tests for data models."""

from datetime import datetime
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from semantic_scholar_mcp.domain_models import (
    Paper, Author, Citation, Reference,
    PaperId, AuthorId, SearchQuery, SearchFilters
)
from semantic_scholar_mcp.base_models import (
    PaginatedResponse, ApiResponse, CacheableModel
)


class TestPaperModel:
    """Test Paper model."""
    
    def test_paper_creation_minimal(self):
        """Test creating a paper with minimal fields."""
        paper = Paper(
            paperId="test123",
            title="Test Paper",
            authors=[],
            citationCount=0,
            referenceCount=0,
            influentialCitationCount=0,
            externalIds={},
            fieldsOfStudy=[],
            isOpenAccess=False
        )
        
        assert paper.paper_id == "test123"
        assert paper.title == "Test Paper"
        assert paper.abstract is None
        assert paper.year is None
        assert paper.venue is None
    
    def test_paper_creation_full(self, sample_paper: Paper):
        """Test creating a paper with all fields."""
        assert sample_paper.paper_id == "test123"
        assert sample_paper.title == "Test Paper: A Comprehensive Study"
        assert sample_paper.abstract == "This is a test abstract for unit testing."
        assert sample_paper.year == 2024
        assert sample_paper.venue == "Test Conference"
        assert len(sample_paper.authors) == 2
        assert sample_paper.citation_count == 42
        assert sample_paper.is_open_access is True
    
    def test_paper_title_validation(self):
        """Test paper title validation."""
        # Empty title should fail
        with pytest.raises(ValidationError):
            Paper(
                paperId="test",
                title="",  # Empty title
                authors=[],
                citation_count=0,
                reference_count=0,
                influential_citation_count=0,
                external_ids={},
                fields_of_study=[],
                is_open_access=False,
                created_at=datetime.utcnow()
            )
    
    def test_paper_year_validation(self):
        """Test paper year validation."""
        # Future year should fail
        with pytest.raises(ValidationError):
            Paper(
                paperId="test",
                title="Test",
                year=2050,  # Future year
                authors=[],
                citation_count=0,
                reference_count=0,
                influential_citation_count=0,
                external_ids={},
                fields_of_study=[],
                is_open_access=False,
                created_at=datetime.utcnow()
            )
        
        # Very old year should fail
        with pytest.raises(ValidationError):
            Paper(
                paperId="test",
                title="Test",
                year=1799,  # Too old
                authors=[],
                citation_count=0,
                reference_count=0,
                influential_citation_count=0,
                external_ids={},
                fields_of_study=[],
                is_open_access=False,
                created_at=datetime.utcnow()
            )
    
    def test_paper_metrics_validation(self):
        """Test paper metrics validation."""
        # Negative citation count should fail
        with pytest.raises(ValidationError):
            Paper(
                paperId="test",
                title="Test",
                authors=[],
                citationCount=-1,  # Negative
                referenceCount=0,
                influentialCitationCount=0,
                externalIds={},
                fieldsOfStudy=[],
                isOpenAccess=False
            )
        
        # Influential citations > total citations should fail
        with pytest.raises(ValidationError):
            Paper(
                paperId="test",
                title="Test",
                authors=[],
                citationCount=10,
                referenceCount=0,
                influentialCitationCount=20,  # More than total
                externalIds={},
                fieldsOfStudy=[],
                isOpenAccess=False
            )
    
    def test_paper_cache_key_generation(self, sample_paper: Paper):
        """Test cache key generation for paper."""
        cache_key = sample_paper.generate_cache_key()
        assert cache_key == "paper:test123"
        assert sample_paper.cache_ttl == 3600  # Default TTL


class TestAuthorModel:
    """Test Author model."""
    
    def test_author_creation_minimal(self):
        """Test creating an author with minimal fields."""
        author = Author(name="Test Author")
        
        assert author.name == "Test Author"
        assert author.author_id is None
        assert author.aliases == []
        assert author.affiliations == []
        assert author.homepage is None
        assert author.citation_count is None
        assert author.h_index is None
        assert author.paper_count is None
    
    def test_author_creation_full(self, sample_author: Author):
        """Test creating an author with all fields."""
        assert sample_author.author_id == "author123"
        assert sample_author.name == "Dr. Test Author"
        assert len(sample_author.aliases) == 2
        assert len(sample_author.affiliations) == 2
        assert sample_author.homepage == "https://example.com/~testauthor"
        assert sample_author.citation_count == 1000
        assert sample_author.h_index == 25
        assert sample_author.paper_count == 50
    
    def test_author_name_validation(self):
        """Test author name validation."""
        # Empty name should fail
        with pytest.raises(ValidationError):
            Author(name="")
        
        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            Author(name="   ")


class TestCitationModel:
    """Test Citation model."""
    
    def test_citation_creation(self, sample_citation: Citation):
        """Test creating a citation."""
        assert sample_citation.paper_id == "citing123"
        assert sample_citation.title == "Citing Paper Title"
        assert sample_citation.year == 2024
        assert len(sample_citation.authors) == 1
        assert sample_citation.venue == "Citation Venue"
        assert sample_citation.citation_count == 10
        assert sample_citation.is_influential is True
        assert len(sample_citation.contexts) == 1
        assert len(sample_citation.intents) == 1
    
    def test_citation_minimal(self):
        """Test creating citation with minimal fields."""
        citation = Citation(
            paperId="cite123",
            title="Citation",
            authors=[],
            citationCount=0,
            isInfluential=False,
            contexts=[],
            intents=[]
        )
        
        assert citation.paper_id == "cite123"
        assert citation.year is None
        assert citation.venue is None


class TestSearchQuery:
    """Test SearchQuery model."""
    
    def test_search_query_minimal(self):
        """Test creating search query with minimal fields."""
        query = SearchQuery(query="test")
        
        assert query.query == "test"
        assert query.limit == 10  # Default
        assert query.offset == 0  # Default
        assert query.filters is None
        assert query.fields is None
        assert query.sort is None
    
    def test_search_query_full(self, sample_search_query: SearchQuery):
        """Test creating search query with all fields."""
        assert sample_search_query.query == "machine learning"
        assert sample_search_query.limit == 10
        assert sample_search_query.offset == 0
        assert sample_search_query.filters is not None
        assert sample_search_query.filters.year_range == (2020, 2024)
        assert sample_search_query.filters.fields_of_study == ["Computer Science"]
    
    def test_search_query_validation(self):
        """Test search query validation."""
        # Empty query should fail
        with pytest.raises(ValidationError):
            SearchQuery(query="")
        
        # Invalid limit should fail
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=0)
        
        with pytest.raises(ValidationError):
            SearchQuery(query="test", limit=101)
        
        # Negative offset should fail
        with pytest.raises(ValidationError):
            SearchQuery(query="test", offset=-1)
    
    def test_search_filters(self):
        """Test SearchFilters model."""
        filters = SearchFilters(
            year=2023,
            yearRange=(2020, 2024),
            venues=["NeurIPS"],
            fieldsOfStudy=["Computer Science", "Mathematics"],
            minCitationCount=10,
            openAccessOnly=True
        )
        
        assert filters.year == 2023
        assert filters.year_range == (2020, 2024)
        assert filters.venues == ["NeurIPS"]
        assert len(filters.fields_of_study) == 2
        assert filters.min_citation_count == 10
        assert filters.open_access_only is True
    
    def test_year_filter_parsing(self):
        """Test year filter string parsing."""
        # With year in filters
        query = SearchQuery(
            query="test", 
            filters=SearchFilters(year=2023)
        )
        assert query.filters.year == 2023
        
        # With year range in filters
        query = SearchQuery(
            query="test", 
            filters=SearchFilters(yearRange=(2020, 2024))
        )
        assert query.filters.year_range == (2020, 2024)


class TestApiResponse:
    """Test ApiResponse model."""
    
    def test_success_response(self, sample_paper: Paper):
        """Test creating a success response."""
        response = ApiResponse.success_response(
            data=sample_paper,
            metadata={"source": "cache"}
        )
        
        assert response.success is True
        assert response.data == sample_paper
        assert response.error is None
        assert response.metadata == {"source": "cache"}
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response(self):
        """Test creating an error response."""
        response = ApiResponse.error_response(
            error_code="NOT_FOUND",
            error_message="Paper not found",
            details={"paper_id": "invalid123"}
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error == {
            "code": "NOT_FOUND",
            "message": "Paper not found",
            "details": {"paper_id": "invalid123"}
        }
        assert isinstance(response.timestamp, datetime)


class TestPaginatedResponse:
    """Test PaginatedResponse model."""
    
    def test_paginated_response(self, sample_papers):
        """Test creating a paginated response."""
        response = PaginatedResponse(
            items=sample_papers,
            total=100,
            offset=0,
            limit=5
        )
        
        assert len(response.items) == 5
        assert response.total == 100
        assert response.offset == 0
        assert response.limit == 5
        assert response.has_more is True
    
    def test_paginated_response_no_more(self, sample_papers):
        """Test paginated response with no more items."""
        response = PaginatedResponse(
            items=sample_papers,
            total=5,
            offset=0,
            limit=10
        )
        
        assert response.has_more is False
    
    def test_paginated_response_middle_page(self, sample_papers):
        """Test paginated response for middle page."""
        response = PaginatedResponse(
            items=sample_papers,
            total=100,
            offset=50,
            limit=5
        )
        
        assert response.has_more is True
        # Check if we're not on the last page
        assert response.offset + response.limit < response.total


class TestTypeAliases:
    """Test custom type aliases."""
    
    def test_paper_id(self):
        """Test PaperId type."""
        paper_id = PaperId("abc123")
        assert paper_id == "abc123"
        assert isinstance(paper_id, str)
    
    def test_author_id(self):
        """Test AuthorId type."""
        author_id = AuthorId("123456")
        assert author_id == "123456"
        assert isinstance(author_id, str)


class TestCacheableModel:
    """Test CacheableModel functionality."""
    
    def test_cacheable_paper(self, sample_paper: Paper):
        """Test that Paper inherits from CacheableModel."""
        assert isinstance(sample_paper, CacheableModel)
        assert hasattr(sample_paper, 'cache_key')
        assert hasattr(sample_paper, 'cache_ttl')
        assert hasattr(sample_paper, 'generate_cache_key')
        
        # Test cache key generation
        cache_key = sample_paper.generate_cache_key()
        assert cache_key == f"paper:{sample_paper.paper_id}"
        
        # Test default TTL
        assert sample_paper.cache_ttl == 3600