"""
Project and memory management for Semantic Scholar MCP (Serena-compliant).

This module provides project-based research management with memory persistence,
following the Serena architecture pattern.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Directory name for Semantic Scholar MCP managed data
MANAGED_DIR_NAME = ".semantic_scholar_mcp"
ENCODING = "utf-8"


def get_managed_dir_path(project_root: str | Path) -> Path:
    """
    Get the path to the .semantic_scholar_mcp directory.

    Args:
        project_root: Project root directory

    Returns:
        Path to the managed directory
    """
    return Path(project_root) / MANAGED_DIR_NAME


class MemoriesManager:
    """
    Manages project-specific memories in Markdown format (Serena-compliant).

    Memories are stored in {project_root}/.semantic_scholar_mcp/memories/
    """

    def __init__(self, project_root: str | Path):
        """
        Initialize the memories manager.

        Args:
            project_root: Project root directory
        """
        self._memory_dir = get_managed_dir_path(project_root) / "memories"
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._encoding = ENCODING

    def get_memory_file_path(self, name: str) -> Path:
        """
        Get the file path for a memory.

        Strips all .md extensions from the name (models tend to get confused).

        Args:
            name: Name of the memory (with or without .md extension)

        Returns:
            Path object for the memory file
        """
        # Strip all .md from the name
        name = name.replace(".md", "")
        filename = f"{name}.md"
        return self._memory_dir / filename

    def load_memory(self, name: str) -> str:
        """
        Load a memory file.

        Args:
            name: Name of the memory

        Returns:
            Content of the memory file, or error message if not found
        """
        memory_file_path = self.get_memory_file_path(name)
        if not memory_file_path.exists():
            return (
                f"Memory file {name} not found, consider creating it with the "
                "`write_memory` tool if you need it."
            )
        with open(memory_file_path, encoding=self._encoding) as f:
            return f.read()

    def save_memory(self, name: str, content: str) -> str:
        """
        Save a memory file.

        Args:
            name: Name of the memory
            content: Content to save (Markdown format)

        Returns:
            Success message
        """
        memory_file_path = self.get_memory_file_path(name)
        with open(memory_file_path, "w", encoding=self._encoding) as f:
            f.write(content)
        return f"Memory {name} written."

    def list_memories(self) -> list[str]:
        """
        List all available memories.

        Returns:
            List of memory names (without .md extension)
        """
        return [
            f.name.replace(".md", "") for f in self._memory_dir.iterdir() if f.is_file()
        ]

    def delete_memory(self, name: str) -> str:
        """
        Delete a memory file.

        Args:
            name: Name of the memory

        Returns:
            Success message

        Raises:
            FileNotFoundError: If memory file does not exist
        """
        memory_file_path = self.get_memory_file_path(name)
        if not memory_file_path.exists():
            raise FileNotFoundError(
                f"Memory file '{name}' not found at {memory_file_path}. "
                f"Available memories: {self.list_memories()}"
            )
        memory_file_path.unlink()
        return f"Memory {name} deleted."

    def search_memories(
        self,
        query: str,
        case_sensitive: bool = False,
        memory_name_filter: str | None = None,
    ) -> dict[str, list[str]]:
        """
        Search for a pattern across all memories (Semantic Scholar extension).

        Args:
            query: Regular expression pattern to search for
            case_sensitive: Whether to perform case-sensitive search
            memory_name_filter: Optional filter for memory names (regex)

        Returns:
            Dictionary mapping memory names to lists of matching lines

        Raises:
            ValueError: If the regex pattern is invalid
        """
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{query}': {e}") from e

        # Validate memory_name_filter if provided
        if memory_name_filter:
            try:
                re.compile(memory_name_filter)
            except re.error as e:
                raise ValueError(
                    f"Invalid memory name filter regex '{memory_name_filter}': {e}"
                ) from e

        results: dict[str, list[str]] = {}

        for memory_path in self._memory_dir.iterdir():
            if not memory_path.is_file():
                continue

            memory_name = memory_path.name.replace(".md", "")

            # Apply name filter if provided
            if memory_name_filter and not re.search(memory_name_filter, memory_name):
                continue

            try:
                with open(memory_path, encoding=self._encoding) as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    if matches:
                        # Return matching lines with context
                        lines = content.split("\n")
                        matching_lines = [
                            line for line in lines if pattern.search(line)
                        ]
                        results[memory_name] = matching_lines
            except OSError as e:
                logger.warning(f"Failed to read memory {memory_name}: {e}")
                continue

        return results


class ProjectConfig(BaseModel):
    """
    Configuration for a research project (Serena-compliant).

    Stored as YAML in {project_root}/.semantic_scholar_mcp/project.yml
    """

    project_name: str = Field(..., description="Name of the research project")
    research_topic: str | None = Field(None, description="Main research topic")
    default_fields_of_study: list[str] = Field(
        default_factory=list, description="Preferred fields of study for searches"
    )
    preferred_search_filters: dict[str, Any] = Field(
        default_factory=dict, description="Default search filters"
    )
    encoding: str = Field(default=ENCODING, description="File encoding")

    @classmethod
    def load(
        cls, project_root: str | Path, autogenerate: bool = True
    ) -> "ProjectConfig":
        """
        Load project configuration from YAML file.

        Args:
            project_root: Project root directory
            autogenerate: If True, create default config if file doesn't exist

        Returns:
            ProjectConfig instance
        """
        config_path = get_managed_dir_path(project_root) / "project.yml"

        if config_path.exists():
            try:
                with open(config_path, encoding=ENCODING) as f:
                    data = yaml.safe_load(f)
                    return cls(**data)
            except yaml.YAMLError as e:
                raise ValueError(
                    f"Invalid YAML syntax in project configuration at "
                    f"{config_path}: {e}. "
                    f"Please fix the YAML syntax or delete the file to regenerate."
                ) from e
            except Exception as e:
                # Catch Pydantic ValidationError and other schema errors
                # Include exception type for better debugging
                raise ValueError(
                    f"Invalid project configuration schema at {config_path} "
                    f"({type(e).__name__}): {e}. "
                    f"Please check required fields (project_name) and data types, "
                    f"or delete the file to regenerate."
                ) from e

        if autogenerate:
            # Create default configuration
            project_name = Path(project_root).name
            config = cls(project_name=project_name)
            config.save(project_root)
            return config

        raise FileNotFoundError(
            f"Project configuration not found at {config_path}. "
            f"To create a new project configuration, set autogenerate=True or use "
            f"Project.create() instead."
        )

    def save(self, project_root: str | Path) -> None:
        """
        Save project configuration to YAML file.

        Args:
            project_root: Project root directory
        """
        config_path = get_managed_dir_path(project_root) / "project.yml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding=ENCODING) as f:
            yaml.dump(
                self.model_dump(), f, default_flow_style=False, allow_unicode=True
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.model_dump()


class Project:
    """
    Research project management class (Serena-compliant).

    Manages project-specific memories, configuration, and metadata.
    """

    def __init__(
        self,
        project_root: str | Path,
        project_config: ProjectConfig,
        is_newly_created: bool = False,
    ):
        """
        Initialize a project.

        Args:
            project_root: Project root directory
            project_config: Project configuration
            is_newly_created: Whether this is a newly created project
        """
        self.project_root = Path(project_root).resolve()
        self.project_config = project_config
        self.memories_manager = MemoriesManager(project_root)
        self._is_newly_created = is_newly_created

        # Create .gitignore file in the managed folder if not present
        managed_dir = get_managed_dir_path(project_root)
        gitignore_path = managed_dir / ".gitignore"
        if not gitignore_path.exists():
            try:
                managed_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Creating .gitignore file in {gitignore_path}")
                with open(gitignore_path, "w", encoding=ENCODING) as f:
                    f.write("# Semantic Scholar MCP managed directory\n")
                    f.write("artifacts/\n")
                    f.write("*.log\n")
            except OSError as e:
                logger.warning(
                    f"Failed to create .gitignore at {gitignore_path}: {e}. "
                    f"Continuing without .gitignore."
                )

    @property
    def project_name(self) -> str:
        """Get the project name."""
        return self.project_config.project_name

    @classmethod
    def load(cls, project_root: str | Path, autogenerate: bool = True) -> "Project":
        """
        Load a project from a directory.

        Args:
            project_root: Project root directory
            autogenerate: If True, create default project if config doesn't exist

        Returns:
            Project instance
        """
        project_root = Path(project_root).resolve()
        if not project_root.exists():
            raise FileNotFoundError(f"Project root not found: {project_root}")

        project_config = ProjectConfig.load(project_root, autogenerate=autogenerate)
        return cls(project_root=project_root, project_config=project_config)

    @classmethod
    def create(
        cls,
        project_root: str | Path,
        project_name: str,
        research_topic: str | None = None,
        **kwargs,
    ) -> "Project":
        """
        Create a new project.

        Args:
            project_root: Project root directory
            project_name: Name of the project
            research_topic: Optional research topic description
            **kwargs: Additional configuration parameters

        Returns:
            New Project instance
        """
        project_root = Path(project_root).resolve()
        project_root.mkdir(parents=True, exist_ok=True)

        config = ProjectConfig(
            project_name=project_name, research_topic=research_topic, **kwargs
        )
        config.save(project_root)

        return cls(
            project_root=project_root,
            project_config=config,
            is_newly_created=True,
        )

    def save_config(self) -> None:
        """Save the current project configuration to disk."""
        logger.info(f"Saving project configuration for {self.project_name}")
        self.project_config.save(self.project_root)

    def get_activation_message(self) -> str:
        """
        Get a message to display when the project is activated.

        Returns:
            Activation message with project information and available memories
        """
        if self._is_newly_created:
            msg = (
                f"Created and activated a new research project '{self.project_name}' "
                f"at {self.project_root}. "
            )
        else:
            msg = (
                f"The research project '{self.project_name}' at {self.project_root} "
                "is activated."
            )

        msg += f"\nEncoding: {self.project_config.encoding}"

        if self.project_config.research_topic:
            msg += f"\nResearch Topic: {self.project_config.research_topic}"

        memories = self.memories_manager.list_memories()
        if memories:
            msg += (
                f"\nAvailable project memories: {json.dumps(memories)}\n"
                "Use the `read_memory` tool to read these memories later if they are "
                "relevant to the task."
            )

        return msg

    def validate_project_path(self, path: Path) -> None:
        """
        Validate that a path is within the project directory.

        Args:
            path: Path to validate

        Raises:
            ValueError: If path is outside project directory
        """
        path = Path(path).resolve()
        if not path.is_relative_to(self.project_root):
            raise ValueError(
                f"Path {path} is outside project root {self.project_root}; "
                "cannot access for safety reasons"
            )

    def __repr__(self) -> str:
        """String representation of the project."""
        return f"Project(name='{self.project_name}', root='{self.project_root}')"
