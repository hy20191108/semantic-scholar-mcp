"""
Research agent for Semantic Scholar MCP (Serena-compliant).

This module provides the main research agent that manages projects, tools,
and integrates with the Semantic Scholar API client.
"""

import logging
from pathlib import Path
from typing import Any, TypeVar, cast

from core.config import ApplicationConfig

from .api_client import SemanticScholarClient
from .project import Project
from .tools.base import Tool

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Tool)


class ProjectNotFoundError(Exception):
    """Raised when a project cannot be found."""


class ResearchAgent:
    """
    Research agent for managing Semantic Scholar research projects (Serena-compliant).

    The agent manages:
    - Multiple research projects with switching capability
    - Tool registry and lifecycle
    - Integration with Semantic Scholar API client
    - Project-specific memories and configuration
    """

    def __init__(
        self,
        api_client: SemanticScholarClient,
        config: ApplicationConfig,
    ):
        """
        Initialize the research agent.

        Args:
            api_client: Semantic Scholar API client instance
            config: Application configuration
        """
        self.api_client = api_client
        self.config = config
        self._active_project: Project | None = None
        self._registered_projects: dict[str, Path] = {}
        self._all_tools: dict[type[Tool], Tool] = {}

        logger.info("ResearchAgent initialized")

        # Load registered projects from config if available
        self._load_registered_projects()

    def _load_registered_projects(self) -> None:
        """
        Load registered projects from persistent storage.

        In a full implementation, this would load from a config file.
        For now, we keep it in memory only.
        """
        # TODO: Load from ~/.semantic_scholar_mcp/projects.json
        # For Phase 2, we'll implement basic in-memory registry
        logger.debug("Project registry loaded (in-memory only for Phase 2)")

    def _save_registered_projects(self) -> None:
        """
        Save registered projects to persistent storage.

        In a full implementation, this would save to a config file.
        """
        # TODO: Save to ~/.semantic_scholar_mcp/projects.json
        logger.debug("Project registry saved (in-memory only for Phase 2)")

    def get_active_project(self) -> Project | None:
        """
        Get the currently active project.

        Returns:
            Active Project instance, or None if no project is active
        """
        return self._active_project

    def get_active_project_or_raise(self) -> Project:
        """
        Get the currently active project, raising an error if none is active.

        Returns:
            Active Project instance

        Raises:
            ProjectNotFoundError: If no project is active
        """
        if self._active_project is None:
            raise ProjectNotFoundError(
                "No project is currently active. Please activate a project first using "
                "the activate_project tool."
            )
        return self._active_project

    def activate_project(self, project_path_or_name: str) -> Project:
        """
        Activate a project from a path or registered name.

        If the project was already registered, it will just be activated.
        If the argument is a path at which no project previously existed,
        the project will be created beforehand.

        Args:
            project_path_or_name: Path to project directory or registered project name

        Returns:
            Activated Project instance

        Raises:
            ProjectNotFoundError: If project cannot be found or created
        """
        # Normalize the path to ensure consistent lookup
        normalized_path = str(Path(project_path_or_name).resolve())

        # Check if it's a registered project (by name or path)
        if project_path_or_name in self._registered_projects:
            project_path = self._registered_projects[project_path_or_name]
            logger.info(
                f"Activating registered project by name: {project_path_or_name}"
            )
        elif normalized_path in self._registered_projects:
            project_path = self._registered_projects[normalized_path]
            logger.info(f"Activating registered project by path: {normalized_path}")
        else:
            # Treat it as a path
            project_path = Path(project_path_or_name).resolve()
            logger.info(f"Activating project from path: {project_path}")

        # Load or create the project
        try:
            project = Project.load(project_path, autogenerate=True)
        except FileNotFoundError as e:
            # Determine if it's a path or name error
            if Path(project_path).exists():
                # Directory exists but no valid project config
                error_msg = (
                    f"Directory '{project_path}' exists but is not a valid "
                    f"Semantic Scholar MCP project. To create a new project here, "
                    f"use create_project tool instead."
                )
            elif project_path_or_name in self._registered_projects:
                # Registered name but directory was deleted
                error_msg = (
                    f"Registered project '{project_path_or_name}' points to "
                    f"non-existent directory '{project_path}'. "
                    f"The directory may have been deleted. "
                    f"To fix this, either: (1) restore the directory, or "
                    f"(2) use create_project with a different name to start fresh."
                )
            else:
                # Neither a valid path nor a registered name
                error_msg = (
                    f"'{project_path_or_name}' is neither a valid project "
                    f"directory nor a registered project name. "
                )
                if self._registered_projects:
                    projects = list(self._registered_projects.keys())
                    error_msg += f"Available registered projects: {projects}"
                else:
                    error_msg += (
                        "No projects are currently registered. "
                        "Use create_project to create one."
                    )

            raise ProjectNotFoundError(error_msg) from e

        # Set as active project
        self._active_project = project

        # Auto-register if not already registered (by both name and path)
        project_name = project.project_name
        project_path_str = str(project.project_root)

        # Register by project name if not already registered
        if project_name not in self._registered_projects:
            self.register_project(project_name, project_path)

        # Also register by path for faster lookup on subsequent activations
        if project_path_str not in self._registered_projects:
            self._registered_projects[project_path_str] = Path(project_path_str)
            logger.debug(
                f"Registered project path '{project_path_str}' for fast lookup"
            )

        logger.info(f"Project '{project.project_name}' activated")

        return project

    def register_project(self, name: str, path: Path | str) -> None:
        """
        Register a project with a friendly name for easy access.

        Args:
            name: Friendly name for the project
            path: Path to the project directory
        """
        path = Path(path).resolve()
        self._registered_projects[name] = path
        self._save_registered_projects()
        logger.info(f"Registered project '{name}' at {path}")

    def list_projects(self) -> dict[str, Any]:
        """
        List all registered projects.

        Returns:
            Dictionary with project information including names, paths,
            and active project status
        """
        projects_list = []
        for name, path in self._registered_projects.items():
            projects_list.append(
                {
                    "name": name,
                    "path": str(path),
                    "is_active": (
                        self._active_project is not None
                        and self._active_project.project_root == path
                    ),
                }
            )

        return {
            "total_projects": len(projects_list),
            "active_project": (
                self._active_project.project_name if self._active_project else None
            ),
            "projects": projects_list,
        }

    def create_project(
        self,
        project_root: str | Path,
        project_name: str,
        research_topic: str | None = None,
        activate: bool = True,
        **kwargs,
    ) -> Project:
        """
        Create a new research project.

        Args:
            project_root: Root directory for the new project
            project_name: Name of the project
            research_topic: Optional research topic description
            activate: If True, activate the project after creation
            **kwargs: Additional project configuration parameters

        Returns:
            New Project instance
        """
        project = Project.create(
            project_root=project_root,
            project_name=project_name,
            research_topic=research_topic,
            **kwargs,
        )

        # Register the project
        self.register_project(project_name, project.project_root)

        # Activate if requested
        if activate:
            self._active_project = project
            logger.info(f"Created and activated project '{project_name}'")
        else:
            logger.info(f"Created project '{project_name}'")

        return project

    def get_tool(self, tool_class: type[T]) -> T:
        """
        Get a tool instance by class.

        Tools are lazily instantiated and cached.

        Args:
            tool_class: Tool class to instantiate

        Returns:
            Tool instance
        """
        if tool_class not in self._all_tools:
            self._all_tools[tool_class] = tool_class(agent=self)
        return cast(T, self._all_tools[tool_class])

    def get_active_tools(self) -> dict[str, Tool]:
        """
        Get all active tools as a dictionary.

        Returns:
            Dictionary mapping tool names to tool instances
        """
        # For Phase 2, return all instantiated tools
        return {
            tool_class.tool_name(): tool for tool_class, tool in self._all_tools.items()
        }

    async def auto_generate_paper_memory(self, paper_id: str) -> str:
        """
        Automatically generate a memory from paper information.

        Semantic Scholar extension for auto-generating research memories.

        Fetches paper details from the API and creates a structured memory.

        Args:
            paper_id: Semantic Scholar paper ID or DOI

        Returns:
            Success message with memory name

        Raises:
            ProjectNotFoundError: If no project is active
        """
        # Get active project
        project = self.get_active_project_or_raise()

        # Fetch paper details from API
        # For Phase 2, we'll implement a simple version
        # Full implementation in Phase 3
        logger.info(f"Auto-generating memory for paper {paper_id}")

        # Create memory name from paper_id
        memory_name = f"paper_{paper_id.replace('/', '_')}"

        # Basic memory content (will be enhanced in Phase 3)
        content = f"""---
paper_id: {paper_id}
auto_generated: true
---

# Paper: {paper_id}

> Auto-generated memory. Use `get_paper` to fetch full details.

## TODO
- Fetch paper details
- Add abstract
- Add authors
- Add key citations
"""

        # Save the memory
        project.memories_manager.save_memory(memory_name, content)

        return f"Auto-generated memory '{memory_name}' for paper {paper_id}"

    async def suggest_papers_from_memories(self) -> list[dict]:
        """
        Suggest related papers based on memory content (Semantic Scholar extension).

        Analyzes memories to find keywords and suggests relevant papers.

        Args:
            None (uses active project memories)

        Returns:
            List of suggested papers

        Raises:
            ProjectNotFoundError: If no project is active
        """
        # Get active project
        project = self.get_active_project_or_raise()

        # Get all memories
        memories = project.memories_manager.list_memories()

        if not memories:
            return []

        # For Phase 2, return a simple message
        # Full implementation in Phase 3 with actual API calls
        logger.info(f"Analyzing {len(memories)} memories for paper suggestions")

        return [
            {
                "message": "Paper suggestion feature will be implemented in Phase 3",
                "analyzed_memories": len(memories),
                "suggestion": "Use search_papers with keywords from your memories",
            }
        ]

    def get_project_root(self) -> str:
        """
        Get the root directory of the active project.

        Returns:
            Project root path as string

        Raises:
            ProjectNotFoundError: If no project is active
        """
        project = self.get_active_project_or_raise()
        return str(project.project_root)

    def get_config_overview(self) -> dict[str, Any]:
        """
        Get an overview of the current agent configuration.

        Returns:
            Dictionary with agent configuration details
        """
        projects_info = self.list_projects()

        return {
            "active_project": (
                {
                    "name": self._active_project.project_name,
                    "root": str(self._active_project.project_root),
                    "research_topic": (
                        self._active_project.project_config.research_topic
                    ),
                    "memories_count": len(
                        self._active_project.memories_manager.list_memories()
                    ),
                }
                if self._active_project
                else None
            ),
            "registered_projects": projects_info,
            "tools_loaded": len(self._all_tools),
            "api_client_configured": self.api_client is not None,
        }

    def __repr__(self) -> str:
        """String representation of the agent."""
        active = self._active_project.project_name if self._active_project else "None"
        num_registered = len(self._registered_projects)
        return f"ResearchAgent(active_project='{active}', registered={num_registered})"
