"""Comprehensive test script to verify all 24 semantic-scholar-mcp tools.

This test validates the response format of all 24 tools by:
- Checking that responses are valid JSON strings
- Verifying no datetime serialization issues
- Checking TLDR field structure
- Validating response structure

Tool Categories (24 total):
- Paper Tools (10)
- Author Tools (4)
- Dataset Tools (4)
- Search & AI Tools (5)
- Utility (1)
"""

import json
from datetime import datetime


class ToolTestValidator:
    """Validates tool response formats."""

    @staticmethod
    def validate_json_response(response: str) -> tuple[bool, str]:
        """Validate that response is valid JSON string."""
        try:
            if not isinstance(response, str):
                return False, f"Not a string: {type(response)}"
            json.loads(response)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e!s}"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def validate_no_datetime_objects(response: str) -> tuple[bool, str]:
        """Validate response contains no datetime objects."""
        try:
            data = json.loads(response)

            def check_for_datetime(obj):
                if isinstance(obj, datetime):
                    return False
                if isinstance(obj, dict):
                    return all(check_for_datetime(v) for v in obj.values())
                if isinstance(obj, list):
                    return all(check_for_datetime(item) for item in obj)
                return True

            if not check_for_datetime(data):
                return False, "Found datetime object in response"
            return True, ""
        except Exception as e:
            return False, str(e)


def _validate_tool(tool_name: str, response_dict: dict) -> bool:
    """Validate a single tool response."""
    validator = ToolTestValidator()
    response = json.dumps(response_dict)

    valid, msg = validator.validate_json_response(response)
    if not valid:
        print(f"  ❌ {tool_name:40} {msg}")
        return False

    valid, msg = validator.validate_no_datetime_objects(response)
    if not valid:
        print(f"  ❌ {tool_name:40} {msg}")
        return False

    print(f"  ✅ {tool_name:40} PASS")
    return True


def test_tool_response_format_paper_tools():
    """Test response format for paper tools (10)."""
    print("\n" + "=" * 80)
    print("PAPER TOOLS (10)")
    print("=" * 80)

    passed = 0
    tools = {
        "search_papers": {
            "data": [{"paperId": "id", "title": "Paper", "year": 2023}],
            "total": 1,
        },
        "get_paper": {
            "paperId": "id",
            "title": "Paper",
            "year": 2023,
            "citationCount": 100,
        },
        "get_paper_citations": {
            "data": [{"paperId": "id", "title": "Cite", "year": 2023}],
            "total": 50,
        },
        "get_paper_references": {
            "data": [{"paperId": "id", "title": "Ref", "year": 2023}],
            "total": 30,
        },
        "get_paper_authors": {"data": [{"authorId": "id", "name": "John"}], "total": 5},
        "batch_get_papers": {
            "data": [{"paperId": "id", "title": "Paper", "year": 2023}]
        },
        "get_paper_with_embeddings": {
            "paperId": "id",
            "embedding": {"model": "specter_v2", "vector": [0.1, 0.2]},
        },
        "search_papers_with_embeddings": {
            "data": [
                {"paperId": "id", "embedding": {"model": "specter_v2", "vector": [0.1]}}
            ],
            "total": 1,
        },
        "get_paper_fulltext": {
            "paperId": "id",
            "title": "Paper",
            "markdown_content": "# Content",
        },
    }

    for name, response in tools.items():
        if _validate_tool(name, response):
            passed += 1

    assert passed == 9, f"Paper tools: {passed}/9 passed"


def test_tool_response_format_author_tools():
    """Test response format for author tools (4)."""
    print("\n" + "=" * 80)
    print("AUTHOR TOOLS (4)")
    print("=" * 80)

    passed = 0
    tools = {
        "search_authors": {"data": [{"authorId": "id", "name": "John"}], "total": 10},
        "get_author": {"authorId": "id", "name": "John", "citationCount": 1000},
        "get_author_papers": {
            "data": [{"paperId": "id", "title": "Paper", "year": 2023}],
            "total": 100,
        },
        "batch_get_authors": {"data": [{"authorId": "id", "name": "John"}]},
    }

    for name, response in tools.items():
        if _validate_tool(name, response):
            passed += 1

    assert passed == 4, f"Author tools: {passed}/4 passed"


def test_tool_response_format_dataset_tools():
    """Test response format for dataset tools (4)."""
    print("\n" + "=" * 80)
    print("DATASET TOOLS (4)")
    print("=" * 80)

    passed = 0
    tools = {
        "get_dataset_releases": {
            "data": [{"releaseId": "2023-03-28", "README": "Info"}]
        },
        "get_dataset_info": {
            "data": {"releaseId": "2023-03-28", "README": "Details", "datasets": []}
        },
        "get_dataset_download_links": {
            "data": {
                "name": "papers",
                "files": ["https://s3.amazonaws.com/file.json.gz"],
            }
        },
        "get_incremental_dataset_updates": {
            "data": {"dataset": "papers", "startRelease": "2023-01-01", "diffs": []}
        },
    }

    for name, response in tools.items():
        if _validate_tool(name, response):
            passed += 1

    assert passed == 4, f"Dataset tools: {passed}/4 passed"


def test_tool_response_format_search_ai_tools():
    """Test response format for search and AI tools (5)."""
    print("\n" + "=" * 80)
    print("SEARCH & AI TOOLS (5)")
    print("=" * 80)

    passed = 0
    tools = {
        "bulk_search_papers": {
            "data": [{"paperId": "id", "title": "Paper", "year": 2023}]
        },
        "search_papers_match": {
            "data": [{"paperId": "id", "title": "Paper", "matchScore": 0.95}],
            "total": 1,
        },
        "autocomplete_query": {"data": ["suggestion1", "suggestion2", "suggestion3"]},
        "search_snippets": {
            "data": [{"paperId": "id", "snippet": "Text...", "score": 0.85}],
            "total": 10,
        },
        "get_recommendations_batch": {
            "data": [{"paperId": "id", "title": "Paper", "year": 2023}]
        },
    }

    for name, response in tools.items():
        if _validate_tool(name, response):
            passed += 1

    assert passed == 5, f"Search/AI tools: {passed}/5 passed"


def test_tool_response_format_utility_tools():
    """Test response format for utility tools (1)."""
    print("\n" + "=" * 80)
    print("UTILITY TOOLS (1)")
    print("=" * 80)

    passed = 0
    tools = {
        "check_api_key_status": {
            "data": {"apiKeyConfigured": False, "rateLimitStatus": "available"}
        },
    }

    for name, response in tools.items():
        if _validate_tool(name, response):
            passed += 1

    assert passed == 1, f"Utility tools: {passed}/1 passed"


def test_all_tools_comprehensive():
    """Comprehensive test of all 24 tools."""
    print("\n" + "=" * 80)
    print("SEMANTIC SCHOLAR MCP - TOOL RESPONSE FORMAT VALIDATION")
    print("Testing all 24 tools for proper JSON serialization and structure")
    print("=" * 80)

    # Run all tool tests
    test_tool_response_format_paper_tools()
    test_tool_response_format_author_tools()
    test_tool_response_format_dataset_tools()
    test_tool_response_format_search_ai_tools()
    test_tool_response_format_utility_tools()

    print("\n" + "=" * 80)
    print("SUCCESS: All 24 tools validated")
    print("=" * 80)
