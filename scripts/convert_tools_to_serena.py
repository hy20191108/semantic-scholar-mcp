#!/usr/bin/env python3
"""
AST-based tool conversion to Serena-compliant pattern.

This script uses Python's ast module to precisely locate and transform tool functions.
"""

import re
from pathlib import Path
from typing import NamedTuple


class ToolInfo(NamedTuple):
    """Information about a tool function."""

    name: str
    category: str


# All 24 tools with their categories
TOOLS = [
    # Paper tools (10)
    ToolInfo("search_papers", "paper"),
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


def find_function_in_source(source: str, func_name: str) -> tuple[int, int] | None:
    """
    Find function definition line numbers in source code.

    Returns:
        Tuple of (start_line, end_line) or None if not found
    """
    lines = source.split("\n")

    # Find function definition
    func_pattern = rf"^async def {re.escape(func_name)}\("
    start_line = None

    for i, line in enumerate(lines):
        if re.match(func_pattern, line):
            start_line = i
            break

    if start_line is None:
        # Try finding with decorators
        for i, line in enumerate(lines):
            if re.search(rf"async def {re.escape(func_name)}\(", line):
                # Go back to find first decorator
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("@"):
                    j -= 1
                start_line = j + 1
                break

    if start_line is None:
        return None

    # Find end of function (next function or end of file)
    end_line = len(lines)
    for i in range(start_line + 1, len(lines)):
        line = lines[i]
        # Next function starts
        if (
            line
            and not line[0].isspace()
            and (
                line.startswith(("@", "async def", "def"))
            )
        ):
            end_line = i
            break
        # Next decorator at same level
        if line.startswith("@") and i > start_line + 10:  # Skip immediate decorators
            end_line = i
            break

    return (start_line, end_line)


def transform_tool_function(source_lines: list[str], tool: ToolInfo) -> list[str]:
    """
    Transform a tool function to Serena-compliant pattern.

    Strategy:
    1. Replace decorators
    2. Change return type annotation
    3. Remove try-except and RequestContext
    4. Simplify function body
    5. Return json.dumps()
    """
    result = []
    inside_try = False
    inside_except = False
    inside_request_context = False
    context_indent = 0
    skip_lines = 0

    for _i, line in enumerate(source_lines):
        if skip_lines > 0:
            skip_lines -= 1
            continue

        # 1. Replace @with_tool_instructions
        if f'@with_tool_instructions("{tool.name}")' in line:
            result.append(
                f'@inject_yaml_instructions("{tool.name}", "{tool.category}")'
            )
            continue

        # 2. Remove @mcp_error_handler
        if f'@mcp_error_handler(tool_name="{tool.name}")' in line:
            continue

        # 3. Change return type annotation
        if ") -> dict[str, Any]:" in line:
            result.append(line.replace(") -> dict[str, Any]:", ") -> str:"))
            continue

        # 4. Handle "with RequestContext():" line
        if "with RequestContext" in line:
            inside_request_context = True
            context_indent = len(line) - len(line.lstrip())
            continue

        # 5. Handle "try:" line
        if line.strip() == "try:":
            if inside_request_context:
                inside_try = True
                len(line) - len(line.lstrip())
                continue

        # 6. Skip except blocks entirely
        if "except" in line and ":" in line:
            inside_except = True
            continue

        # If in except block, skip until we're back at function level
        if inside_except:
            # Check if we're out of the except block
            if line and len(line) - len(line.lstrip()) <= context_indent:
                inside_except = False
                inside_try = False
                inside_request_context = False
                # Don't append - this line is part of except cleanup
            continue

        # 7. Process lines based on context
        if inside_request_context:
            # Inside context, dedent by appropriate amount
            if inside_try:
                # Inside try block - dedent by 8 spaces (context + try)
                if line and line.startswith(" " * (context_indent + 8)):
                    result.append(line[8:])
                elif line.strip() == "":
                    result.append(line)
                else:
                    # Less indented - might be end of try
                    result.append(line)
            else:
                # Inside context but not try - dedent by 4 spaces
                if line and line.startswith(" " * (context_indent + 4)):
                    result.append(line[4:])
                elif line.strip() == "":
                    result.append(line)
                else:
                    result.append(line)
        else:
            result.append(line)

    return result


def simplify_function_body(lines: list[str]) -> list[str]:
    """
    Simplify function body by removing Serena-incompatible patterns.

    Removals:
    - execute_api_with_error_handling wrapper
    - isinstance(result, dict) checks
    - dashboard recording calls
    - Complex error returns
    """
    result = []
    skip_next = 0

    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            continue

        # Remove execute_api_with_error_handling wrapper
        if "await execute_api_with_error_handling(" in line:
            # Extract the full call across multiple lines
            j = i
            full_call = ""
            indent = " " * (len(line) - len(line.lstrip()))

            # Collect full call
            while j < len(lines):
                full_call += lines[j]
                if lines[j].rstrip().endswith(")"):
                    break
                j += 1

            # Extract variable name and api call
            var_match = re.search(
                r"(\w+)\s*=\s*await execute_api_with_error_handling", full_call
            )
            api_match = re.search(
                r"lambda:\s*(api_client\.\w+\([^)]*(?:\([^)]*\))*[^)]*\))",
                full_call,
                re.DOTALL,
            )

            if var_match and api_match:
                var_name = var_match.group(1)
                api_call = api_match.group(1)
                # Clean up the API call
                api_call = re.sub(r"\s+", " ", api_call)
                result.append(f"{indent}{var_name} = await {api_call}")
                skip_next = j - i
                continue

        # Remove isinstance(result, dict) checks and their returns
        if "if isinstance(" in line and ", dict):" in line:
            # Find the matching return statement
            j = i + 1
            while j < len(lines) and "return" not in lines[j]:
                j += 1
            skip_next = j - i
            continue

        # Remove dashboard recording
        if "_record_search_insights(" in line or "_record_paper_metadata(" in line:
            continue
        if "dashboard_stats.record_" in line:
            continue
        if "dashboard_stats." in line:
            continue

        # Transform return statements with {"success": True, "data": ...}
        if "return {" in line and '"success": True' in line:
            # Collect the full return statement
            j = i
            full_return = ""
            brace_count = 0

            while j < len(lines):
                curr_line = lines[j]
                full_return += curr_line
                brace_count += curr_line.count("{") - curr_line.count("}")
                if brace_count <= 0:
                    break
                j += 1

            # Extract data value
            data_match = re.search(
                r'"data":\s*([^,}]+(?:\{[^}]*\})?[^,}]*)', full_return, re.DOTALL
            )
            if data_match:
                data_value = data_match.group(1).strip()
                indent = " " * (len(line) - len(line.lstrip()))
                result.append(
                    f"{indent}return json.dumps({data_value}, ensure_ascii=False, indent=2)"
                )
                skip_next = j - i
                continue

        # Transform simple dict returns without success/data structure
        if "return {" in line and '"success"' not in line:
            # This might be a simple dict return that needs json.dumps
            j = i
            full_return = ""
            brace_count = 0

            while j < len(lines):
                curr_line = lines[j]
                full_return += curr_line
                brace_count += curr_line.count("{") - curr_line.count("}")
                if brace_count <= 0:
                    break
                j += 1

            # Check if it's a dict literal
            if full_return.strip().startswith("return {"):
                indent = " " * (len(line) - len(line.lstrip()))
                dict_content = full_return.replace("return ", "").strip()
                result.append(
                    f"{indent}return json.dumps({dict_content}, ensure_ascii=False, indent=2)"
                )
                skip_next = j - i
                continue

        result.append(line)

    return result


def main() -> None:
    """Main conversion logic."""
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    source = server_path.read_text(encoding="utf-8")

    # First, update imports
    print("\nUpdating imports...")

    # Add json import at the beginning
    if "import json" not in source:
        import_pos = source.find("import ")
        if import_pos != -1:
            source = source[:import_pos] + "import json\n" + source[import_pos:]

    # Update instruction_loader import
    source = re.sub(
        r"from \.instruction_loader import load_all_instructions",
        "from .instruction_loader import load_all_instructions, inject_yaml_instructions",
        source,
    )

    # Remove unused imports
    source = re.sub(r"from \.utils import.*RequestContext.*\n", "", source)
    source = re.sub(
        r"from \.utils import.*execute_api_with_error_handling.*\n", "", source
    )
    source = re.sub(r"from \.utils import.*mcp_error_handler.*\n", "", source)
    source = re.sub(r"from \.utils import.*with_tool_instructions.*\n", "", source)

    lines = source.split("\n")

    # Track conversions
    converted = []
    failed = []

    # Convert all tools
    tools_to_convert = TOOLS

    for tool in tools_to_convert:
        print(f"\n{'=' * 60}")
        print(f"Converting: {tool.name} (category: {tool.category})")
        print(f"{'=' * 60}")

        # Find function
        location = find_function_in_source("\n".join(lines), tool.name)
        if not location:
            print(f"❌ Failed to locate function: {tool.name}")
            failed.append(tool.name)
            continue

        start_line, end_line = location
        func_lines = lines[start_line:end_line]

        print(f"Found at lines {start_line + 1}-{end_line}")

        # Transform
        try:
            transformed = transform_tool_function(func_lines, tool)
            transformed = simplify_function_body(transformed)

            # Replace in source
            lines[start_line:end_line] = transformed

            print(f"✅ Successfully converted: {tool.name}")
            converted.append(tool.name)

        except Exception as e:
            print(f"❌ Error converting {tool.name}: {e}")
            failed.append(tool.name)

    # Reconstruct source
    new_source = "\n".join(lines)

    # Final cleanup with regex
    print(f"\n{'=' * 60}")
    print("Final cleanup...")
    print(f"{'=' * 60}")

    # Remove unused helper functions
    new_source = re.sub(
        r"\ndef _record_search_insights\(.*?\n(?=\ndef |\n@|\Z)",
        "\n",
        new_source,
        flags=re.DOTALL,
    )
    new_source = re.sub(
        r"\ndef _record_paper_metadata\(.*?\n(?=\ndef |\n@|\Z)",
        "\n",
        new_source,
        flags=re.DOTALL,
    )
    new_source = re.sub(
        r"\nasync def execute_api_with_error_handling\(.*?\n(?=\ndef |\n@|\nasync def |\Z)",
        "\n",
        new_source,
        flags=re.DOTALL,
    )

    # Write back
    print(f"\nWriting to {server_path}")
    server_path.write_text(new_source, encoding="utf-8")

    print(f"\n{'=' * 60}")
    print("Conversion Summary")
    print(f"{'=' * 60}")
    print(f"✅ Converted: {len(converted)} tools")
    print(f"   {', '.join(converted[:5])}{'...' if len(converted) > 5 else ''}")
    print(f"❌ Failed: {len(failed)} tools")
    if failed:
        print(f"   {', '.join(failed)}")
    print("\nNext steps:")
    print("1. Review changes: git diff src/semantic_scholar_mcp/server.py")
    print("2. Format code: uv run --frozen ruff format .")
    print("3. Manual fixes: Check and fix any remaining issues")
    print("4. Update tests: Adapt to JSON string returns")


if __name__ == "__main__":
    main()
