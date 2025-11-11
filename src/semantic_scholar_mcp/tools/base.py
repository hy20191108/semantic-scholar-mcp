"""
Base classes for Semantic Scholar MCP tools (Serena-compliant).

This module provides the foundational tool infrastructure for the MCP server,
following the Serena architecture pattern.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from semantic_scholar_mcp.agent import ResearchAgent
    from semantic_scholar_mcp.project import MemoriesManager, Project


class Tool(ABC):
    """
    Base class for all MCP tools (Serena-compliant).

    Tools are operations that can be exposed through the MCP protocol.
    Each tool has access to the research agent and active project.
    """

    def __init__(self, agent: Optional["ResearchAgent"] = None):
        """
        Initialize the tool.

        Args:
            agent: ResearchAgent instance (optional, for future use)
        """
        self._agent = agent

    @property
    def agent(self) -> Optional["ResearchAgent"]:
        """Get the research agent instance."""
        return self._agent

    @property
    def memories_manager(self) -> "MemoriesManager":
        """
        Get the memories manager from the active project.

        Returns:
            MemoriesManager instance

        Raises:
            RuntimeError: If no project is active
        """
        if self._agent is None:
            raise RuntimeError("Tool has no agent instance")

        project = self._agent.get_active_project()
        if project is None:
            raise RuntimeError("No active project; please activate a project first")

        return project.memories_manager

    @property
    def active_project(self) -> "Project":
        """
        Get the active project.

        Returns:
            Project instance

        Raises:
            RuntimeError: If no project is active
        """
        if self._agent is None:
            raise RuntimeError("Tool has no agent instance")

        project = self._agent.get_active_project()
        if project is None:
            raise RuntimeError("No active project; please activate a project first")

        return project

    def get_project_root(self) -> str:
        """
        Get the root directory of the active project.

        Returns:
            Project root path as string
        """
        return str(self.active_project.project_root)

    @abstractmethod
    def apply(self, **kwargs) -> str:
        """
        Execute the tool's operation.

        This method must be implemented by subclasses.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Result as string (Serena-style tool result)
        """

    @classmethod
    def tool_name(cls) -> str:
        """
        Get the MCP tool name.

        By default, converts class name from CamelCase to snake_case.
        Can be overridden in subclasses.

        Returns:
            Tool name for MCP registration
        """
        # Convert CamelCase to snake_case
        name = cls.__name__
        # Remove "Tool" suffix if present
        if name.endswith("Tool"):
            name = name[:-4]

        # Convert CamelCase to snake_case
        import re

        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()

    @classmethod
    def tool_description(cls) -> str:
        """
        Get the tool description for MCP.

        Uses the class docstring by default.

        Returns:
            Tool description
        """
        return cls.__doc__ or ""

    def __repr__(self) -> str:
        """String representation of the tool."""
        return f"{self.__class__.__name__}()"
