#!/usr/bin/env python3
"""
Add proper return statements with json.dumps() to all tool functions.
"""

import re
from pathlib import Path


def add_return_statements():
    """Add return json.dumps() statements to all tool functions."""

    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        content = f.read()

    # All tool functions that need return statements
    tools = [
        "search_papers",
        "get_paper",
        "get_paper_citations",
        "get_paper_references",
        "get_paper_authors",
        "batch_get_papers",
        "bulk_search_papers",
        "search_papers_match",
        "get_paper_with_embeddings",
        "search_papers_with_embeddings",
        "get_author",
        "get_author_papers",
        "search_authors",
        "batch_get_authors",
        "get_recommendations_for_paper",
        "get_recommendations_batch",
        "autocomplete_query",
        "search_snippets",
        "check_api_key_status",
        "get_dataset_releases",
        "get_dataset_info",
        "get_dataset_download_links",
        "get_incremental_dataset_updates",
        "get_paper_fulltext",
    ]

    for tool_name in tools:
        print(f"Processing {tool_name}...")

        # Find the function and check if it has proper return
        pattern = rf"async def {tool_name}\([^)]*\) -> str:.*?(?=\n@|\nasync def|\Z)"

        match = re.search(pattern, content, re.DOTALL)
        if match:
            func_content = match.group(0)

            # Check if function already has json.dumps return
            if "return json.dumps(" in func_content:
                print(f"  ✓ {tool_name} already has json.dumps return")
                continue

            # Find variable assignments that should be returned
            # Common patterns: result =, paper =, papers =, author =, etc.
            var_patterns = [
                r"(\s+)(result|paper|papers|author|authors|citations|references|info|releases|links|updates|suggestions) = await",
                r"(\s+)(result|paper|papers|author|authors|citations|references|info|releases|links|updates|suggestions) = \[",
                r"(\s+)(result|paper|papers|author|authors|citations|references|info|releases|links|updates|suggestions) = \{",
            ]

            for var_pattern in var_patterns:
                var_match = re.search(var_pattern, func_content)
                if var_match:
                    var_name = var_match.group(2)
                    indent = var_match.group(1)

                    # Add return statement at the end of the function
                    # Find the last line of the function
                    lines = func_content.split("\n")

                    # Add return if not present
                    if not any("return" in line for line in lines):
                        # Insert return statement before the end
                        return_statement = f"{indent}return json.dumps({var_name}, ensure_ascii=False, indent=2)"

                        # Find where to insert (before the next function or at the end)
                        insert_pos = len(func_content)

                        # Replace in content
                        new_func = (
                            func_content[:insert_pos].rstrip()
                            + "\n"
                            + return_statement
                            + "\n"
                        )
                        content = content.replace(func_content, new_func)
                        print(f"  + Added return json.dumps({var_name}) to {tool_name}")
                    break

    # Add json import if not present
    if "import json" not in content:
        # Find first import
        import_match = re.search(r"^import ", content, re.MULTILINE)
        if import_match:
            content = (
                content[: import_match.start()]
                + "import json\n"
                + content[import_match.start() :]
            )
            print("+ Added import json")

    # Write back
    print(f"\nWriting to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("\n✅ Return statements added!")


if __name__ == "__main__":
    add_return_statements()
