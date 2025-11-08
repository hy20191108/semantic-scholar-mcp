"""Load and cache tool instruction templates from external files."""

from functools import lru_cache
from pathlib import Path
from typing import Final

from core.logging import get_logger

logger = get_logger(__name__)

# Base directory for instruction templates
INSTRUCTIONS_DIR: Final[Path] = (
    Path(__file__).parent / "resources" / "tool_instructions"
)

# Tool name to template file mapping (category/tool_name.md)
TOOL_TEMPLATE_MAPPING: Final[dict[str, str]] = {
    # Paper tools
    "search_papers": "paper/search_papers.md",
    "get_paper": "paper/get_paper.md",
    "get_paper_citations": "paper/get_paper_citations.md",
    "get_paper_references": "paper/get_paper_references.md",
    "get_paper_authors": "paper/get_paper_authors.md",
    "batch_get_papers": "paper/batch_get_papers.md",
    "bulk_search_papers": "paper/bulk_search_papers.md",
    "search_papers_match": "paper/search_papers_match.md",
    "get_paper_with_embeddings": "paper/get_paper_with_embeddings.md",
    "search_papers_with_embeddings": "paper/search_papers_with_embeddings.md",
    # Author tools
    "search_authors": "author/search_authors.md",
    "get_author": "author/get_author.md",
    "get_author_papers": "author/get_author_papers.md",
    "batch_get_authors": "author/batch_get_authors.md",
    # Dataset tools
    "get_dataset_releases": "dataset/get_dataset_releases.md",
    "get_dataset_info": "dataset/get_dataset_info.md",
    "get_dataset_download_links": "dataset/get_dataset_download_links.md",
    "get_incremental_dataset_updates": "dataset/get_incremental_dataset_updates.md",
    # PDF tools
    "get_paper_fulltext": "pdf/get_paper_fulltext.md",
    # AI/Prompts/Advanced search tools
    "get_recommendations_for_paper": "prompts/get_recommendations_for_paper.md",
    "get_recommendations_batch": "prompts/get_recommendations_batch.md",
    "autocomplete_query": "prompts/autocomplete_query.md",
    "search_snippets": "prompts/search_snippets.md",
    "check_api_key_status": "prompts/check_api_key_status.md",
}


def _default_instruction(tool_name: str) -> str:
    """Return a fallback instruction block for tools without explicit guidance."""
    return (
        "### Next Steps\n"
        f"- Review the `{tool_name}` output and capture follow-up questions.\n"
        "- Ask for summaries or comparisons based on your goal.\n"
        "- Run adjacent tools if you need supporting context.\n"
    )


@lru_cache(maxsize=128)
def _load_instruction_template(template_path: str) -> str:
    """Load instruction template from file with caching."""
    full_path = INSTRUCTIONS_DIR / template_path

    try:
        if not full_path.exists():
            logger.debug(
                "Instruction template not found, using default",
                template_path=template_path,
            )
            return ""

        with open(full_path, encoding="utf-8") as f:
            content = f.read().strip()

        logger.debug(
            "Loaded instruction template",
            template_path=template_path,
            content_length=len(content),
        )
        return content

    except Exception as e:
        logger.warning(
            "Failed to load instruction template, using default",
            template_path=template_path,
            error=str(e),
        )
        return ""


def load_tool_instructions() -> dict[str, str]:
    """Load all tool instructions from external template files."""
    instructions: dict[str, str] = {}

    for tool_name, template_path in TOOL_TEMPLATE_MAPPING.items():
        content = _load_instruction_template(template_path)

        # Use default instruction if template is empty or not found
        if not content:
            content = _default_instruction(tool_name)

        instructions[tool_name] = content

    logger.info(
        "Loaded tool instructions",
        total_tools=len(instructions),
        from_templates=sum(1 for v in instructions.values() if "Review the `" not in v),
    )

    return instructions


def get_instruction(tool_name: str) -> str:
    """Get instruction for a specific tool, with fallback to default."""
    template_path = TOOL_TEMPLATE_MAPPING.get(tool_name)

    if not template_path:
        logger.debug(
            "No template mapping for tool, using default",
            tool_name=tool_name,
        )
        return _default_instruction(tool_name)

    content = _load_instruction_template(template_path)
    return content if content else _default_instruction(tool_name)


def clear_instruction_cache() -> None:
    """Clear the instruction template cache (useful for testing/development)."""
    _load_instruction_template.cache_clear()
    logger.debug("Cleared instruction template cache")
