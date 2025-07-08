#!/usr/bin/env python3
"""Test script for Semantic Scholar MCP server."""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from semantic_scholar_mcp.server import api_client, initialize_server


async def test_search_papers():
    """Test paper search functionality."""
    print("🔍 Testing paper search...")

    try:
        # Initialize the server first
        await initialize_server()

        if not api_client:
            print("❌ API client not initialized")
            return

        # Test search
        print("Searching for papers on 'machine learning'...")

        # Create a simple search request
        from semantic_scholar_mcp.domain_models import SearchQuery

        search_query = SearchQuery(
            query="machine learning",
            limit=5,
            offset=0
        )

        async with api_client:
            result = await api_client.search_papers(search_query)

        print(f"✅ Found {len(result.items)} papers:")
        for i, paper in enumerate(result.items[:3], 1):
            print(f"{i}. {paper.title}")
            print(f"   Authors: {', '.join([a.name for a in paper.authors])}")
            print(f"   Year: {paper.year}")
            print(f"   Citations: {paper.citation_count}")
            print()

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

async def test_get_paper():
    """Test getting specific paper details."""
    print("📄 Testing paper retrieval...")

    try:
        # Initialize the server first
        await initialize_server()

        if not api_client:
            print("❌ API client not initialized")
            return

        # Test with a known paper ID (example ArXiv paper)
        paper_id = "2017arXiv170603762V"  # Attention is All You Need

        print(f"Getting paper details for: {paper_id}")

        async with api_client:
            paper = await api_client.get_paper(paper_id=paper_id)

        print("✅ Retrieved paper:")
        print(f"   Title: {paper.title}")
        print(f"   Authors: {', '.join([a.name for a in paper.authors])}")
        print(f"   Year: {paper.year}")
        print(f"   Citations: {paper.citation_count}")
        if paper.abstract:
            print(f"   Abstract: {paper.abstract[:200]}...")
        print()

    except Exception as e:
        print(f"❌ Error during paper retrieval test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("🚀 Starting Semantic Scholar MCP Server Tests")
    print("=" * 50)

    await test_search_papers()
    print("-" * 50)
    await test_get_paper()

    print("✅ Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
