#!/usr/bin/env python3
"""Direct API test for Semantic Scholar."""

import asyncio

import httpx


async def test_semantic_scholar_api():
    """Test direct API call to Semantic Scholar."""
    print("🌐 Testing direct Semantic Scholar API...")

    base_url = "https://api.semanticscholar.org/graph/v1"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test search endpoint
            search_url = f"{base_url}/paper/search"
            params = {
                "query": "machine learning",
                "limit": 3,
                "fields": "title,authors,year,citationCount,abstract"
            }

            print(f"Calling: {search_url}")
            print(f"Params: {params}")

            response = await client.get(search_url, params=params)
            response.raise_for_status()

            data = response.json()

            print("✅ API call successful!")
            print(f"   Status: {response.status_code}")
            print(f"   Found {data.get('total', 0)} papers")

            papers = data.get("data", [])
            for i, paper in enumerate(papers[:3], 1):
                print(f"\n{i}. {paper.get('title', 'No title')}")
                authors = paper.get('authors', [])
                author_names = [a.get('name', 'Unknown') for a in authors]
                print(f"   Authors: {', '.join(author_names)}")
                print(f"   Year: {paper.get('year', 'Unknown')}")
                print(f"   Citations: {paper.get('citationCount', 0)}")

                abstract = paper.get('abstract', '')
                if abstract:
                    print(f"   Abstract: {abstract[:150]}...")

            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_get_specific_paper():
    """Test getting a specific paper."""
    print("\n📄 Testing specific paper retrieval...")

    base_url = "https://api.semanticscholar.org/graph/v1"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Test with "Attention is All You Need" paper
            paper_id = "204e3073870fae3d05bcbc2f6a8e263d9b72e776"  # Transformer paper
            paper_url = f"{base_url}/paper/{paper_id}"
            params = {
                "fields": "title,authors,year,citationCount,abstract,venue"
            }

            print(f"Getting paper: {paper_id}")

            response = await client.get(paper_url, params=params)
            response.raise_for_status()

            paper = response.json()

            print("✅ Paper retrieved successfully!")
            print(f"   Title: {paper.get('title', 'No title')}")

            authors = paper.get('authors', [])
            author_names = [a.get('name', 'Unknown') for a in authors]
            print(f"   Authors: {', '.join(author_names)}")
            print(f"   Year: {paper.get('year', 'Unknown')}")
            print(f"   Venue: {paper.get('venue', 'Unknown')}")
            print(f"   Citations: {paper.get('citationCount', 0)}")

            abstract = paper.get('abstract', '')
            if abstract:
                print(f"   Abstract: {abstract[:200]}...")

            return True

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run API tests."""
    print("🚀 Direct Semantic Scholar API Tests")
    print("=" * 50)

    search_ok = await test_semantic_scholar_api()
    paper_ok = await test_get_specific_paper()

    print("\n" + "=" * 50)
    if search_ok and paper_ok:
        print("✅ All API tests passed! Semantic Scholar API is accessible.")
    else:
        print("❌ Some API tests failed.")

if __name__ == "__main__":
    asyncio.run(main())
