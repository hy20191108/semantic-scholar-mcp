"""
Test suite for memory activation bug fixes.

This module tests the bug fixes for:
1. Project activation by path with proper caching
2. Memory tools error handling when no project is active
"""

import json
import tempfile
from pathlib import Path

import pytest

from core.config import ApplicationConfig
from semantic_scholar_mcp.agent import ResearchAgent
from semantic_scholar_mcp.api_client import SemanticScholarClient
from semantic_scholar_mcp.tools.memory_tools import WriteMemoryTool


class TestProjectActivationCaching:
    """Test that project activation by path uses proper caching."""

    def test_path_activation_caching(self):
        """Test that activating by path twice reuses cached project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project
            project_root = Path(tmpdir) / "cache_test"
            project = agent.create_project(
                project_root=project_root,
                project_name="Cache Test Project",
                activate=True,
            )

            # Deactivate by setting to None
            agent._active_project = None

            # Activate by path (first time)
            project1 = agent.activate_project(str(project_root))
            assert project1.project_name == "Cache Test Project"

            # Verify both name and path are registered
            assert "Cache Test Project" in agent._registered_projects
            assert str(project_root) in agent._registered_projects

            # Deactivate again
            agent._active_project = None

            # Activate by path (second time - should use cache)
            project2 = agent.activate_project(str(project_root))
            assert project2.project_name == "Cache Test Project"

            # Verify we have the same project instance
            assert project1.project_root == project2.project_root


class TestMemoryToolsErrorHandling:
    """Test memory tools error handling when no project is active."""

    def test_write_memory_no_active_project(self):
        """Test write_memory with no active project."""
        config = ApplicationConfig()
        api_client = SemanticScholarClient(config=config)
        agent = ResearchAgent(api_client=api_client, config=config)

        # Ensure no project is active
        assert agent.get_active_project() is None

        # Try to write memory - should raise RuntimeError
        tool = WriteMemoryTool(agent)
        with pytest.raises(
            RuntimeError, match="No active project; please activate a project first"
        ):
            tool.apply(memory_name="test", content="# Test")

    def test_memory_tools_after_activation(self):
        """Test memory tools work after project activation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create and activate project
            project_root = Path(tmpdir) / "memory_test"
            agent.create_project(
                project_root=project_root,
                project_name="Memory Test",
                activate=True,
            )

            # Now memory tools should work
            tool = WriteMemoryTool(agent)
            result = tool.apply(memory_name="test_note", content="# Test Note")
            assert "written" in result


class TestServerMemoryFunctions:
    """Test server-level memory functions with _check_active_project."""

    @pytest.mark.asyncio
    async def test_server_check_active_project_helper(self):
        """Test _check_active_project helper function."""
        from semantic_scholar_mcp import server

        # Save original research_agent
        original_agent = server.research_agent

        try:
            # Test 1: research_agent is None
            server.research_agent = None
            is_active, error_msg = server._check_active_project()
            assert not is_active
            assert "ResearchAgent not initialized" in error_msg

            # Test 2: research_agent exists but no active project
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)
            server.research_agent = agent

            is_active, error_msg = server._check_active_project()
            assert not is_active
            assert "No project is currently active" in error_msg
            assert "create_project or activate_project" in error_msg

            # Test 3: research_agent exists with active project
            with tempfile.TemporaryDirectory() as tmpdir:
                project_root = Path(tmpdir) / "active_test"
                agent.create_project(
                    project_root=project_root,
                    project_name="Active Test",
                    activate=True,
                )

                is_active, error_msg = server._check_active_project()
                assert is_active
                assert error_msg is None

        finally:
            # Restore original research_agent
            server.research_agent = original_agent


class TestProjectActivationEdgeCases:
    """Test edge cases in project activation."""

    def test_activate_by_name_after_path_activation(self):
        """Test activating by name after initial path activation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project
            project_root = Path(tmpdir) / "name_path_test"
            agent.create_project(
                project_root=project_root,
                project_name="Name Path Test",
                activate=False,
            )

            # Activate by path
            agent.activate_project(str(project_root))
            assert agent.get_active_project().project_name == "Name Path Test"

            # Deactivate
            agent._active_project = None

            # Activate by name (should work because it was registered)
            agent.activate_project("Name Path Test")
            assert agent.get_active_project().project_name == "Name Path Test"

    def test_normalized_path_handling(self):
        """Test that paths are properly normalized for lookup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ApplicationConfig()
            api_client = SemanticScholarClient(config=config)
            agent = ResearchAgent(api_client=api_client, config=config)

            # Create project with absolute path
            project_root = Path(tmpdir) / "norm_test"
            agent.create_project(
                project_root=project_root,
                project_name="Normalization Test",
                activate=True,
            )

            # Deactivate
            agent._active_project = None

            # Try activating with unnormalized path (with ..)
            unnormalized_path = str(project_root / ".." / "norm_test")
            agent.activate_project(unnormalized_path)

            # Should successfully activate
            assert agent.get_active_project().project_name == "Normalization Test"
