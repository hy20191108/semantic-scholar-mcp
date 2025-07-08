#!/usr/bin/env python3
"""Test README.md specified functionalities."""

import asyncio
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))


async def test_search_papers():
    """Test search_papers tool as specified in README."""
    print("🔍 Testing search_papers...")

    try:
        from semantic_scholar_mcp.server import initialize_server, search_papers

        await initialize_server()

        # Test the exact functionality mentioned in README
        result = await search_papers(
            query="large language models",
            limit=3
        )

        if result.get("success"):
            papers = result["data"]["papers"]
            print(f"✅ Found {len(papers)} papers")
            for i, paper in enumerate(papers, 1):
                print(f"{i}. {paper['title']}")
            return True
        print(f"❌ Error: {result.get('error', {}).get('message', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_get_paper():
    """Test get_paper tool as specified in README."""
    print("\n📄 Testing get_paper...")

    try:
        from semantic_scholar_mcp.server import get_paper, initialize_server

        await initialize_server()

        # Test with the Transformer paper (Attention is All You Need)
        paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"

        result = await get_paper(
            paper_id=paper_id,
            include_citations=False,
            include_references=False
        )

        await asyncio.sleep(1)  # Rate limiting

        if result.get("success"):
            paper = result["data"]
            print(f"✅ Retrieved paper: {paper['title']}")
            print(f"   Authors: {', '.join([a['name'] for a in paper['authors'][:3]])}...")
            print(f"   Year: {paper.get('year', 'Unknown')}")
            return True
        print(f"❌ Error: {result.get('error', {}).get('message', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_search_authors():
    """Test search_authors tool as specified in README."""
    print("\n👤 Testing search_authors...")

    try:
        from semantic_scholar_mcp.server import initialize_server, search_authors

        await initialize_server()

        result = await search_authors(
            query="Geoffrey Hinton",
            limit=3
        )

        await asyncio.sleep(1)  # Rate limiting

        if result.get("success"):
            authors = result["data"]["authors"]
            print(f"✅ Found {len(authors)} authors")
            for i, author in enumerate(authors, 1):
                print(f"{i}. {author['name']} (Papers: {author.get('paper_count', 'Unknown')})")
            return True
        print(f"❌ Error: {result.get('error', {}).get('message', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_batch_get_papers():
    """Test batch_get_papers tool as specified in README."""
    print("\n📚 Testing batch_get_papers...")

    try:
        from semantic_scholar_mcp.server import batch_get_papers, initialize_server

        await initialize_server()

        # Test with a few known paper IDs
        paper_ids = [
            "204e3073870fae3d05bcbc2f6a8e263d9b72e776",  # Attention is All You Need
            "649def34f8be52c8b66281af98ae884c09aef38b",   # BERT
        ]

        result = await batch_get_papers(
            paper_ids=paper_ids
        )

        await asyncio.sleep(2)  # Rate limiting

        if result.get("success"):
            papers = result["data"]["papers"]
            print(f"✅ Retrieved {len(papers)} papers in batch")
            for i, paper in enumerate(papers, 1):
                print(f"{i}. {paper['title']}")
            return True
        print(f"❌ Error: {result.get('error', {}).get('message', 'Unknown error')}")
        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_literature_review_prompt():
    """Test literature_review prompt as specified in README."""
    print("\n📝 Testing literature_review prompt...")

    try:
        from semantic_scholar_mcp.server import literature_review

        # Test the prompt generation
        prompt = literature_review(
            topic="transformer architectures",
            max_papers=10,
            start_year=2017
        )

        if "transformer architectures" in prompt and "2017" in prompt:
            print("✅ Literature review prompt generated successfully")
            print("   Topic: transformer architectures")
            print("   Max papers: 10")
            print("   Start year: 2017")
            return True
        print("❌ Prompt generation failed")
        return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def main():
    """Run all README functionality tests."""
    print("🚀 Testing README.md Specified Functionalities")
    print("=" * 60)

    tests = [
        test_search_papers,
        test_get_paper,
        test_search_authors,
        test_batch_get_papers,
        test_literature_review_prompt
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} README functionality tests passed!")
    else:
        print(f"❌ {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
