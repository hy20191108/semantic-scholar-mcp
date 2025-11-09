"""
Load and inject tool instruction templates from YAML files.

This module provides YAML-based tool instruction loading and automatic
docstring injection, inspired by Serena's architecture.
"""

import inspect
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Final, TypedDict

import yaml

from core.logging import get_logger

logger = get_logger(__name__)

# Base directory for instruction templates
INSTRUCTIONS_DIR: Final[Path] = (
    Path(__file__).parent / "resources" / "tool_instructions"
)


class ToolInstruction(TypedDict, total=False):
    """Structure of a tool instruction YAML file."""

    tool_name: str
    category: str
    description: str
    next_steps: list[str]


@lru_cache(maxsize=128)
def load_tool_instruction(tool_name: str, category: str) -> ToolInstruction:
    """
    Load tool instruction from YAML file (with LRU caching).

    Args:
        tool_name: Name of the tool (e.g., 'search_papers')
        category: Category directory (e.g., 'paper', 'author')

    Returns:
        Dictionary containing tool instruction data
    """
    yaml_path = INSTRUCTIONS_DIR / category / f"{tool_name}.yml"

    # Fallback to empty instruction if file not found
    if not yaml_path.exists():
        logger.debug(
            "Instruction YAML not found, using empty",
            tool_name=tool_name,
            category=category,
            path=str(yaml_path),
        )
        return {
            "tool_name": tool_name,
            "category": category,
            "description": "",
            "next_steps": [],
        }

    try:
        with open(yaml_path, encoding="utf-8") as f:
            data: ToolInstruction = yaml.safe_load(f)

        logger.debug(
            "Loaded instruction YAML",
            tool_name=tool_name,
            category=category,
            next_steps_count=len(data.get("next_steps", [])),
        )

        return data

    except Exception as e:
        logger.warning(
            "Failed to load instruction YAML, using empty",
            tool_name=tool_name,
            category=category,
            error=str(e),
        )
        return {
            "tool_name": tool_name,
            "category": category,
            "description": "",
            "next_steps": [],
        }


def format_next_steps(next_steps: list[str]) -> str:
    """
    Format next steps list as docstring-compatible text.

    Args:
        next_steps: List of next step instructions

    Returns:
        Formatted string ready for docstring injection
    """
    if not next_steps:
        return ""

    formatted_lines = ["Next Steps:"]
    for step in next_steps:
        # Add bullet point if not already present
        if not step.strip().startswith("-"):
            formatted_lines.append(f"    - {step.strip()}")
        else:
            formatted_lines.append(f"    {step.strip()}")

    return "\n".join(formatted_lines)


def inject_yaml_instructions(tool_name: str, category: str) -> Callable:
    """
    Decorator to inject YAML-based instructions into tool docstring.

    This decorator reads tool instructions from YAML files and appends them
    to the tool function's docstring, following Serena's pattern of providing
    guidance to the LLM about how to use the tool effectively.

    Args:
        tool_name: Name of the tool (must match YAML filename)
        category: Category directory (paper/author/dataset/pdf/prompts)

    Returns:
        Decorated function with enhanced docstring

    Example:
        ```python
        @inject_yaml_instructions("search_papers", "paper")
        async def search_papers(query: str) -> str:
            '''Search for papers.'''
            ...
        ```

    The decorator will append Next Steps guidance from the YAML file:
        ```
        Search for papers.

        Next Steps:
            - Review the returned papers list
            - Request summaries of interesting papers
            - Refine query if needed
        ```
    """

    def decorator(func: Callable) -> Callable:
        # Load instruction from YAML
        instruction = load_tool_instruction(tool_name, category)

        # Get original docstring
        original_doc = inspect.getdoc(func) or ""

        # Build enhanced docstring
        parts = [original_doc]

        # Add Next Steps if available
        next_steps = instruction.get("next_steps", [])
        if next_steps:
            next_steps_text = format_next_steps(next_steps)
            parts.append(f"\n{next_steps_text}")

        # Update function docstring
        enhanced_doc = "\n".join(parts)
        func.__doc__ = enhanced_doc

        logger.debug(
            "Injected YAML instructions into docstring",
            tool_name=tool_name,
            category=category,
            original_length=len(original_doc),
            enhanced_length=len(enhanced_doc),
        )

        return func

    return decorator


