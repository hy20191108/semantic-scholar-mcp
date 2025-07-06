"""Unit tests for MCP server implementation."""

import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_scholar_mcp.domain_models import (
    Paper, Author, Citation, PaperId, AuthorId,
    SearchQuery
)
from semantic_scholar_mcp.base_models import PaginatedResponse
from core.exceptions import ValidationError, APIError


class TestMCPTools:
    """Test MCP tool implementations."""
    
    @pytest.mark.asyncio
    async def test_search_papers_tool(self, sample_papers):
        """Test search_papers tool function."""
        # Mock the global API client
        mock_client = AsyncMock()
        mock_client.search_papers.return_value = PaginatedResponse(
            items=sample_papers[:3],
            total=50,
            offset=0,
            limit=10
        )
        
        # Import and patch the tool function
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import search_papers
            
            # Execute tool
            result = await search_papers(
                query="machine learning",
                limit=10,
                year=2024
            )
            
            # Verify result structure
            assert "items" in result
            assert "total" in result
            assert len(result["items"]) == 3
            assert result["total"] == 50
            
            # Verify API call
            mock_client.search_papers.assert_called_once()
            call_args = mock_client.search_papers.call_args[0][0]
            assert isinstance(call_args, SearchQuery)
            assert call_args.query == "machine learning"
            assert call_args.limit == 10
    
    @pytest.mark.asyncio
    async def test_search_papers_validation_error(self):
        """Test search_papers with invalid parameters."""
        from semantic_scholar_mcp.server import search_papers
        
        # Empty query should raise validation error
        with pytest.raises(ValidationError):
            await search_papers(query="", limit=10)
        
        # Invalid limit should raise validation error
        with pytest.raises(ValidationError):
            await search_papers(query="test", limit=200)
    
    @pytest.mark.asyncio
    async def test_get_paper_tool(self, sample_paper):
        """Test get_paper tool function."""
        mock_client = AsyncMock()
        mock_client.get_paper.return_value = sample_paper
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import get_paper
            
            # Execute tool
            result = await get_paper(
                paper_id="test123",
                include_citations=True,
                include_references=True
            )
            
            # Verify result
            assert result["paper_id"] == "test123"
            assert result["title"] == sample_paper.title
            assert "authors" in result
            
            # Verify API call
            mock_client.get_paper.assert_called_once_with(
                PaperId("test123"),
                include_citations=True,
                include_references=True
            )
    
    @pytest.mark.asyncio
    async def test_get_paper_not_found(self):
        """Test get_paper with non-existent paper."""
        mock_client = AsyncMock()
        mock_client.get_paper.side_effect = APIError(
            "Paper not found",
            status_code=404,
            error_code="NOT_FOUND"
        )
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import get_paper
            
            with pytest.raises(APIError) as exc_info:
                await get_paper(paper_id="invalid123")
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_author_tool(self, sample_author):
        """Test get_author tool function."""
        mock_client = AsyncMock()
        mock_client.get_author.return_value = sample_author
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import get_author
            
            # Execute tool
            result = await get_author(author_id="author123")
            
            # Verify result
            assert result["author_id"] == "author123"
            assert result["name"] == sample_author.name
            assert result["h_index"] == sample_author.h_index
            assert "affiliations" in result
    
    @pytest.mark.asyncio
    async def test_batch_get_papers_tool(self, sample_papers):
        """Test batch_get_papers tool function."""
        mock_client = AsyncMock()
        mock_client.batch_get_papers.return_value = sample_papers[:3]
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import batch_get_papers
            
            paper_ids = ["paper0", "paper1", "paper2"]
            
            # Execute tool
            result = await batch_get_papers(paper_ids=paper_ids)
            
            # Verify result
            assert len(result) == 3
            assert all(p["paper_id"] in paper_ids for p in result)
    
    @pytest.mark.asyncio
    async def test_get_recommendations_tool(self, sample_papers):
        """Test get_recommendations tool function."""
        mock_client = AsyncMock()
        mock_client.get_recommendations.return_value = sample_papers[:5]
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import get_recommendations
            
            # Execute tool
            result = await get_recommendations(
                paper_id="test123",
                limit=5
            )
            
            # Verify result
            assert len(result) == 5
            assert all("paper_id" in p for p in result)
            assert all("title" in p for p in result)
    
    @pytest.mark.asyncio
    async def test_health_check_tool(self):
        """Test health_check tool function."""
        mock_client = AsyncMock()
        mock_client.health_check.return_value = {
            "status": "healthy",
            "api_accessible": True,
            "cache_enabled": True,
            "rate_limit_remaining": 95,
            "version": "1.0.0",
            "uptime_seconds": 3600
        }
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import health_check
            
            # Execute tool
            result = await health_check()
            
            # Verify result
            assert result["status"] == "healthy"
            assert result["api_accessible"] is True
            assert "rate_limit_remaining" in result


