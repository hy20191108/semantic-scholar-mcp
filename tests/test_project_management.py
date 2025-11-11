"""
Test suite for project management and memory tools (Phase 1 & 2).

This module tests:
- Project and MemoriesManager (Phase 1)
- ResearchAgent and project lifecycle (Phase 2)
- Memory tools (write, read, list, delete, edit)
- Project tools (create, activate, list, config)
"""

import json
import tempfile
from pathlib import Path

import pytest

from core.config import ApplicationConfig
from semantic_scholar_mcp.agent import ProjectNotFoundError, ResearchAgent
from semantic_scholar_mcp.api_client import SemanticScholarClient
from semantic_scholar_mcp.project import MemoriesManager, Project
from semantic_scholar_mcp.tools.memory_tools import (
    DeleteMemoryTool,
    EditMemoryTool,
    ListMemoriesTool,
    ReadMemoryTool,
    WriteMemoryTool,
)
from semantic_scholar_mcp.tools.project_tools import (
    ActivateProjectTool,
    CreateProjectTool,
    GetCurrentConfigTool,
    ListProjectsTool,
)


class TestProjectAndMemories:
    """Test Project and MemoriesManager (Phase 1)."""

    def test_project_creation_and_loading(self):
        """Test project creation and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"

            # Create project
            project = Project.create(
                project_root=project_root,
                project_name="Test Project",
                research_topic="AI Research",
            )

            assert project.project_name == "Test Project"
            assert project.project_config.research_topic == "AI Research"
            assert project_root.exists()

            # Load existing project
            loaded_project = Project.load(project_root)
            assert loaded_project.project_name == "Test Project"
            assert loaded_project.project_config.research_topic == "AI Research"

    def test_memories_manager_basic_operations(self):
        """Test MemoriesManager basic operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoriesManager(tmpdir)

            # Save memory
            result = manager.save_memory("note1", "# Title\n\nContent here")
            assert "written" in result

            # Load memory
            content = manager.load_memory("note1")
            assert "# Title" in content

            # List memories
            memories = manager.list_memories()
            assert "note1" in memories

            # Delete memory
            result = manager.delete_memory("note1")
            assert "deleted" in result
            assert "note1" not in manager.list_memories()

    def test_memories_with_yaml_front_matter(self):
        """Test that YAML front matter is preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoriesManager(tmpdir)

            content = """---
tags: [ai, transformers]
date: 2024-01-01
---

# Research Note

