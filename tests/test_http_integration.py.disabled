"""Integration tests with HTTP responses mocked but realistic data."""

import json
import sys
from pathlib import Path

import pytest
import respx
from httpx import Response

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from core.config import SemanticScholarConfig


@pytest.mark.asyncio
class TestHTTPIntegration:
    """Integration tests with realistic HTTP responses."""

    @pytest.fixture
    async def client(self):
        """Create client for testing."""
        config = SemanticScholarConfig()
        client = SemanticScholarClient(config=config)
        async with client:
            yield client

    @respx.mock
    async def test_search_papers_http_integration(self, client):
        """Test search with realistic HTTP response."""
        # Mock realistic API response
        mock_response = {
            "total": 1,
            "offset": 0,
            "data": [
                {
                    "paperId": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
                    "title": "Attention Is All You Need",
                    "abstract": "The dominant sequence transduction models...",
                    "year": 2017,
                    "venue": "NIPS",
                    "citationCount": 50000,
                    "influentialCitationCount": 8000,
                    "authors": [
                        {
                            "authorId": "1699956",
                            "name": "Ashish Vaswani"
                        },
                        {
                            "authorId": "1710503", 
                            "name": "Noam M. Shazeer"
                        }
                    ],
                    "fieldsOfStudy": ["Computer Science"],
                    "publicationTypes": ["JournalArticle"],
                    "url": "https://arxiv.org/abs/1706.03762"
                }
            ]
        }
        
        # Mock the HTTP request
        respx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search"
        ).mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Make the request
        result = await client.search_papers(query="attention", limit=1)
        
        # Verify the actual data processing worked
        assert result.total == 1
        assert len(result.items) == 1
        
        paper = result.items[0]
        assert paper.title == "Attention Is All You Need"
        assert paper.year == 2017
        assert paper.citation_count == 50000
        assert len(paper.authors) == 2
        assert paper.authors[0].name == "Ashish Vaswani"

    @respx.mock
    async def test_get_paper_http_integration(self, client):
        """Test get paper with realistic HTTP response."""
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"
        
        mock_response = {
            "paperId": paper_id,
            "title": "Attention Is All You Need",
            "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
            "year": 2017,
            "venue": "NIPS",
            "citationCount": 50000,
            "referenceCount": 42,
            "influentialCitationCount": 8000,
            "authors": [
                {
                    "authorId": "1699956",
                    "name": "Ashish Vaswani",
                    "affiliations": ["Google Research"]
                }
            ],
            "fieldsOfStudy": ["Computer Science", "Mathematics"],
            "publicationTypes": ["JournalArticle"],
            "url": "https://arxiv.org/abs/1706.03762",
            "publicationDate": "2017-06-12",
            "externalIds": {
                "ArXiv": "1706.03762",
                "DBLP": "journals/corr/VaswaniSPUJGKP17"
            }
        }
        
        respx.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}"
        ).mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Test the actual request
        paper = await client.get_paper(paper_id=paper_id)
        
        # Verify data processing
        assert paper.paper_id == paper_id
        assert paper.title == "Attention Is All You Need"
        assert paper.citation_count == 50000
        assert paper.reference_count == 42
        assert len(paper.authors) == 1
        assert paper.authors[0].affiliations == ["Google Research"]

    @respx.mock
    async def test_error_handling_http_integration(self, client):
        """Test error handling with real HTTP error responses."""
        # Mock 404 response
        respx.get(
            "https://api.semanticscholar.org/graph/v1/paper/invalid-id"
        ).mock(
            return_value=Response(404, json={"error": "Paper not found"})
        )
        
        # Should raise appropriate exception
        with pytest.raises(Exception):
            await client.get_paper(paper_id="invalid-id")

    @respx.mock
    async def test_rate_limiting_http_integration(self, client):
        """Test rate limiting with HTTP 429 response."""
        # Mock rate limit response
        respx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search"
        ).mock(
            return_value=Response(429, json={"error": "Rate limit exceeded"})
        )
        
        # Should handle rate limiting appropriately
        with pytest.raises(Exception):
            await client.search_papers(query="test")

    @respx.mock
    async def test_malformed_response_handling(self, client):
        """Test handling of malformed API responses."""
        # Mock malformed response (missing required fields)
        mock_response = {
            "total": 1,
            "data": [
                {
                    # Missing paperId and title
                    "year": 2020
                }
            ]
        }
        
        respx.get(
            "https://api.semanticscholar.org/graph/v1/paper/search"
        ).mock(
            return_value=Response(200, json=mock_response)
        )
        
        # Should handle validation errors gracefully
        with pytest.raises(Exception):  # Pydantic validation error
            await client.search_papers(query="test")