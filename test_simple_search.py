#!/usr/bin/env python3
"""Integration test for Semantic Scholar MCP server."""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


async def test_search_papers():
    """Test paper search functionality."""
    print("🔍 Testing paper search...")

    try:
        # Import required modules
        from core.cache import InMemoryCache
        from core.config import get_config
        from core.logging import get_logger
        from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
        from semantic_scholar_mcp.domain_models import SearchQuery

        # Initialize components
        config = get_config()
        logger = get_logger(__name__)

        cache = InMemoryCache(
            max_size=config.cache.max_size,
            default_ttl=config.cache.ttl_seconds
        ) if config.cache.enabled else None

        # Create API client
        api_client = SemanticScholarClient(
            config=config.semantic_scholar,
            logger=logger,
            cache=cache
        )

        # Create search query
        search_query = SearchQuery(
            query="machine learning transformers",
            limit=3,
            offset=0
        )

        print(f"Search query: {search_query.query} (limit: {search_query.limit})")

        # Execute search
        async with api_client:
            result = await api_client.search_papers(search_query)

        print(f"✅ Search successful! Found {len(result.items)} papers:")

        for i, paper in enumerate(result.items, 1):
            print(f"\n{i}. {paper.title}")
            authors = [a.name for a in paper.authors]
            author_list = ', '.join(authors[:3])
            suffix = '...' if len(authors) > 3 else ''
            print(f"   Authors: {author_list}{suffix}")
            print(f"   Year: {paper.year or 'Unknown'}")
            print(f"   Citations: {paper.citation_count or 0}")
            if paper.abstract:
                preview_length = 150
                abstract_preview = (
                    paper.abstract[:preview_length] + "..."
                    if len(paper.abstract) > preview_length
                    else paper.abstract
                )
                print(f"   Abstract: {abstract_preview}")

        return True

    except Exception as e:
        import traceback

        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run integration test."""
    print("🚀 Semantic Scholar MCP Integration Test")
    print("=" * 50)

    result = await test_search_papers()

    if result:
        print("\n✅ Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed.")


if __name__ == "__main__":
    asyncio.run(main())
