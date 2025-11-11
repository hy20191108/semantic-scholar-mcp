"""
Memory management tools for Semantic Scholar MCP (Serena-compliant).

This module provides tools for managing project-specific memories,
following the Serena architecture pattern.
"""

import re

from .base import Tool


class WriteMemoryTool(Tool):
    """
    Write a memory to the project's memory store.

    Memories are stored as Markdown files and can contain research notes,
    paper summaries, search strategies, and other project-specific information.
    """

    def apply(self, memory_name: str, content: str, max_chars: int = 100000) -> str:
        """
        Write a memory file.

        Args:
            memory_name: Name of the memory (without .md extension)
            content: Content to write (Markdown format)
            max_chars: Maximum allowed content length (default: 100000)

        Returns:
            Success message

        Raises:
            ValueError: If content is too long or max_chars is invalid
        """
        if max_chars <= 0:
            raise ValueError("max_chars must be a positive integer")

        if len(content) > max_chars:
            raise ValueError(
                f"Content for {memory_name} is too long. "
                f"Max length is {max_chars} characters. "
                "Please make the content shorter."
            )

        return self.memories_manager.save_memory(memory_name, content)


class ReadMemoryTool(Tool):
    """
    Read a memory from the project's memory store.

    Use this tool to retrieve previously stored research notes, paper summaries,
    and other project-specific information.
    """

    def apply(self, memory_name: str) -> str:
        """
        Read a memory file.

        Args:
            memory_name: Name of the memory (without .md extension)

        Returns:
            Content of the memory file, or error message if not found

        Note:
            This tool should only be used if the information is relevant to the
            current task. You can infer relevance from the memory file name.
            You should not read the same memory file multiple times in the same
            conversation.
        """
        return self.memories_manager.load_memory(memory_name)


class ListMemoriesTool(Tool):
    """
    List all available memories in the project.

    This tool shows all stored memories, which can help you discover existing
    research notes and documentation.
    """

    def apply(self) -> str:
        """
        List all memories.

        Returns:
            JSON string containing list of memory names
        """
        import json

        memories = self.memories_manager.list_memories()
        return json.dumps({"memories": memories, "count": len(memories)}, indent=2)


class DeleteMemoryTool(Tool):
    """
    Delete a memory from the project's memory store.

    Use this tool when a memory is no longer needed or contains outdated information.
    """

    def apply(self, memory_name: str) -> str:
        """
        Delete a memory file.

        Args:
            memory_name: Name of the memory to delete

        Returns:
            Success message

        Note:
            This operation cannot be undone. Make sure you really want to delete
            the memory before calling this tool.
        """
        return self.memories_manager.delete_memory(memory_name)


class EditMemoryTool(Tool):
    """
    Edit a memory using regular expression replacement (Serena-compliant).

    This tool allows precise modifications to memory content using regex patterns,
    following the same pattern as Serena's replace_regex tool.
    """

    def apply(
        self,
        memory_name: str,
        regex: str,
        repl: str,
        allow_multiple_occurrences: bool = False,
    ) -> str:
        r"""
        Replace content in a memory using regular expression.

        Args:
            memory_name: Name of the memory to edit
            regex: Python-style regular expression (DOTALL and MULTILINE enabled).
                   '.' matches all characters including newlines.
                   Apply usual escaping for reserved characters.
            repl: Replacement string, may contain backreferences like \1, \2, etc.
                  Insert new content verbatim, except for backslashes which must
                  be escaped.
            allow_multiple_occurrences: If True, replace all matches. If False,
                                        error if pattern matches multiple times.

        Returns:
            Success message with number of replacements made

        Raises:
            ValueError: If pattern matches multiple times and
                       allow_multiple_occurrences is False
            FileNotFoundError: If memory doesn't exist
        """
        # Load the memory content
        content = self.memories_manager.load_memory(memory_name)

        # Check if memory exists
        if content.startswith("Memory file") and "not found" in content:
            raise FileNotFoundError(content)

        # Compile regex with DOTALL and MULTILINE flags
        pattern = re.compile(regex, re.DOTALL | re.MULTILINE)

        # Check number of matches
        matches = pattern.findall(content)
        num_matches = len(matches)

        if num_matches == 0:
            return f"No matches found for pattern '{regex}' in memory {memory_name}"

        if num_matches > 1 and not allow_multiple_occurrences:
            raise ValueError(
                f"Pattern '{regex}' matches {num_matches} times in {memory_name}. "
                f"Please provide a more specific regex or set "
                f"allow_multiple_occurrences=True to replace all occurrences."
            )

        # Perform replacement
        new_content = pattern.sub(repl, content)

        # Save the modified content
        self.memories_manager.save_memory(memory_name, new_content)

        return (
            f"Successfully replaced {num_matches} occurrence(s) in memory {memory_name}"
        )


# Export all tools
__all__ = [
    "DeleteMemoryTool",
    "EditMemoryTool",
    "ListMemoriesTool",
    "ReadMemoryTool",
    "WriteMemoryTool",
]
