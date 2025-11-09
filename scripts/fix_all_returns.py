#!/usr/bin/env python3
"""
Fix all return statements in tool functions.
"""

from pathlib import Path


def fix_all_returns():
    """Fix return statements for all tool functions."""

    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Track changes
    changes = []

    # Tool-specific fixes
    fixes = {
        # Each tool and its expected variable to return
        "get_paper": "paper",
        "get_paper_citations": "citations",
        "get_paper_references": "references",
        "get_paper_authors": "result",
        "batch_get_papers": "papers",
        "bulk_search_papers": "papers",
        "search_papers_match": "result",
        "get_paper_with_embeddings": "paper",
        "search_papers_with_embeddings": "result",
        "get_author": "author",
        "get_author_papers": "result",
        "search_authors": "result",
        "batch_get_authors": "authors",
        "get_recommendations_for_paper": "papers",
        "get_recommendations_batch": "papers",
        "autocomplete_query": "suggestions",
        "search_snippets": "result",
        "check_api_key_status": "api_key_data",
        "get_dataset_releases": "releases",
        "get_dataset_info": "info",
        "get_dataset_download_links": "links",
        "get_incremental_dataset_updates": "updates",
        "get_paper_fulltext": "result",
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a function definition we need to fix
        for func_name, var_name in fixes.items():
            if f"async def {func_name}(" in line:
                print(f"Found {func_name} at line {i + 1}")

                # Look for the end of the function
                j = i + 1
                func_indent = len(line) - len(line.lstrip())

                # Find the last line of the function
                end_of_func = None
                while j < len(lines):
                    next_line = lines[j]
                    # Check if we've hit the next function or decorator
                    if next_line.strip() and not next_line[0].isspace():
                        end_of_func = j
                        break
                    if next_line.strip().startswith("@"):
                        end_of_func = j
                        break
                    if (
                        "async def " in next_line
                        and len(next_line) - len(next_line.lstrip()) <= func_indent
                    ):
                        end_of_func = j
                        break
                    j += 1

                if end_of_func is None:
                    end_of_func = len(lines)

                # Check if function already has a return
                has_return = False
                for k in range(i, end_of_func):
                    if "return json.dumps(" in lines[k]:
                        has_return = True
                        print(f"  {func_name} already has json.dumps return")
                        break

                if not has_return:
                    # Add return statement before the end of function
                    # Find the last non-empty line
                    insert_pos = end_of_func - 1
                    while insert_pos > i and not lines[insert_pos].strip():
                        insert_pos -= 1

                    # Insert return statement
                    return_line = f"    return json.dumps({var_name}, ensure_ascii=False, indent=2)\n"
                    lines.insert(insert_pos + 1, return_line)
                    changes.append(f"Added return to {func_name}")
                    print(f"  + Added return json.dumps({var_name}) to {func_name}")

                break

        i += 1

    # Write back
    print(f"\nWriting to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n✅ Fixed {len(changes)} functions:")
    for change in changes:
        print(f"  - {change}")


if __name__ == "__main__":
    fix_all_returns()
