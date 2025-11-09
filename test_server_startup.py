#!/usr/bin/env python3
"""Simple MCP server startup test."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set debug mode
os.environ["DEBUG_MCP_MODE"] = "true"
os.environ["LOG_MCP_MESSAGES"] = "true"

from semantic_scholar_mcp.server import mcp


async def test_server():
    """Test server initialization."""
    print("🔍 Testing MCP server startup...")

    # List tools
    tools = await mcp.list_tools()
    tool_list = getattr(tools, "tools", tools)
    print(f"✓ Tools registered: {len(tool_list)}")

    # List prompts
    prompts = await mcp.list_prompts()
    prompt_list = getattr(prompts, "prompts", prompts)
    print(f"✓ Prompts registered: {len(prompt_list)}")

    # List resources
    resources = await mcp.list_resources()
    resource_list = getattr(resources, "resources", resources)
    print(f"✓ Resources registered: {len(resource_list)}")

    # Show tool names
    print("\n📝 Tool names:")
    for i, tool in enumerate(tool_list, 1):
        print(f"  {i}. {tool.name}")

    # Check for errors
    if len(tool_list) != 24:
        print(f"\n❌ ERROR: Expected 24 tools, found {len(tool_list)}")
        return False

    print("\n✅ Server startup: OK")
    return True


if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
