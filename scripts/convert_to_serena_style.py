#!/usr/bin/env python3
"""
Automatic conversion script to migrate all 24 tools to Serena-compliant pattern.

This script performs the following transformations:
1. Replace @with_tool_instructions with @inject_yaml_instructions
2. Remove @mcp_error_handler decorator
3. Change return type from dict[str, Any] to str
4. Remove RequestContext wrapper
5. Remove try-except blocks
6. Remove execute_api_with_error_handling calls
7. Remove dashboard statistics recording
8. Add json.dumps() to return statements
"""

import re
from pathlib import Path
from typing import NamedTuple


class ToolInfo(NamedTuple):
    """Information about a tool function."""

    name: str
    category: str


# All 23 tools with their categories (search_papers already converted manually)
TOOLS = [
    # Paper tools (9 - search_papers excluded)
    ToolInfo("get_paper", "paper"),
    ToolInfo("get_paper_citations", "paper"),
    ToolInfo("get_paper_references", "paper"),
    ToolInfo("get_paper_authors", "paper"),
    ToolInfo("batch_get_papers", "paper"),
    ToolInfo("bulk_search_papers", "paper"),
    ToolInfo("search_papers_match", "paper"),
    ToolInfo("get_paper_with_embeddings", "paper"),
    ToolInfo("search_papers_with_embeddings", "paper"),
    # Author tools (4)
    ToolInfo("search_authors", "author"),
    ToolInfo("get_author", "author"),
    ToolInfo("get_author_papers", "author"),
    ToolInfo("batch_get_authors", "author"),
    # Dataset tools (4)
    ToolInfo("get_dataset_releases", "dataset"),
    ToolInfo("get_dataset_info", "dataset"),
    ToolInfo("get_dataset_download_links", "dataset"),
    ToolInfo("get_incremental_dataset_updates", "dataset"),
    # PDF tools (1)
    ToolInfo("get_paper_fulltext", "pdf"),
    # Prompts/advanced tools (5)
    ToolInfo("get_recommendations_for_paper", "prompts"),
    ToolInfo("get_recommendations_batch", "prompts"),
    ToolInfo("autocomplete_query", "prompts"),
    ToolInfo("search_snippets", "prompts"),
    ToolInfo("check_api_key_status", "prompts"),
]


def extract_function_body(content: str, func_name: str) -> tuple[str, int, int] | None:
    """
    Extract function body from source code.

    Returns:
        Tuple of (function_body, start_pos, end_pos) or None if not found
    """
    # Match function definition
    pattern = rf"(@[\w_]+\([^)]*\)\s*)*\nasync def {func_name}\("
    match = re.search(pattern, content)

    if not match:
        return None

    start_pos = match.start()

    # Find the end of the function (next function or end of file)
    # Look for next function definition or end of file
    next_func_pattern = r"\n@[\w_]+\([^)]*\)\s*\nasync def \w+\("
    next_match = re.search(next_func_pattern, content[match.end() :])

    end_pos = match.end() + next_match.start() if next_match else len(content)

    return content[start_pos:end_pos], start_pos, end_pos


