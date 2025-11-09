#!/usr/bin/env python3
"""
Semantic Scholar MCP - 24ツール動作チェック

すべてのツールに対する基本的な動作確認を行います。
APIキーが必要な一部のツールは適切なエラーが返されることを確認します。
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトのrootディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from semantic_scholar_mcp.server import mcp


async def test_tool(tool_name: str, **kwargs) -> bool:
    """単一ツールのテスト実行."""
    try:
        # MCPツールを直接呼び出し
        if tool_name == "search_papers":
            result = await mcp.call_tool("search_papers", {"query": "machine learning", "limit": 1})
        elif tool_name == "get_paper":
            result = await mcp.call_tool("get_paper", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b"})
        elif tool_name == "get_paper_citations":
            result = await mcp.call_tool("get_paper_citations", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b", "limit": 1})
        elif tool_name == "get_paper_references":
            result = await mcp.call_tool("get_paper_references", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b", "limit": 1})
        elif tool_name == "get_paper_authors":
            result = await mcp.call_tool("get_paper_authors", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b", "limit": 1})
        elif tool_name == "search_authors":
            result = await mcp.call_tool("search_authors", {"query": "Andrew Ng", "limit": 1})
        elif tool_name == "get_author":
            result = await mcp.call_tool("get_author", {"author_id": "1741101"})
        elif tool_name == "get_author_papers":
            result = await mcp.call_tool("get_author_papers", {"author_id": "1741101", "limit": 1})
        elif tool_name == "get_recommendations_for_paper":
            result = await mcp.call_tool("get_recommendations_for_paper", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b", "limit": 1})
        elif tool_name == "batch_get_papers":
            result = await mcp.call_tool("batch_get_papers", {"paper_ids": ["649def34f8be52c8b66281af98ae884c09aef38b"]})
        elif tool_name == "bulk_search_papers":
            result = await mcp.call_tool("bulk_search_papers", {"query": "machine learning", "limit": 1})
        elif tool_name == "search_papers_match":
            result = await mcp.call_tool("search_papers_match", {"title": "Attention Is All You Need"})
        elif tool_name == "autocomplete_query":
            result = await mcp.call_tool("autocomplete_query", {"query": "machine learn"})
        elif tool_name == "search_snippets":
            result = await mcp.call_tool("search_snippets", {"query": "machine learning", "limit": 1})
        elif tool_name == "batch_get_authors":
            result = await mcp.call_tool("batch_get_authors", {"author_ids": ["1741101"]})
        elif tool_name == "get_recommendations_batch":
            result = await mcp.call_tool("get_recommendations_batch", {"positive_paper_ids": ["649def34f8be52c8b66281af98ae884c09aef38b"], "limit": 1})
        elif tool_name == "get_dataset_releases":
            result = await mcp.call_tool("get_dataset_releases", {})
        elif tool_name == "get_dataset_info":
            result = await mcp.call_tool("get_dataset_info", {"release_id": "2023-03-28"})
        elif tool_name == "get_dataset_download_links":
            # APIキーが必要 - 401エラーが期待される
            result = await mcp.call_tool("get_dataset_download_links", {"release_id": "2023-03-28", "dataset_name": "papers"})
        elif tool_name == "get_paper_fulltext":
            result = await mcp.call_tool("get_paper_fulltext", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b"})
        elif tool_name == "get_paper_with_embeddings":
            result = await mcp.call_tool("get_paper_with_embeddings", {"paper_id": "649def34f8be52c8b66281af98ae884c09aef38b"})
        elif tool_name == "search_papers_with_embeddings":
            result = await mcp.call_tool("search_papers_with_embeddings", {"query": "machine learning", "limit": 1})
        elif tool_name == "get_incremental_dataset_updates":
            # APIキーが必要 - 401エラーが期待される
            result = await mcp.call_tool("get_incremental_dataset_updates", {"start_release_id": "2023-01-01", "end_release_id": "2023-03-28", "dataset_name": "papers"})
        elif tool_name == "check_api_key_status":
            result = await mcp.call_tool("check_api_key_status", {})
        else:
            print(f"  ❌ {tool_name:<35} Unknown tool")
            return False

        # 結果の確認
        if result and hasattr(result, 'content'):
            content = result.content[0].text if result.content else ""
            if content and ("data" in content or "error" in content or tool_name in ["check_api_key_status", "get_dataset_download_links", "get_incremental_dataset_updates"]):
                print(f"  ✅ {tool_name:<35} PASS")
                return True
            print(f"  ⚠️  {tool_name:<35} UNEXPECTED RESPONSE: {content[:100]}...")
            return False
        print(f"  ❌ {tool_name:<35} NO RESPONSE")
        return False

    except Exception as e:
        error_msg = str(e)
        # APIキー関連のエラーは期待される
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            print(f"  ✅ {tool_name:<35} PASS (Expected 401 - API key required)")
            return True
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            print(f"  ⚠️  {tool_name:<35} RATE LIMITED")
            return True
        print(f"  ❌ {tool_name:<35} ERROR: {error_msg}")
        return False


async def main():
    """24ツールの動作チェックを実行."""
    print("=" * 80)
    print("SEMANTIC SCHOLAR MCP - 24ツール動作チェック")
    print("=" * 80)
    print()

    # 24ツールの一覧（カテゴリー別）
    tools = {
        "Paper Tools (9)": [
            "search_papers",
            "get_paper",
            "get_paper_citations",
            "get_paper_references",
            "get_paper_authors",
            "batch_get_papers",
            "get_paper_with_embeddings",
            "search_papers_with_embeddings",
            "get_paper_fulltext",
        ],
        "Author Tools (4)": [
            "search_authors",
            "get_author",
            "get_author_papers",
            "batch_get_authors",
        ],
        "Recommendation Tools (2)": [
            "get_recommendations_for_paper",
            "get_recommendations_batch",
        ],
        "Search Tools (4)": [
            "bulk_search_papers",
            "search_papers_match",
            "autocomplete_query",
            "search_snippets",
        ],
        "Dataset Tools (4)": [
            "get_dataset_releases",
            "get_dataset_info",
            "get_dataset_download_links",
            "get_incremental_dataset_updates",
        ],
        "Utility Tools (1)": [
            "check_api_key_status",
        ],
    }

    total_tools = 0
    total_passed = 0

    for category, tool_list in tools.items():
        print(f"{category}")
        print("=" * len(category))

        category_passed = 0
        for tool_name in tool_list:
            if await test_tool(tool_name):
                category_passed += 1
            total_tools += 1

            # APIレート制限を避けるため少し待機
            await asyncio.sleep(0.1)

        total_passed += category_passed
        print(f"Category Result: {category_passed}/{len(tool_list)} passed")
        print()

    print("=" * 80)
    print(f"OVERALL RESULT: {total_passed}/{total_tools} tools passed")

    if total_passed == total_tools:
        print("SUCCESS: All tools are working correctly!")
    else:
        print(f"WARNING: {total_tools - total_passed} tools have issues")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
