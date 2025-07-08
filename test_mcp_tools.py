#!/usr/bin/env python3
"""Test MCP tools directly."""

import asyncio
import json
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

async def test_mcp_search_papers():
    """Test MCP search_papers tool."""
    print("🔍 Testing MCP search_papers tool...")

    try:
        from semantic_scholar_mcp.server import initialize_server, search_papers

        # Initialize server
        await initialize_server()

        # Test search
        result = await search_papers(
            query="machine learning",
            limit=3
        )

        print("✅ MCP search_papers result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result.get("success", False)

    except Exception as e:
        print(f"❌ Error testing MCP search_papers: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mcp_get_paper():
    """Test MCP get_paper tool."""
    print("\n📄 Testing MCP get_paper tool...")

    try:
        from semantic_scholar_mcp.server import get_paper, initialize_server

        # Initialize server
        await initialize_server()

        # Test with a specific paper ID
        # Using Semantic Scholar ID format instead
        paper_id = "649def34f8be52c8b66281af98ae884c09aef38b"  # Another well-known paper

        result = await get_paper(
            paper_id=paper_id,
            include_citations=False,
            include_references=False
        )

        print("✅ MCP get_paper result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result.get("success", False)

    except Exception as e:
        print(f"❌ Error testing MCP get_paper: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run MCP tool tests."""
    print("🚀 MCP Tools Tests")
    print("=" * 50)

    search_ok = await test_mcp_search_papers()
    print("-" * 50)

    # Wait a bit to avoid rate limiting
    await asyncio.sleep(2)

    paper_ok = await test_mcp_get_paper()

    print("\n" + "=" * 50)
    if search_ok and paper_ok:
        print("✅ All MCP tool tests passed!")
    else:
        print("❌ Some MCP tool tests failed.")

if __name__ == "__main__":
    asyncio.run(main())
