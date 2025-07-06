"""Integration tests with real Semantic Scholar API."""

import asyncio
import os

import pytest

from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from semantic_scholar_mcp.models import (
    SearchQuery, PaperId, AuthorId,
    Paper, Author, PaginatedResponse
)
from core.exceptions import RateLimitError, APIError


@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests that use the real Semantic Scholar API."""
    
    @pytest.mark.asyncio
    async def test_search_papers_real(self, real_api_client):
        """Test real paper search."""
        # Search for well-known paper
        query = SearchQuery(
            query="attention is all you need",
            limit=5
        )
        
        result = await real_api_client.search_papers(query)
        
        # Verify response structure
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) <= 5
        assert result.total > 0
        
        # Verify paper structure
        if result.items:
            paper = result.items[0]
            assert isinstance(paper, Paper)
            assert paper.paper_id
            assert paper.title
            assert paper.citation_count >= 0
            
            # The famous "Attention is All You Need" paper should appear
            titles = [p.title.lower() for p in result.items]
            assert any("attention" in title for title in titles)
    
    @pytest.mark.asyncio
    async def test_get_specific_paper_real(self, real_api_client):
        """Test retrieving a specific well-known paper."""
        # Paper ID for "Attention Is All You Need" by Vaswani et al.
        paper_id = PaperId("204e3073870fae3d05bcbc2f6a8e263d9b72e776")
        
        paper = await real_api_client.get_paper(paper_id)
        
        # Verify paper details
        assert isinstance(paper, Paper)
        assert paper.paper_id == paper_id
        assert "attention" in paper.title.lower()
        assert paper.year == 2017
        assert len(paper.authors) > 0
        assert paper.citation_count > 50000  # Very highly cited
        
        # Check author names (should include Vaswani)
        author_names = [a.name for a in paper.authors]
        assert any("Vaswani" in name for name in author_names)
    
    @pytest.mark.asyncio
    async def test_get_paper_citations_real(self, real_api_client):
        """Test retrieving citations for a paper."""
        # Use a moderately cited paper to avoid huge responses
        paper_id = PaperId("204e3073870fae3d05bcbc2f6a8e263d9b72e776")
        
        citations = await real_api_client.get_paper_citations(
            paper_id,
            limit=10
        )
        
        # Verify citations
        assert isinstance(citations, list)
        assert len(citations) <= 10
        
        if citations:
            citation = citations[0]
            assert citation.paper_id
            assert citation.title
            assert isinstance(citation.is_influential, bool)
    
    @pytest.mark.asyncio
    async def test_search_authors_real(self, real_api_client):
        """Test author search with real API."""
        # Search for well-known researcher
        result = await real_api_client.search_authors(
            query="Geoffrey Hinton",
            limit=5
        )
        
        # Verify response
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) > 0
        
        # Should find Geoffrey Hinton
        author_names = [a.name for a in result.items]
        assert any("Hinton" in name for name in author_names)
        
        # Check first result
        if result.items:
            author = result.items[0]
            assert isinstance(author, Author)
            assert author.name
            if author.h_index:
                assert author.h_index > 0
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, real_api_client):
        """Test rate limiting behavior (careful with this test)."""
        # Make a reasonable number of requests
        query = SearchQuery(query="machine learning", limit=1)
        
        # Make 5 requests in quick succession
        tasks = []
        for i in range(5):
            tasks.append(real_api_client.search_papers(query))
        
        # All should succeed due to rate limiter
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        errors = [r for r in results if isinstance(r, Exception)]
        successful = [r for r in results if not isinstance(r, Exception)]
        
        # All should succeed (rate limiter prevents hitting API limit)
        assert len(successful) == 5
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_get_recommendations_real(self, real_api_client):
        """Test paper recommendations with real API."""
        # Use a well-known paper
        paper_id = PaperId("204e3073870fae3d05bcbc2f6a8e263d9b72e776")
        
        recommendations = await real_api_client.get_recommendations(
            paper_id,
            limit=5
        )
        
        # Verify recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5
        
        if recommendations:
            # Should recommend related transformer/attention papers
            titles = [p.title.lower() for p in recommendations]
            # At least some should be about transformers, attention, or NLP
            relevant_keywords = ["transformer", "attention", "bert", "language model"]
            assert any(
                any(keyword in title for keyword in relevant_keywords)
                for title in titles
            )
    
    @pytest.mark.asyncio
    async def test_batch_get_papers_real(self, real_api_client):
        """Test batch paper retrieval with real API."""
        # Use known paper IDs
        paper_ids = [
            PaperId("204e3073870fae3d05bcbc2f6a8e263d9b72e776"),  # Attention paper
            PaperId("df2b0e26d0599ce3e70df8a9da02e51594e0e992"),  # BERT paper
        ]
        
        papers = await real_api_client.batch_get_papers(paper_ids)
        
        # Verify results
        assert len(papers) == 2
        assert all(isinstance(p, Paper) for p in papers)
        
        # Check we got the right papers
        retrieved_ids = [p.paper_id for p in papers]
        assert set(retrieved_ids) == set(paper_ids)
        
        # Verify paper titles
        titles = [p.title.lower() for p in papers]
        assert any("attention" in title for title in titles)
        assert any("bert" in title for title in titles)
    
    @pytest.mark.asyncio
    async def test_error_handling_real(self, real_api_client):
        """Test error handling with real API."""
        # Test with non-existent paper ID
        with pytest.raises(APIError) as exc_info:
            await real_api_client.get_paper(PaperId("nonexistent123456"))
        
        assert exc_info.value.status_code == 404
        
        # Test with invalid search
        with pytest.raises(Exception):  # Could be various errors
            await real_api_client.search_papers(
                SearchQuery(query="", limit=10)  # Empty query
            )
    
    @pytest.mark.asyncio
    async def test_field_filtering_real(self, real_api_client):
        """Test field filtering in real API calls."""
        # Search with specific fields
        query = SearchQuery(
            query="deep learning",
            limit=3,
            fields_of_study=["Computer Science"]
        )
        
        result = await real_api_client.search_papers(
            query,
            fields=["paperId", "title", "year", "citationCount"]
        )
        
        # Verify only requested fields are populated
        if result.items:
            paper = result.items[0]
            assert paper.paper_id
            assert paper.title
            assert paper.year
            assert paper.citation_count is not None
            # Abstract might not be included if not requested
            # (depends on API implementation)
    
    @pytest.mark.asyncio
    async def test_health_check_real(self, real_api_client):
        """Test health check with real API."""
        health = await real_api_client.health_check()
        
        # Verify health check response
        assert health["status"] in ["healthy", "degraded"]
        assert health["api_accessible"] is True
        assert isinstance(health["rate_limit_remaining"], int)
        assert health["rate_limit_remaining"] >= 0
        assert "version" in health
    
    @pytest.mark.asyncio
    async def test_mcp_server_tools_real(self, real_api_client):
        """Test MCP server tools with real API."""
        # Import server tools
        from semantic_scholar_mcp.server import (
            search_papers, get_paper, health_check,
            get_recommendations, batch_get_papers
        )
        
        # Test search_papers tool
        search_result = await search_papers(
            query="transformer neural network",
            limit=3
        )
        assert search_result["success"] is True
        assert len(search_result["data"]["papers"]) <= 3
        
        # Test get_paper tool
        paper_result = await get_paper(
            paper_id="204e3073870fae3d05bcbc2f6a8e263d9b72e776"
        )
        assert paper_result["success"] is True
        assert "title" in paper_result["data"]
        
        # Test health_check tool
        health_result = await health_check()
        assert health_result["success"] is True
        assert "status" in health_result["data"]
        
        # Test get_recommendations tool
        rec_result = await get_recommendations(
            paper_id="204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            limit=3
        )
        assert rec_result["success"] is True
        assert len(rec_result["data"]["recommendations"]) <= 3
        
        # Test batch_get_papers tool
        batch_result = await batch_get_papers(
            paper_ids=[
                "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
                "df2b0e26d0599ce3e70df8a9da02e51594e0e992"
            ]
        )
        assert batch_result["success"] is True
        assert len(batch_result["data"]["papers"]) == 2