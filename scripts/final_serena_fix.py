#!/usr/bin/env python3
"""
Final comprehensive fix for Serena compliance.
Removes all try blocks and fixes decorators.
"""

from pathlib import Path


def main():
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    skip_line = False

    # Tool name to category mapping
    tool_categories = {
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

    print("\nProcessing lines...")
    for i, line in enumerate(lines):
        if skip_line:
            skip_line = False
            continue

        # Remove standalone try: lines
        if line.strip() == "try:":
            print(f"  Removing try: at line {i + 1}")
            continue

        # Replace @with_tool_instructions with @inject_yaml_instructions
        for tool_name, category in tool_categories.items():
            if f'@with_tool_instructions("{tool_name}")' in line:
                new_line = f'@inject_yaml_instructions("{tool_name}", "{category}")\n'
                new_lines.append(new_line)
                print(f"  Replaced decorator for {tool_name} at line {i + 1}")
                skip_line = False  # Don't skip next line
                break
        else:
            # Remove @mcp_error_handler lines
            if "@mcp_error_handler(tool_name=" in line:
                print(f"  Removing @mcp_error_handler at line {i + 1}")
                continue

            # Replace ToolResult with str
            if ") -> ToolResult:" in line:
                line = line.replace(") -> ToolResult:", ") -> str:")
                print(f"  Changed return type at line {i + 1}")

            new_lines.append(line)

    # Write back
    print(f"\nWriting to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("\n✅ Fixed!")
    print("\nNext steps:")
    print("1. Run: uv run --frozen ruff format .")
    print("2. Run: uv run --frozen ruff check . --fix")
    print("3. Run: uv run --frozen pytest tests/")


if __name__ == "__main__":
    main()