def transform_function(func_body: str, tool: ToolInfo) -> str:
    """
    Transform a single function to Serena-compliant pattern.

    Steps:
    1. Replace decorators
    2. Change return type
    3. Remove RequestContext
    4. Remove try-except
    5. Direct API calls
    6. json.dumps() returns
    """
    result = func_body

    # 1. Replace @with_tool_instructions with @inject_yaml_instructions
    result = re.sub(
        r"@with_tool_instructions\(['\"]" + re.escape(tool.name) + r"['\"]\)",
        f'@inject_yaml_instructions("{tool.name}", "{tool.category}")',
        result,
    )

    # 2. Remove @mcp_error_handler decorator
    result = re.sub(
        r"@mcp_error_handler\(tool_name=['\"]" + re.escape(tool.name) + r"['\"]\)\s*\n",
        "",
        result,
    )

    # 3. Change return type from dict[str, Any] to str
    result = re.sub(
        r"\) -> dict\[str, Any\]:",
        r") -> str:",
        result,
    )

    # 4. Remove RequestContext wrapper
    # Find "with RequestContext():" and remove it along with its indentation
    result = re.sub(
        r"    with RequestContext\(\):\s*\n",
        "",
        result,
    )

    # Dedent the content that was inside RequestContext
    # This is complex - need to reduce indentation by 4 spaces for function body
    lines = result.split("\n")
    new_lines = []
    inside_function = False
    docstring_complete = False

    for i, line in enumerate(lines):
        # Detect function definition line
        if re.match(r"async def " + re.escape(tool.name), line):
            inside_function = True
            new_lines.append(line)
            continue

        # Track docstring completion
        if inside_function and not docstring_complete:
            if '"""' in line:
                # Count quotes to detect end of docstring
                if line.count('"""') == 2 or (i > 0 and '"""' in lines[i - 1]):
                    docstring_complete = True
            new_lines.append(line)
            continue

        # Dedent function body (after docstring, before next function)
        if inside_function and docstring_complete:
            # Stop at next function or decorator
            if line.strip().startswith("@") or line.strip().startswith("async def"):
                inside_function = False
                new_lines.append(line)
                continue

            # Dedent by 4 spaces if line starts with 8+ spaces
            if line.startswith("        "):
                new_lines.append(line[4:])
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)

    # 5. Remove try-except blocks
    # This is complex - remove "try:" and all except/except Exception blocks
    # Strategy: Find try: and its matching except, remove both and dedent content

    # Remove "try:" line
    result = re.sub(r"    try:\s*\n", "", result)

    # Remove except blocks (ValidationError and general Exception)
    # Pattern: except ... : through the end of that except block
    result = re.sub(
        r"    except ValidationError as exc:.*?(?=\n    except|\n    \S|\Z)",
        "",
        result,
        flags=re.DOTALL,
    )
    result = re.sub(
        r"    except Exception as exc:.*?(?=\n@|\nasync def|\Z)",
        "",
        result,
        flags=re.DOTALL,
    )

    # 6. Remove execute_api_with_error_handling wrapper
    # Replace: result = await execute_api_with_error_handling("...", lambda: api_client.xxx(...))
    # With: result = await api_client.xxx(...)

    # Pattern 1: execute_api_with_error_handling with lambda
    result = re.sub(
        r"(\w+) = await execute_api_with_error_handling\(\s*"
        r'["\'][\w_]+["\']\s*,\s*'
        r"lambda:\s*(api_client\.\w+\([^)]*\))\s*"
        r"(?:,\s*context=\{[^}]*\})?\s*\)",
        r"\1 = await \2",
        result,
    )

    # 7. Remove dashboard recording calls
    result = re.sub(r"    _record_search_insights\([^)]*\)\s*\n", "", result)
    result = re.sub(r"    _record_paper_metadata\([^)]*\)\s*\n", "", result)
    result = re.sub(r"    dashboard_stats\.record_[^(]*\([^)]*\)\s*\n", "", result)

    # 8. Transform return statements to return json.dumps()
    # Pattern: return {"success": True, "data": ...}
    # Replace with: return json.dumps(..., ensure_ascii=False, indent=2)

    # Find all return statements with dict
    def replace_return(match: re.Match) -> str:
        indent = match.group(1)
        dict_content = match.group(2)

        # Check if it's an error return
        if '"success": False' in dict_content or "'success': False" in dict_content:
            # Error case - keep the dict structure but wrap in json.dumps
            return f"{indent}return json.dumps({dict_content}, ensure_ascii=False, indent=2)"

        # Success case - extract data field
        # Pattern: {"success": True, "data": {...}}
        data_match = re.search(r'"data":\s*({.*}|\[.*\])', dict_content, re.DOTALL)
        if data_match:
            data_value = data_match.group(1)
            return (
                f"{indent}return json.dumps({data_value}, ensure_ascii=False, indent=2)"
            )

        # Fallback - just wrap the whole dict
        return (
            f"{indent}return json.dumps({dict_content}, ensure_ascii=False, indent=2)"
        )

    result = re.sub(
        r"(\s+)return\s+(\{[^}]*\})",
        replace_return,
        result,
        flags=re.DOTALL,
    )

    # 9. Remove isinstance checks for error dict returns
    return re.sub(
        r"    if isinstance\(\w+, dict\):\s*\n\s*return \w+\s*\n\s*\n",
        "",
        result,
    )



def main() -> None:
    """Main conversion logic."""
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    content = server_path.read_text(encoding="utf-8")

    # Track conversions
    converted_count = 0
    failed_count = 0

    for tool in TOOLS:
        print(f"\n{'=' * 60}")
        print(f"Converting: {tool.name} (category: {tool.category})")
        print(f"{'=' * 60}")

        # Extract function
        extraction = extract_function_body(content, tool.name)
        if not extraction:
            print(f"❌ Failed to extract function: {tool.name}")
            failed_count += 1
            continue

        func_body, start_pos, end_pos = extraction

        # Transform function
        try:
            transformed = transform_function(func_body, tool)

            # Replace in content
            content = content[:start_pos] + transformed + content[end_pos:]

            print(f"✅ Successfully converted: {tool.name}")
            converted_count += 1

        except Exception as e:
            print(f"❌ Error converting {tool.name}: {e}")
            failed_count += 1
            continue

    # Add json import at top if not present
    if "import json" not in content:
        # Find first import statement and add json import
        import_match = re.search(r"^(import |from )", content, re.MULTILINE)
        if import_match:
            insert_pos = import_match.start()
            content = content[:insert_pos] + "import json\n" + content[insert_pos:]

    # Remove unused decorators and helpers
    print(f"\n{'=' * 60}")
    print("Removing unused code...")
    print(f"{'=' * 60}")

    # Remove mcp_error_handler decorator definition
    content = re.sub(
        r"def mcp_error_handler.*?(?=\ndef |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

    # Remove execute_api_with_error_handling function
    content = re.sub(
        r"async def execute_api_with_error_handling.*?(?=\nasync def |\ndef |\Z)",
        "",
        content,
        flags=re.DOTALL,
    )

    # Remove helper functions
    content = re.sub(
        r"def _record_search_insights.*?(?=\ndef |\Z)", "", content, flags=re.DOTALL
    )
    content = re.sub(
        r"def _record_paper_metadata.*?(?=\ndef |\Z)", "", content, flags=re.DOTALL
    )

    # Write back
    print(f"\n{'=' * 60}")
    print(f"Writing converted code to {server_path}")
    print(f"{'=' * 60}")

    server_path.write_text(content, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print("Conversion Summary")
    print(f"{'=' * 60}")
    print(f"✅ Converted: {converted_count}/{len(TOOLS)}")
    print(f"❌ Failed: {failed_count}/{len(TOOLS)}")
    print("\nNext steps:")
    print("1. Review the changes: git diff src/semantic_scholar_mcp/server.py")
    print("2. Run formatting: uv run --frozen ruff format .")
    print("3. Fix any remaining issues manually")
    print("4. Update tests to handle JSON string returns")


if __name__ == "__main__":
    main()
