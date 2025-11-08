#!/usr/bin/env python3
"""
Test script to verify YAML instruction loading and docstring injection.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semantic_scholar_mcp.instruction_loader import (
    format_next_steps,
    inject_yaml_instructions,
    load_tool_instruction,
)


def test_load_yaml():
    """Test loading YAML instruction file."""
    print("=" * 60)
    print("Test 1: Load YAML instruction")
    print("=" * 60)

    instruction = load_tool_instruction("search_papers", "paper")

    print(f"Tool name: {instruction['tool_name']}")
    print(f"Category: {instruction['category']}")
    print(f"Description: {instruction.get('description', '(empty)')}")
    print(f"Next steps count: {len(instruction.get('next_steps', []))}")
    print("\nNext steps:")
    for step in instruction.get("next_steps", []):
        print(f"  - {step}")


def test_format_next_steps():
    """Test formatting next steps."""
    print("\n" + "=" * 60)
    print("Test 2: Format Next Steps")
    print("=" * 60)

    next_steps = [
        "Review the returned papers list",
        "Ask for summaries of interesting papers",
        "- Already has bullet point",
    ]

    formatted = format_next_steps(next_steps)
    print(formatted)


def test_decorator():
    """Test decorator injection."""
    print("\n" + "=" * 60)
    print("Test 3: Decorator Injection")
    print("=" * 60)

    @inject_yaml_instructions("search_papers", "paper")
    async def search_papers(query: str) -> str:
        """
        Search Semantic Scholar papers.

        Args:
            query: Search query string

        Returns:
            Papers matching the query
        """
        return f"Searching for: {query}"

    print("Original docstring (should be enhanced):")
    print(search_papers.__doc__)
    print("\n" + "-" * 60)


def test_missing_yaml():
    """Test fallback for missing YAML file."""
    print("\n" + "=" * 60)
    print("Test 4: Missing YAML Fallback")
    print("=" * 60)

    instruction = load_tool_instruction("nonexistent_tool", "fake_category")

    print(f"Tool name: {instruction['tool_name']}")
    print(f"Category: {instruction['category']}")
    print(f"Next steps: {instruction.get('next_steps', [])}")
    print("(Should return empty structure)")


if __name__ == "__main__":
    test_load_yaml()
    test_format_next_steps()
    test_decorator()
    test_missing_yaml()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
