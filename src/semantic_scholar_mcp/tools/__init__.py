"""
Semantic Scholar MCP Tools (Serena-compliant).

This package provides MCP tools for research project management,
memory management, and Semantic Scholar API integration.
"""

from .base import Tool
from .memory_tools import (
    DeleteMemoryTool,
    EditMemoryTool,
    ListMemoriesTool,
    ReadMemoryTool,
    WriteMemoryTool,
)
from .project_tools import (
    ActivateProjectTool,
    CreateProjectTool,
    GetCurrentConfigTool,
    ListProjectsTool,
)

# All available tools
__all__ = [
    # Project tools (Phase 2)
    "ActivateProjectTool",
    "CreateProjectTool",
    "DeleteMemoryTool",
    "EditMemoryTool",
    "GetCurrentConfigTool",
    "ListMemoriesTool",
    "ListProjectsTool",
    "ReadMemoryTool",
    # Base
    "Tool",
    # Memory tools (Phase 1)
    "WriteMemoryTool",
]

# Tool registry for easy lookup
MEMORY_TOOLS = [
    WriteMemoryTool,
    ReadMemoryTool,
    ListMemoriesTool,
    DeleteMemoryTool,
    EditMemoryTool,
]

PROJECT_TOOLS = [
    ActivateProjectTool,
    ListProjectsTool,
    CreateProjectTool,
    GetCurrentConfigTool,
]

ALL_TOOLS = MEMORY_TOOLS + PROJECT_TOOLS
