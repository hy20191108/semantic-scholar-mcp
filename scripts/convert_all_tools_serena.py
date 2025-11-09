#!/usr/bin/env python3
"""
Complete conversion of all tools to Serena-compliant pattern.
This script uses regex to ensure all decorators are properly replaced.
"""

import re
from pathlib import Path


def convert_tool_body(tool_name: str, source: str, category: str) -> str:
    """Convert a single tool's body to Serena-compliant pattern."""

    # First, find and replace decorators for this tool
    # Pattern to find @with_tool_instructions and @mcp_error_handler
    decorator_pattern = rf"""
    (@with_tool_instructions\("{tool_name}\"\)\s*)?
    (@mcp\.tool\(\)\s*)?
    (@mcp_error_handler\(tool_name="{tool_name}"\)\s*)?
    (async def {re.escape(tool_name)}\([^{{]+\) -> )dict\[str, Any\]:
    """

    # Replace with Serena-compliant decorators
    replacement = rf"""@inject_yaml_instructions("{tool_name}", "{category}")
@mcp.tool()
\4str:"""

    source = re.sub(
        decorator_pattern, replacement, source, flags=re.VERBOSE | re.MULTILINE
    )

    # Now find the function body and clean it up
    # Find function start
    func_pattern = rf"async def {re.escape(tool_name)}\("
    match = re.search(func_pattern, source)

    if not match:
        return source

    func_start = match.start()

    # Find function end (next @inject or end of file)
    next_func = re.search(r"\n@inject_yaml_instructions\(", source[func_start + 10 :])
    func_end = func_start + 10 + next_func.start() if next_func else len(source)

    func_body = source[func_start:func_end]

    # Remove try: line
    func_body = re.sub(r"\n        try:\s*\n", "\n", func_body)

    # Remove except ValidationError block
    func_body = re.sub(
        r"\n        except ValidationError as exc:.*?(?=\n        except |\n        \n|\n@|\Z)",
        "",
        func_body,
        flags=re.DOTALL,
    )

    # Remove except Exception block
    func_body = re.sub(
        r"\n        except Exception as exc:.*?(?=\n\n@|\n@|\Z)",
        "",
        func_body,
        flags=re.DOTALL,
    )

    # Dedent function body by 4 spaces (from try: removal)
    lines = func_body.split("\n")
    dedented_lines = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            dedented_lines.append(line)
            continue

        # Don't dedent decorators and function signature
        if line.strip().startswith("@") or line.strip().startswith("async def"):
            dedented_lines.append(line)
            continue

        # Don't dedent docstring
        if '"""' in line:
            dedented_lines.append(line)
            continue

        # Dedent by 4 spaces if starts with 12+ spaces
        if line.startswith("            "):
            dedented_lines.append(line[4:])
        else:
            dedented_lines.append(line)

    func_body = "\n".join(dedented_lines)

    # Step 4: Remove execute_api_with_error_handling wrapper
    func_body = re.sub(
        r"(\w+) = await execute_api_with_error_handling\(\s*"
        r'"[^"]+"\s*,\s*'
        r"lambda:\s*(api_client\.[^)]+\([^)]*\))\s*"
        r"(?:,\s*context=[^)]+)?\s*\)",
        r"\1 = await \2",
        func_body,
        flags=re.DOTALL,
    )

    # Step 5: Remove isinstance(result, dict) checks
    func_body = re.sub(
        r"        if isinstance\(\w+, dict\):\s*\n\s+return \w+\s*\n\s*\n",
        "",
        func_body,
    )

    # Step 6: Remove dashboard recording
    func_body = re.sub(r"        _record_search_insights\([^)]+\)\s*\n", "", func_body)
    func_body = re.sub(r"        _record_paper_metadata\([^)]+\)\s*\n", "", func_body)
    func_body = re.sub(
        r"        for payload in [^:]+:\s*\n\s+_record_paper_metadata[^)]+\)\s*\n",
        "",
        func_body,
    )

    # Step 7: Transform return statements
    # Pattern: return {"success": True, "data": {...}}
    # Replace with: return json.dumps({...}, ensure_ascii=False, indent=2)

    # Find all return statements with success/data structure
    def replace_return(match):
        indent = match.group(1)

        # Check if it's an error return
        if '"success": False' in match.group(0) or "'success': False" in match.group(0):
            # For errors, wrap entire dict in json.dumps
            dict_content = match.group(2)
            return f"{indent}return json.dumps({dict_content}, ensure_ascii=False, indent=2)"

        # For success, extract data field
        data_match = re.search(
            r'"data":\s*(\{[^}]+\}|[^,}]+)', match.group(2), re.DOTALL
        )
        if data_match:
            data_value = data_match.group(1)
            return (
                f"{indent}return json.dumps({data_value}, ensure_ascii=False, indent=2)"
            )

        # Fallback
        dict_content = match.group(2)
        return (
            f"{indent}return json.dumps({dict_content}, ensure_ascii=False, indent=2)"
        )

    func_body = re.sub(
        r"(\s+)return\s+(\{[^}]+\})", replace_return, func_body, flags=re.DOTALL
    )

    # Replace in source
    return source[:func_start] + func_body + source[func_end:]



def main():
    """Main conversion logic."""
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    source = server_path.read_text(encoding="utf-8")

    # All tools with their categories
    tools = {
        # Paper tools
        "search_papers": "paper",
        "get_paper": "paper",
        "get_paper_citations": "paper",
        "get_paper_references": "paper",
        "get_paper_authors": "paper",
        "batch_get_papers": "paper",
        "bulk_search_papers": "paper",
        "search_papers_match": "paper",
        "get_paper_with_embeddings": "paper",
        "search_papers_with_embeddings": "paper",
        # Author tools
        "get_author": "author",
        "get_author_papers": "author",
        "search_authors": "author",
        "batch_get_authors": "author",
        # Prompts tools
        "get_recommendations_for_paper": "prompts",
        "get_recommendations_batch": "prompts",
        "autocomplete_query": "prompts",
        "search_snippets": "prompts",
        "check_api_key_status": "prompts",
        # Dataset tools
        "get_dataset_releases": "dataset",
        "get_dataset_info": "dataset",
        "get_dataset_download_links": "dataset",
        "get_incremental_dataset_updates": "dataset",
        # PDF tools
        "get_paper_fulltext": "pdf",
    }

    converted = 0
    for tool, category in tools.items():
        print(f"Converting {tool} ({category})...")
        source = convert_tool_body(tool, source, category)
        converted += 1

    # Write back
    print(f"\nWriting to {server_path}")
    server_path.write_text(source, encoding="utf-8")

    print(f"\n✅ Converted {converted} tools")
    print("Next: Run ruff format and check for issues")


if __name__ == "__main__":
    main()
