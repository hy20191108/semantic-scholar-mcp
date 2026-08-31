"""Tests for the authoritative MCP tool instructions."""

from semantic_scholar_mcp import server
from semantic_scholar_mcp.instruction_loader import format_next_steps, get_instruction


async def test_registered_descriptions_contain_yaml_next_steps_once() -> None:
    """Each instructed MCP tool exposes its YAML guidance exactly once."""
    registered_tools = {tool.name: tool for tool in await server.mcp.list_tools()}
    assert server.REGISTERED_TOOL_NAMES == server.TOOL_INSTRUCTION_KEYS

    for tool_name, instruction in server.TOOL_INSTRUCTIONS.items():
        description = registered_tools[tool_name].description or ""
        expected = format_next_steps(instruction.get("next_steps", []))

        assert description.count("Next Steps:") == 1, tool_name
        assert expected in description, tool_name


def test_exported_tool_docstrings_contain_yaml_next_steps_once() -> None:
    """Each exported tool function exposes its YAML guidance exactly once."""
    for tool_name, instruction in server.TOOL_INSTRUCTIONS.items():
        docstring = getattr(server, tool_name).__doc__ or ""
        expected = format_next_steps(instruction.get("next_steps", []))

        assert docstring.count("Next Steps:") == 1, tool_name
        assert expected in docstring, tool_name


def test_markdown_fallback_matches_yaml() -> None:
    """Compatibility templates mirror the authoritative YAML guidance."""
    for tool_name, instruction in server.TOOL_INSTRUCTIONS.items():
        markdown_steps = [
            line.removeprefix("- ")
            for line in get_instruction(tool_name).splitlines()
            if line.startswith("- ")
        ]

        assert markdown_steps == instruction.get("next_steps", []), tool_name
