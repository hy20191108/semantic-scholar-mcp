"""Semantic Scholar MCP server package."""

try:
    from importlib.metadata import version
    __version__ = version("semantic-scholar-mcp")
except ImportError:
    __version__ = "unknown"

from .server import main

__all__ = ["__version__", "main"]
