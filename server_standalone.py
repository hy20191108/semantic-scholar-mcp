#!/usr/bin/env python3
"""Standalone MCP server for development and testing."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from semantic_scholar_mcp.server import main, mcp  # noqa: E402

# Export the FastMCP server for MCP inspector
server = mcp

if __name__ == "__main__":
    main()