def clear_instruction_cache() -> None:
    """Clear the instruction template cache (useful for testing/development)."""
    load_tool_instruction.cache_clear()
    logger.debug("Cleared instruction YAML cache")


# Backward compatibility: functions for loading all instructions at once
# (used by server.py if needed for validation/debugging)


def load_all_instructions() -> dict[str, ToolInstruction]:
    """
    Load all tool instructions from YAML files.

    Returns:
        Dictionary mapping tool names to instruction data
    """
    all_instructions: dict[str, ToolInstruction] = {}

    # Scan all YAML files in tool_instructions directory
    for yaml_path in INSTRUCTIONS_DIR.rglob("*.yml"):
        category = yaml_path.parent.name
        tool_name = yaml_path.stem

        try:
            instruction = load_tool_instruction(tool_name, category)
            all_instructions[tool_name] = instruction
        except Exception as e:
            logger.warning(
                "Failed to load instruction during bulk load",
                tool_name=tool_name,
                category=category,
                error=str(e),
            )

    logger.info(
        "Loaded all tool instructions",
        total_tools=len(all_instructions),
    )

    return all_instructions


def get_next_steps_text(tool_name: str, category: str) -> str:
    """
    Get formatted Next Steps text for a tool.

    Args:
        tool_name: Name of the tool
        category: Category directory

    Returns:
        Formatted Next Steps text (empty string if none)
    """
    instruction = load_tool_instruction(tool_name, category)
    next_steps = instruction.get("next_steps", [])
    return format_next_steps(next_steps)


# Markdown-based instruction loading (for backward compatibility with server.py)
# These functions load instruction text from .md template files


# Mapping of tool names to their template paths
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
    # Prompts/advanced tools
    "get_recommendations_for_paper": "prompts/get_recommendations_for_paper.md",
    "get_recommendations_batch": "prompts/get_recommendations_batch.md",
    "autocomplete_query": "prompts/autocomplete_query.md",
    "search_snippets": "prompts/search_snippets.md",
    "check_api_key_status": "prompts/check_api_key_status.md",
}


@lru_cache(maxsize=128)
def _load_instruction_template(template_path: str) -> str:
    """
    Load instruction template from Markdown file with caching.

    Args:
        template_path: Relative path from INSTRUCTIONS_DIR
            (e.g., 'paper/search_papers.md')

    Returns:
        Template content as string
    """
    full_path = INSTRUCTIONS_DIR / template_path

    if not full_path.exists():
        logger.warning(
            "Instruction template not found",
            template_path=template_path,
            full_path=str(full_path),
        )
        return ""

    try:
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
            "Failed to load instruction template",
            template_path=template_path,
            error=str(e),
        )
        return ""


def get_instruction(tool_name: str) -> str:
    """
    Get instruction text for a specific tool from Markdown template.

    Args:
        tool_name: Name of the tool

    Returns:
        Instruction text (empty string if not found)
    """
    template_path = TOOL_TEMPLATE_MAPPING.get(tool_name)

    if not template_path:
        logger.debug(
            "No instruction template mapping for tool",
            tool_name=tool_name,
        )
        return ""

    return _load_instruction_template(template_path)


def load_tool_instructions() -> dict[str, str]:
    """
    Load all tool instructions from Markdown templates.

    Returns:
        Dictionary mapping tool names to instruction text
    """
    instructions: dict[str, str] = {}

    for tool_name, template_path in TOOL_TEMPLATE_MAPPING.items():
        instruction_text = _load_instruction_template(template_path)
        if instruction_text:
            instructions[tool_name] = instruction_text

    logger.info(
        "Loaded tool instructions",
        total_tools=len(instructions),
        from_templates=len([v for v in instructions.values() if v]),
    )

    return instructions
