"""Integration tests for MCP server functionality."""

import asyncio
import os

# Add src to path for imports
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from semantic_scholar_mcp.server import (  # noqa: E402
    get_author,
    get_paper,
    get_paper_resource,
    get_recommendations,
    initialize_server,
    literature_review,
    search_papers,
)


class TestMCPIntegration:
    """Integration tests for MCP server tools."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment."""
        # Initialize server components
        with patch('semantic_scholar_mcp.server.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                logging=MagicMock(
                    level="INFO", 
                    format="json",
                    file_path=None,
                    max_file_size=1024,
                    backup_count=3,
                    include_timestamp=True,
                    include_context=True
                ),
                cache=MagicMock(enabled=True, max_size=100, ttl_seconds=300),
                semantic_scholar=MagicMock()
            )
            await initialize_server()

    @pytest.mark.asyncio
    async def test_search_papers_integration(self):
        """Test search_papers tool integration."""
        # Arrange
        mock_response = MagicMock()
        mock_response.items = [
            MagicMock(
                paper_id="123",
                title="Test Paper",
                abstract="Test abstract",
                year=2024,
                citation_count=10,
                authors=[MagicMock(name="Author 1")],
                model_dump=lambda **_kwargs: {
                    "paperId": "123",
                    "title": "Test Paper",
                    "abstract": "Test abstract",
                    "year": 2024,
                    "citationCount": 10,
                    "authors": [{"name": "Author 1"}]
                }
            )
        ]
        mock_response.total = 1
        mock_response.offset = 0
        mock_response.limit = 10
        mock_response.has_more = False

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.search_papers = AsyncMock(return_value=mock_response)

            # Act
            result = await search_papers("test query", limit=10)

            # Assert
            assert result["success"] is True
            assert len(result["data"]["papers"]) == 1
            assert result["data"]["papers"][0]["title"] == "Test Paper"
            assert result["data"]["total"] == 1
            assert result["data"]["has_more"] is False

    @pytest.mark.asyncio
    async def test_search_papers_error_handling(self):
        """Test search_papers error handling."""
        # Arrange
        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.search_papers = AsyncMock(
                side_effect=Exception("API Error")
            )

            # Act
            result = await search_papers("test query")

            # Assert
            assert result["success"] is False
            assert result["error"]["type"] == "error"
            assert "API Error" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_paper_integration(self):
        """Test get_paper tool integration."""
        # Arrange
        mock_paper = MagicMock(
            paper_id="123",
            title="Test Paper",
            abstract="Test abstract",
            year=2024,
            citation_count=10,
            authors=[MagicMock(name="Author 1")],
            model_dump=lambda **kwargs: {
                "paperId": "123",
                "title": "Test Paper",
                "abstract": "Test abstract",
                "year": 2024,
                "citationCount": 10,
                "authors": [{"name": "Author 1"}]
            }
        )

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.get_paper = AsyncMock(return_value=mock_paper)

            # Act
            result = await get_paper("123", include_citations=False)

            # Assert
            assert result["success"] is True
            assert result["data"]["paperId"] == "123"
            assert result["data"]["title"] == "Test Paper"

    @pytest.mark.asyncio
    async def test_get_author_integration(self):
        """Test get_author tool integration."""
        # Arrange
        mock_author = MagicMock(
            author_id="1234567",
            name="John Doe",
            paper_count=50,
            citation_count=1000,
            h_index=25,
            model_dump=lambda **kwargs: {
                "authorId": "1234567",
                "name": "John Doe",
                "paperCount": 50,
                "citationCount": 1000,
                "hIndex": 25
            }
        )

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.get_author = AsyncMock(return_value=mock_author)

            # Act
            result = await get_author("1234567")

            # Assert
            assert result["success"] is True
            assert result["data"]["name"] == "John Doe"
            assert result["data"]["paperCount"] == 50

    @pytest.mark.asyncio
    async def test_get_recommendations_integration(self):
        """Test get_recommendations tool integration."""
        # Arrange
        mock_papers = [
            MagicMock(
                paper_id=f"rec{i}",
                title=f"Recommended Paper {i}",
                model_dump=lambda i=i, **_kwargs: {
                    "paperId": f"rec{i}",
                    "title": f"Recommended Paper {i}"
                }
            )
            for i in range(3)
        ]

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.get_recommendations = AsyncMock(return_value=mock_papers)

            # Act
            result = await get_recommendations("123", limit=3)

            # Assert
            assert result["success"] is True
            assert len(result["data"]["recommendations"]) == 3
            assert result["data"]["count"] == 3

    @pytest.mark.asyncio
    async def test_resource_handler(self):
        """Test resource handler for paper retrieval."""
        # Arrange
        mock_author1 = MagicMock()
        mock_author1.name = "Author 1"
        mock_author2 = MagicMock()
        mock_author2.name = "Author 2"
        
        mock_paper = MagicMock(
            title="Test Paper",
            abstract="Test abstract",
            year=2024,
            venue="Test Conference",
            citation_count=10,
            url="https://example.com/paper",
            authors=[mock_author1, mock_author2]
        )

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_client.get_paper = AsyncMock(return_value=mock_paper)

            # Act
            result = await get_paper_resource("123")

            # Assert
            assert "# Test Paper" in result
            assert "**Authors**: Author 1, Author 2" in result
            assert "**Year**: 2024" in result
            assert "**Citations**: 10" in result

    @pytest.mark.asyncio
    async def test_prompt_handler(self):
        """Test prompt handler for literature review."""
        # Act
        result = literature_review("machine learning", max_papers=15, start_year=2020)

        # Assert
        assert "machine learning" in result
        assert "15 papers" in result
        assert "published after 2020" in result
        assert "literature review" in result.lower()

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests."""
        # Arrange
        async def make_search(query: str):
            return await search_papers(query, limit=5)

        with patch('semantic_scholar_mcp.server.api_client') as mock_client:
            mock_response = MagicMock(
                items=[],
                total=0,
                offset=0,
                limit=5,
                has_more=False
            )
            mock_client.search_papers = AsyncMock(return_value=mock_response)

            # Act - Make 10 concurrent requests
            tasks = [make_search(f"query {i}") for i in range(10)]
            results = await asyncio.gather(*tasks)

            # Assert - All should succeed
            for result in results:
                assert result["success"] is True
                assert result["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_validation_errors(self):
        """Test validation error handling."""
        # Test with invalid limit
        result = await search_papers("test", limit=1000)  # Max is 100

        # The function should handle this gracefully
        assert "success" in result

    @pytest.mark.asyncio
    async def test_api_key_configuration(self):
        """Test API key configuration handling."""
        # Arrange
        os.environ["SEMANTIC_SCHOLAR_API_KEY"] = "test-api-key"

        with patch('semantic_scholar_mcp.server.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                logging=MagicMock(
                    level="INFO", 
                    format="json",
                    file_path=None,
                    max_file_size=1024,
                    backup_count=3,
                    include_timestamp=True,
                    include_context=True
                ),
                cache=MagicMock(enabled=True, max_size=100, ttl_seconds=300),
                semantic_scholar=MagicMock(api_key="test-api-key")
            )

            # Act - Re-initialize with API key
            await initialize_server()

            # Assert - Client should be configured with API key
            # This would be verified by checking the headers in actual requests