This is a test note."""

            manager.save_memory("note_with_yaml", content)
            loaded = manager.load_memory("note_with_yaml")

            assert "tags: [ai, transformers]" in loaded
            assert "date: 2024-01-01" in loaded
            assert "# Research Note" in loaded

    def test_memory_search(self):
        """Test memory search functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoriesManager(tmpdir)

            # Create multiple memories
            manager.save_memory("ai_paper", "# AI Research\n\nTransformers are great")
            manager.save_memory(
                "ml_paper", "# Machine Learning\n\nNeural networks work"
            )
            manager.save_memory("stats_paper", "# Statistics\n\nBayesian methods")

            # Search for "Transformers"
            results = manager.search_memories("Transformers")
            assert "ai_paper" in results
            assert len(results["ai_paper"]) > 0

            # Search for "Neural"
            results = manager.search_memories("Neural")
            assert "ml_paper" in results

    def test_memory_tools(self):
        """Test memory tools integration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create and activate project
            project_root = Path(tmpdir) / "tool_test"
            agent.create_project(
                project_root=project_root,
                project_name="Tool Test",
                research_topic="Testing memory tools",
            )

            # Test WriteMemoryTool
            write_tool = WriteMemoryTool(agent)
            result = write_tool.apply(
                memory_name="test_note", content="# Test\n\nThis is a test note."
            )
            assert "written" in result

            # Test ReadMemoryTool
            read_tool = ReadMemoryTool(agent)
            content = read_tool.apply(memory_name="test_note")
            assert "# Test" in content

            # Test ListMemoriesTool
            list_tool = ListMemoriesTool(agent)
            result = list_tool.apply()
            assert "test_note" in result

            # Test DeleteMemoryTool
            delete_tool = DeleteMemoryTool(agent)
            result = delete_tool.apply(memory_name="test_note")
            assert "deleted" in result

    def test_edit_memory_tool(self):
        """Test EditMemoryTool functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create and activate project
            project_root = Path(tmpdir) / "edit_test"
            agent.create_project(
                project_root=project_root, project_name="Edit Test", activate=True
            )

            # Create a memory
            write_tool = WriteMemoryTool(agent)
            write_tool.apply(
                memory_name="editable",
                content="# Title\n\nOld content here\n\nMore text",
            )

            # Edit the memory
            edit_tool = EditMemoryTool(agent)
            result = edit_tool.apply(
                memory_name="editable",
                regex="Old content",
                repl="New content",
            )
            assert "replaced 1 occurrence" in result

            # Verify the edit
            read_tool = ReadMemoryTool(agent)
            content = read_tool.apply(memory_name="editable")
            assert "New content" in content
            assert "Old content" not in content

    def test_edit_memory_multiple_matches_error(self):
        """Test EditMemoryTool error on multiple matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            project_root = Path(tmpdir) / "multi_match"
            agent.create_project(
                project_root=project_root, project_name="Multi Match", activate=True
            )

            # Create memory with duplicate pattern
            write_tool = WriteMemoryTool(agent)
            write_tool.apply(
                memory_name="duplicate",
                content="test\ntest\ntest",
            )

            # Try to edit without allow_multiple_occurrences
            edit_tool = EditMemoryTool(agent)
            with pytest.raises(ValueError, match=r"Pattern .* matches 3 times"):
                edit_tool.apply(
                    memory_name="duplicate",
                    regex="test",
                    repl="replacement",
                    allow_multiple_occurrences=False,
                )


class TestResearchAgent:
    """Test ResearchAgent (Phase 2)."""

    def test_agent_initialization(self):
        """Test ResearchAgent initialization."""
        config = ApplicationConfig()
        api_client = SemanticScholarClient(config=config)
        agent = ResearchAgent(api_client=api_client, config=config)

        assert agent.get_active_project() is None
        assert len(agent._registered_projects) == 0
        assert agent.api_client is not None

    def test_project_creation_and_activation(self):
        """Test project creation and activation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project
            project_root = Path(tmpdir) / "research1"
            project = agent.create_project(
                project_root=project_root,
                project_name="Research Project 1",
                research_topic="Transformer Architectures",
                activate=True,
            )

            assert project.project_name == "Research Project 1"
            assert agent.get_active_project().project_name == "Research Project 1"

    def test_project_switching(self):
        """Test switching between projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create two projects
            project_root1 = Path(tmpdir) / "research1"
            agent.create_project(
                project_root=project_root1,
                project_name="Research Project 1",
                activate=True,
            )

            project_root2 = Path(tmpdir) / "research2"
            agent.create_project(
                project_root=project_root2,
                project_name="Research Project 2",
                activate=False,
            )

            # Verify project1 is active
            assert agent.get_active_project().project_name == "Research Project 1"

            # Switch to project2 by name (registered name)
            agent.activate_project("Research Project 2")
            assert agent.get_active_project().project_name == "Research Project 2"

            # Switch back to project1 by name
            agent.activate_project("Research Project 1")
            assert agent.get_active_project().project_name == "Research Project 1"

    def test_project_not_found_error(self):
        """Test ProjectNotFoundError when activating non-existent project."""
        config = ApplicationConfig()
        api_client = SemanticScholarClient(config=config)
        agent = ResearchAgent(api_client=api_client, config=config)

        with pytest.raises(ProjectNotFoundError):
            agent.activate_project("/non/existent/path")

    def test_list_projects(self):
        """Test listing registered projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create two projects
            project_root1 = Path(tmpdir) / "research1"
            agent.create_project(
                project_root=project_root1,
                project_name="Research Project 1",
                activate=True,
            )

            project_root2 = Path(tmpdir) / "research2"
            agent.create_project(
                project_root=project_root2,
                project_name="Research Project 2",
                activate=False,
            )

            # List projects
            projects_info = agent.list_projects()
            assert projects_info["total_projects"] == 2
            assert projects_info["active_project"] == "Research Project 1"
            assert len(projects_info["projects"]) == 2

    def test_get_tool(self):
        """Test tool lazy instantiation."""
        config = ApplicationConfig()
        api_client = SemanticScholarClient(config=config)
        agent = ResearchAgent(api_client=api_client, config=config)

        # Get tool (should create and cache)
        tool1 = agent.get_tool(WriteMemoryTool)
        assert isinstance(tool1, WriteMemoryTool)

        # Get same tool again (should return cached)
        tool2 = agent.get_tool(WriteMemoryTool)
        assert tool1 is tool2

    def test_config_overview(self):
        """Test agent configuration overview."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project with memories
            project_root = Path(tmpdir) / "config_test"
            agent.create_project(
                project_root=project_root,
                project_name="Config Test",
                research_topic="Testing configuration overview",
            )

            # Add memories
            write_tool = WriteMemoryTool(agent)
            write_tool.apply(memory_name="note1", content="# Note 1")
            write_tool.apply(memory_name="note2", content="# Note 2")

            # Get configuration overview
            config_overview = agent.get_config_overview()

            assert config_overview["active_project"]["name"] == "Config Test"
            assert config_overview["active_project"]["memories_count"] == 2
            assert config_overview["api_client_configured"] is True


class TestProjectTools:
    """Test project management tools (Phase 2)."""

    def test_create_project_tool(self):
        """Test CreateProjectTool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            create_tool = CreateProjectTool(agent)
            project_root = Path(tmpdir) / "tool_test_project"
            result = create_tool.apply(
                project_root=str(project_root),
                project_name="Tool Test Project",
                research_topic="Testing project tools",
                default_fields_of_study=["Computer Science", "AI"],
            )

            assert "Created research project" in result
            assert "Tool Test Project" in result
            assert project_root.exists()

    def test_list_projects_tool(self):
        """Test ListProjectsTool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project
            project_root = Path(tmpdir) / "list_test"
            agent.create_project(
                project_root=project_root,
                project_name="List Test Project",
                activate=True,
            )

            # Test tool
            list_tool = ListProjectsTool(agent)
            result = list_tool.apply()
            result_data = json.loads(result)

            assert result_data["total_projects"] == 1
            assert result_data["active_project"] == "List Test Project"

    def test_activate_project_tool(self):
        """Test ActivateProjectTool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create two projects
            project_root1 = Path(tmpdir) / "project1"
            agent.create_project(
                project_root=project_root1,
                project_name="Project 1",
                activate=True,
            )

            project_root2 = Path(tmpdir) / "project2"
            agent.create_project(
                project_root=project_root2,
                project_name="Project 2",
                activate=False,
            )

            # Activate project 2
            activate_tool = ActivateProjectTool(agent)
            result = activate_tool.apply("Project 2")

            assert "Project 2" in result or "project2" in result
            assert agent.get_active_project().project_name == "Project 2"

    def test_get_current_config_tool(self):
        """Test GetCurrentConfigTool."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project
            project_root = Path(tmpdir) / "config_test"
            agent.create_project(
                project_root=project_root,
                project_name="Config Test",
                activate=True,
            )

            # Test tool
            config_tool = GetCurrentConfigTool(agent)
            result = config_tool.apply()
            config_data = json.loads(result)

            assert "active_project" in config_data
            assert config_data["active_project"]["name"] == "Config Test"
            assert "api_client_configured" in config_data
