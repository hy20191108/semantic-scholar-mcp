#!/bin/bash
# Batch replace decorators for all tools

FILE="src/semantic_scholar_mcp/server.py"

echo "Starting batch replacements..."

# Add search_papers
sed -i 's/@with_tool_instructions("search_papers")/@inject_yaml_instructions("search_papers", "paper")/g' "$FILE"

# Paper tools
sed -i 's/@with_tool_instructions("get_paper")/@inject_yaml_instructions("get_paper", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_paper_citations")/@inject_yaml_instructions("get_paper_citations", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_paper_references")/@inject_yaml_instructions("get_paper_references", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_paper_authors")/@inject_yaml_instructions("get_paper_authors", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("batch_get_papers")/@inject_yaml_instructions("batch_get_papers", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("bulk_search_papers")/@inject_yaml_instructions("bulk_search_papers", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("search_papers_match")/@inject_yaml_instructions("search_papers_match", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_paper_with_embeddings")/@inject_yaml_instructions("get_paper_with_embeddings", "paper")/g' "$FILE"
sed -i 's/@with_tool_instructions("search_papers_with_embeddings")/@inject_yaml_instructions("search_papers_with_embeddings", "paper")/g' "$FILE"

# Author tools
sed -i 's/@with_tool_instructions("get_author")/@inject_yaml_instructions("get_author", "author")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_author_papers")/@inject_yaml_instructions("get_author_papers", "author")/g' "$FILE"
sed -i 's/@with_tool_instructions("search_authors")/@inject_yaml_instructions("search_authors", "author")/g' "$FILE"
sed -i 's/@with_tool_instructions("batch_get_authors")/@inject_yaml_instructions("batch_get_authors", "author")/g' "$FILE"

# Prompts/AI tools
sed -i 's/@with_tool_instructions("get_recommendations_for_paper")/@inject_yaml_instructions("get_recommendations_for_paper", "prompts")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_recommendations_batch")/@inject_yaml_instructions("get_recommendations_batch", "prompts")/g' "$FILE"
sed -i 's/@with_tool_instructions("autocomplete_query")/@inject_yaml_instructions("autocomplete_query", "prompts")/g' "$FILE"
sed -i 's/@with_tool_instructions("search_snippets")/@inject_yaml_instructions("search_snippets", "prompts")/g' "$FILE"
sed -i 's/@with_tool_instructions("check_api_key_status")/@inject_yaml_instructions("check_api_key_status", "prompts")/g' "$FILE"

# Dataset tools
sed -i 's/@with_tool_instructions("get_dataset_releases")/@inject_yaml_instructions("get_dataset_releases", "dataset")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_dataset_info")/@inject_yaml_instructions("get_dataset_info", "dataset")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_dataset_download_links")/@inject_yaml_instructions("get_dataset_download_links", "dataset")/g' "$FILE"
sed -i 's/@with_tool_instructions("get_incremental_dataset_updates")/@inject_yaml_instructions("get_incremental_dataset_updates", "dataset")/g' "$FILE"

# PDF tools
sed -i 's/@with_tool_instructions("get_paper_fulltext")/@inject_yaml_instructions("get_paper_fulltext", "pdf")/g' "$FILE"

echo "Decorator replacements completed."

echo "Removing @mcp_error_handler decorators..."
sed -i '/@mcp_error_handler(tool_name=/d' "$FILE"

echo "Changing return types from ToolResult to str..."
sed -i 's/) -> ToolResult:/) -> str:/g' "$FILE"

echo "✅ All replacements completed!"
