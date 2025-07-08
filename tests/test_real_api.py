"""Real API integration tests (requires internet connection)."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from semantic_scholar_mcp.domain_models import Paper
from core.config import SemanticScholarConfig


@pytest.mark.integration
class TestRealAPI:
    """Integration tests using real Semantic Scholar API."""

    @pytest.fixture
    async def client(self):
        """Create a real API client."""
        # Skip if no API key available
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        
        # Create config
        config = SemanticScholarConfig(api_key=api_key)
        client = SemanticScholarClient(config=config)
        
        async with client:
            yield client

    @pytest.mark.asyncio
    async def test_search_real_papers(self, client):
        """Test searching for real papers."""
        # Search for a well-known paper topic
        response = await client.search_papers(
            query="attention is all you need",
            limit=5
        )
        
        # Verify we get real results
        assert response.total > 0
        assert len(response.items) > 0
        
        # Verify paper structure
        paper = response.items[0]
        assert isinstance(paper, Paper)
        assert paper.title is not None
        assert paper.paper_id is not None
        
        # Should find the famous "Attention Is All You Need" paper
        titles = [p.title.lower() for p in response.items]
        assert any("attention" in title and "all you need" in title for title in titles)

    @pytest.mark.asyncio
    async def test_get_real_paper(self, client):
        """Test getting a specific real paper."""
        # Use a well-known paper ID (Attention Is All You Need)
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"
        
        paper = await client.get_paper(paper_id=paper_id)
        
        # Verify paper details
        assert paper.paper_id == paper_id
        assert "attention" in paper.title.lower()
        assert paper.year == 2017
        assert len(paper.authors) > 0
        assert paper.citation_count > 1000  # Very famous paper

    @pytest.mark.asyncio
    async def test_get_paper_citations(self, client):
        """Test getting citations for a real paper."""
        # Use the same famous paper
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"
        
        citations = await client.get_paper_citations(paper_id=paper_id, limit=10)
        
        # Should have many citations
        assert citations.total > 100
        assert len(citations.data) <= 10
        
        # Verify citation structure
        citation = citations.data[0]
        assert citation.paper_id is not None
        assert citation.title is not None

    @pytest.mark.asyncio
    async def test_search_authors(self, client):
        """Test searching for real authors."""
        response = await client.search_authors(query="Yoshua Bengio", limit=5)
        
        assert response.total > 0
        author = response.data[0]
        assert "bengio" in author.name.lower()
        assert author.paper_count > 100  # Prolific researcher

    @pytest.mark.asyncio
    async def test_error_handling_invalid_paper_id(self, client):
        """Test error handling with invalid paper ID."""
        with pytest.raises(Exception):  # Should raise an appropriate exception
            await client.get_paper(paper_id="invalid-paper-id-123")

    @pytest.mark.asyncio 
    async def test_rate_limiting_compliance(self, client):
        """Test that we respect rate limits."""
        import time
        
        start_time = time.time()
        
        # Make multiple requests
        for i in range(3):
            await client.search_papers(query=f"machine learning {i}", limit=1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should take at least 2 seconds due to rate limiting (1 req/sec)
        assert duration >= 2.0, f"Requests completed too quickly: {duration}s"