#!/usr/bin/env python3
"""Simple test script for the MCP server."""

import asyncio
import json
from typing import Dict, Any

# Import the server components directly
from semantic_scholar_mcp.server import mcp, on_startup, on_shutdown, initialize_server
from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
from semantic_scholar_mcp.domain_models import SearchQuery
from core.config import ApplicationConfig


async def test_tools():
    """Test the MCP tools directly."""
    print("=== Testing Semantic Scholar MCP Server ===\n")
    
    # Initialize server
    await initialize_server()
    
    try:
        # Test 1: Health Check
        print("1. Testing health_check tool...")
        from semantic_scholar_mcp.server import health_check
        result = await health_check()
        print(f"   Status: {result['status']}")
        print(f"   API Accessible: {result['api_accessible']}")
        print(f"   Cache Enabled: {result['cache_enabled']}")
        
        # Test 2: Search Papers
        print("\n2. Testing search_papers tool...")
        from semantic_scholar_mcp.server import search_papers
        result = await search_papers(
            query="transformer architecture",
            limit=3
        )
        print(f"   Found {result['total']} papers")
        for i, paper in enumerate(result['items'][:3], 1):
            print(f"   {i}. {paper['title']} ({paper.get('year', 'N/A')})")
            print(f"      Citations: {paper.get('citation_count', 0)}")
        
        # Test 3: Search Authors
        print("\n3. Testing search_authors tool...")
        from semantic_scholar_mcp.server import search_authors
        result = await search_authors(
            query="Yoshua Bengio",
            limit=2
        )
        print(f"   Found {result['total']} authors")
        for i, author in enumerate(result['items'][:2], 1):
            print(f"   {i}. {author['name']}")
            if author.get('h_index'):
                print(f"      H-index: {author['h_index']}")
            if author.get('paper_count'):
                print(f"      Papers: {author['paper_count']}")
        
        # Test 4: Get specific paper (if we found any)
        print("\n4. Testing get_paper tool...")
        search_result = await search_papers(query="attention is all you need", limit=1)
        if search_result['items']:
            paper_id = search_result['items'][0]['paper_id']
            from semantic_scholar_mcp.server import get_paper
            paper = await get_paper(paper_id=paper_id)
            print(f"   Title: {paper['title']}")
            print(f"   Year: {paper.get('year', 'N/A')}")
            print(f"   Authors: {', '.join(a['name'] for a in paper.get('authors', []))}")
            print(f"   Abstract: {paper.get('abstract', '')[:100]}...")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await on_shutdown()


async def test_direct_client():
    """Test the API client directly."""
    print("\n=== Testing API Client Directly ===\n")
    
    config = ApplicationConfig()
    client = SemanticScholarClient(config.semantic_scholar)
    
    try:
        # Test search
        query = SearchQuery(query="machine learning", limit=3)
        result = await client.search_papers(query)
        print(f"Found {result.total} papers via direct client")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await client.close()


def main():
    """Run tests."""
    # Run tool tests
    asyncio.run(test_tools())
    
    # Run direct client test
    asyncio.run(test_direct_client())


if __name__ == "__main__":
    main()