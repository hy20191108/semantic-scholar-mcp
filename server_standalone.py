#!/usr/bin/env python3
"""Standalone MCP server for development and testing."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from semantic_scholar_mcp.server import mcp  # noqa: E402

# Export the FastMCP server for MCP inspector
server = mcp

if __name__ == "__main__":
    import asyncio

    from semantic_scholar_mcp.server import on_shutdown, on_startup

    # Initialize server
    asyncio.run(on_startup())

    try:
        # Run MCP server (this will handle stdio communication)
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        asyncio.run(on_shutdown())