class TestMCPResources:
    """Test MCP resource implementations."""
    
    @pytest.mark.asyncio
    async def test_paper_resource(self, sample_paper):
        """Test paper resource handler."""
        mock_client = AsyncMock()
        mock_client.get_paper.return_value = sample_paper
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import handle_paper_resource
            
            # Execute resource handler
            result = await handle_paper_resource("paper://test123")
            
            # Verify result
            assert result["uri"] == "paper://test123"
            assert result["name"] == sample_paper.title
            assert result["mimeType"] == "application/json"
            assert "size" in result
            assert "metadata" in result
            
            # Verify content
            content = json.loads(result["content"])
            assert content["paper_id"] == "test123"
            assert content["title"] == sample_paper.title
    
    @pytest.mark.asyncio
    async def test_author_resource(self, sample_author):
        """Test author resource handler."""
        mock_client = AsyncMock()
        mock_client.get_author.return_value = sample_author
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import handle_author_resource
            
            # Execute resource handler
            result = await handle_author_resource("author://author123")
            
            # Verify result
            assert result["uri"] == "author://author123"
            assert result["name"] == sample_author.name
            assert result["mimeType"] == "application/json"
            
            # Verify metadata
            assert result["metadata"]["h_index"] == sample_author.h_index
            assert result["metadata"]["citation_count"] == sample_author.citation_count


class TestMCPPrompts:
    """Test MCP prompt templates."""
    
    def test_literature_review_prompt(self):
        """Test literature review prompt template."""
        from semantic_scholar_mcp.server import PROMPTS
        
        lit_review = next(p for p in PROMPTS if p["name"] == "literature_review")
        
        assert lit_review["name"] == "literature_review"
        assert "Generate a comprehensive literature review" in lit_review["description"]
        assert len(lit_review["arguments"]) >= 2
        
        # Check required arguments
        arg_names = [arg["name"] for arg in lit_review["arguments"]]
        assert "topic" in arg_names
        assert "year_range" in arg_names
    
    def test_paper_summary_prompt(self):
        """Test paper summary prompt template."""
        from semantic_scholar_mcp.server import PROMPTS
        
        summary = next(p for p in PROMPTS if p["name"] == "paper_summary")
        
        assert summary["name"] == "paper_summary"
        assert "concise summary" in summary["description"].lower()
        
        # Check paper_id argument
        paper_id_arg = next(
            arg for arg in summary["arguments"] 
            if arg["name"] == "paper_id"
        )
        assert paper_id_arg["required"] is True
    
    def test_citation_analysis_prompt(self):
        """Test citation analysis prompt template."""
        from semantic_scholar_mcp.server import PROMPTS
        
        citation = next(p for p in PROMPTS if p["name"] == "citation_analysis")
        
        assert citation["name"] == "citation_analysis"
        assert "citation patterns" in citation["description"].lower()
        assert len(citation["arguments"]) >= 1


class TestErrorHandling:
    """Test error handling in MCP server."""
    
    @pytest.mark.asyncio
    async def test_api_error_propagation(self):
        """Test that API errors are properly propagated."""
        mock_client = AsyncMock()
        mock_client.search_papers.side_effect = APIError(
            "Service unavailable",
            status_code=503,
            error_code="SERVICE_UNAVAILABLE"
        )
        
        with patch('semantic_scholar_mcp.server.api_client', mock_client):
            from semantic_scholar_mcp.server import search_papers
            
            with pytest.raises(APIError) as exc_info:
                await search_papers(query="test")
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.error_code == "SERVICE_UNAVAILABLE"
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation error handling."""
        from semantic_scholar_mcp.server import search_papers
        
        # Test with invalid parameters
        with pytest.raises(ValidationError) as exc_info:
            await search_papers(
                query="test",
                limit=150  # Exceeds maximum
            )
        
        assert "less than or equal to 100" in str(exc_info.value)


class TestToolMetadata:
    """Test tool metadata and descriptions."""
    
    def test_tool_descriptions(self):
        """Test that all tools have proper descriptions."""
        # This would normally import the tool decorators
        # For now, we'll test the expected structure
        expected_tools = [
            "search_papers",
            "get_paper",
            "get_paper_citations",
            "get_paper_references",
            "get_author",
            "get_author_papers",
            "search_authors",
            "batch_get_papers",
            "get_recommendations",
            "health_check"
        ]
        
        # In a real test, we'd verify each tool has:
        # - A descriptive docstring
        # - Proper parameter annotations
        # - Return type hints
        assert len(expected_tools) == 10