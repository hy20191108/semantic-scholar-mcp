#!/usr/bin/env python3
"""
Batch fix all issues in server.py for Serena compliance.
"""

import re
from pathlib import Path


def main():
    """Main function to fix all issues."""
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    content = server_path.read_text(encoding="utf-8")

    # Step 1: Remove all orphan try: statements
    print("\n1. Removing orphan try statements...")
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for try: statement
        if line.strip() == "try:":
            # Look ahead for except
            has_except = False
            for j in range(i + 1, min(i + 30, len(lines))):
                if "except" in lines[j] and ":" in lines[j]:
                    has_except = True
                    break
                # Stop if we hit another function
                if lines[j].strip().startswith("@") or "async def " in lines[j]:
                    break

            if not has_except:
                print(f"  Removing orphan try at line {i + 1}")
                i += 1  # Skip the try line
                continue

        result.append(line)
        i += 1

    content = "\n".join(result)

    # Step 2: Remove all "with RequestContext():" lines and dedent
    print("\n2. Removing RequestContext blocks...")
    lines = content.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if "with RequestContext" in line:
            print(f"  Removing RequestContext at line {i + 1}")
            # Skip this line, dedent following lines
            i += 1

            # Process following indented lines
            while i < len(lines):
                next_line = lines[i]
                # If line is less indented, we're done with this block
                if next_line and not next_line[0].isspace():
                    break
                if next_line.strip() and len(next_line) - len(next_line.lstrip()) < 4:
                    break

                # Dedent the line
                if next_line.startswith("    "):
                    result.append(next_line[4:])
                else:
                    result.append(next_line)
                i += 1
            continue

        result.append(line)
        i += 1

    content = "\n".join(result)

    # Step 3: Add missing definitions at the top of the file
    print("\n3. Adding missing definitions...")

    # Find where to insert (after imports)
    import_section_end = 0
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith(("from ", "import ")):
            import_section_end = i

    # Prepare additions
    additions = []

    # Add logger if needed
    if "logger = " not in content and "logger." in content:
        additions.append("logger = get_logger(__name__)")

    # Add mcp if needed
    if "mcp = " not in content and "@mcp." in content:
        additions.append("""mcp = FastMCP(
    "Semantic Scholar MCP Server",
    version="0.2.2"
)""")

    # Add type definitions
    if "ToolResult = " not in content and "ToolResult" in content:
        additions.append("ToolResult = dict[str, Any]  # Type alias for tool results")

    if "TResult = " not in content and "TResult" in content:
        additions.append("TResult = TypeVar('TResult')")

    # Insert additions
    if additions:
        lines.insert(
            import_section_end + 2,
            "\n# Missing definitions added for Serena compliance",
        )
        lines.insert(import_section_end + 3, "\n".join(additions))
        lines.insert(import_section_end + 4, "")

    content = "\n".join(lines)

    # Step 4: Replace @with_tool_instructions with @inject_yaml_instructions
    print("\n4. Replacing decorators...")

    # Define all tools and their categories
    tools = {
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
        "get_author": "author",
        "get_author_papers": "author",
        "search_authors": "author",
        "batch_get_authors": "author",
        "get_recommendations_for_paper": "prompts",
        "get_recommendations_batch": "prompts",
        "autocomplete_query": "prompts",
        "search_snippets": "prompts",
        "check_api_key_status": "prompts",
        "get_dataset_releases": "dataset",
        "get_dataset_info": "dataset",
        "get_dataset_download_links": "dataset",
        "get_incremental_dataset_updates": "dataset",
        "get_paper_fulltext": "pdf",
    }

    for tool_name, category in tools.items():
        # Replace @with_tool_instructions
        old_decorator = f'@with_tool_instructions("{tool_name}")'
        new_decorator = f'@inject_yaml_instructions("{tool_name}", "{category}")'
        content = content.replace(old_decorator, new_decorator)

        # Remove @mcp_error_handler
        error_decorator = f'@mcp_error_handler(tool_name="{tool_name}")'
        content = content.replace(error_decorator + "\n", "")

    # Step 5: Change return types from dict[str, Any] to str
    print("\n5. Changing return types...")
    content = re.sub(r"\) -> dict\[str, Any\]:", r") -> str:", content)
    content = re.sub(r"\) -> ToolResult:", r") -> str:", content)

    # Step 6: Fix return statements
    print("\n6. Fixing return statements...")

    # Pattern for {"success": True, "data": ...}
    content = re.sub(
        r'return \{"success": True, "data": ([^}]+)\}',
        r"return json.dumps(\1, ensure_ascii=False, indent=2)",
        content,
    )

    # Pattern for {"success": False, ...}
    content = re.sub(
        r'return \{"success": False[^}]+\}',
        r'raise Exception("Operation failed")',
        content,
    )

    # Step 7: Remove helper function calls
    print("\n7. Removing helper function calls...")
    content = re.sub(r"_record_search_insights\([^)]+\)\n?", "", content)
    content = re.sub(r"_record_paper_metadata\([^)]+\)\n?", "", content)
    content = re.sub(r"dashboard_stats\.[^(]+\([^)]+\)\n?", "", content)

    # Step 8: Clean up execute_api_with_error_handling
    print("\n8. Simplifying API calls...")
    content = re.sub(
        r"await execute_api_with_error_handling\([^,]+,\s*lambda:\s*(api_client\.[^)]+\))[^)]*\)",
        r"await \1",
        content,
    )

    # Step 9: Clean up multiple blank lines
    print("\n9. Cleaning up...")
    content = re.sub(r"\n\n\n+", "\n\n", content)

    # Write back
    print(f"\n10. Writing to {server_path}")
    server_path.write_text(content, encoding="utf-8")

    print("\n✅ Batch fix complete!")
    print("\nNext steps:")
    print("1. Run: uv run --frozen ruff format .")
    print("2. Run: uv run --frozen pytest tests/")
    print("3. Review changes with: git diff")


if __name__ == "__main__":
    main()
