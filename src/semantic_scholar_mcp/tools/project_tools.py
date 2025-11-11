"""
Project management tools for Semantic Scholar MCP (Serena-compliant).

This module provides tools for managing research projects, including
project creation, activation, and listing.
"""

import json

from .base import Tool


class ActivateProjectTool(Tool):
    """
    Activate a research project.

    This tool switches the active project, making its memories and configuration
    available for use. You can specify either a project path or a registered
    project name.
    """

    def apply(self, project_path_or_name: str) -> str:
        """
        Activate a research project.

        Args:
            project_path_or_name: Path to project directory or registered project name

        Returns:
            Activation message with project information and available memories

        Raises:
            ProjectNotFoundError: If project cannot be found

        Example:
            activate_project("/path/to/my/research")
            activate_project("my_research_project")
        """
        if self.agent is None:
            raise RuntimeError("Tool has no agent instance")

        # Activate the project through the agent
        project = self.agent.activate_project(project_path_or_name)

        # Return the activation message
        return project.get_activation_message()


class ListProjectsTool(Tool):
    """
    List all registered research projects.

    This tool shows all projects that have been registered with the agent,
    including their paths and activation status.
    """

    def apply(self) -> str:
        """
        List all registered projects.

        Returns:
            JSON string with project information including names, paths,
            and active status

        Example output:
            {
                "total_projects": 2,
                "active_project": "my_research",
                "projects": [
                    {
                        "name": "my_research",
                        "path": "/path/to/my/research",
                        "is_active": true
                    },
                    {
                        "name": "other_research",
                        "path": "/path/to/other/research",
                        "is_active": false
                    }
                ]
            }
        """
        if self.agent is None:
            raise RuntimeError("Tool has no agent instance")

        # Get project list from the agent
        projects_info = self.agent.list_projects()

        # Return formatted JSON
        return json.dumps(projects_info, indent=2)


class CreateProjectTool(Tool):
    """
    Create a new research project.

    This tool creates a new research project directory with the necessary
    configuration files and directory structure. The project can be automatically
    activated after creation.
    """

    def apply(
        self,
        project_root: str,
        project_name: str,
        research_topic: str | None = None,
        activate: bool = True,
        default_fields_of_study: list[str] | None = None,
    ) -> str:
        """
        Create a new research project.

        Args:
            project_root: Root directory for the new project (will be created if
                         it doesn't exist)
            project_name: Name of the project (used for identification)
            research_topic: Optional description of the research topic
            activate: If True, activate the project after creation (default: True)
            default_fields_of_study: Optional list of preferred fields of study
                                     for searches (e.g., ["Computer Science", "AI"])

        Returns:
            Success message with project information

        Example:
            create_project(
                project_root="/path/to/my/research",
                project_name="Transformer Research",
                research_topic="Analysis of transformer architectures",
                default_fields_of_study=["Computer Science", "Machine Learning"]
            )
        """
        if self.agent is None:
            raise RuntimeError("Tool has no agent instance")

        # Prepare kwargs for project creation
        kwargs = {}
        if default_fields_of_study:
            kwargs["default_fields_of_study"] = default_fields_of_study

        # Create the project through the agent
        project = self.agent.create_project(
            project_root=project_root,
            project_name=project_name,
            research_topic=research_topic,
            activate=activate,
            **kwargs,
        )

        # Build response message
        msg = f"Created research project '{project_name}' at {project.project_root}\n"

        if research_topic:
            msg += f"Research Topic: {research_topic}\n"

        if default_fields_of_study:
            msg += f"Default Fields of Study: {', '.join(default_fields_of_study)}\n"

        if activate:
            msg += "\nProject is now active and ready to use."
            msg += "\nUse write_memory to create research notes and documentation."
        else:
            msg += (
                "\nProject created but not activated. "
                f"Use activate_project('{project_name}') to activate it."
            )

        return msg


class GetCurrentConfigTool(Tool):
    """
    Get the current agent configuration.

    This tool shows the current state of the research agent, including
    active project, registered projects, and loaded tools.
    """

    def apply(self) -> str:
        """
        Get current configuration overview.

        Returns:
            JSON string with agent configuration details including active project,
            registered projects, and tool information

        Example output:
            {
                "active_project": {
                    "name": "my_research",
                    "root": "/path/to/my/research",
                    "research_topic": "Transformers",
                    "memories_count": 5
                },
                "registered_projects": {...},
                "tools_loaded": 8,
                "api_client_configured": true
            }
        """
        if self.agent is None:
            raise RuntimeError("Tool has no agent instance")

        # Get config overview from the agent
        config = self.agent.get_config_overview()

        # Return formatted JSON
        return json.dumps(config, indent=2)


# Export all tools
__all__ = [
    "ActivateProjectTool",
    "CreateProjectTool",
    "GetCurrentConfigTool",
    "ListProjectsTool",
]
