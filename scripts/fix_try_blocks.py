#!/usr/bin/env python3
"""
Fix all incomplete try blocks in server.py
"""

from pathlib import Path


def fix_try_blocks(content: str) -> str:
    """Remove all standalone try: statements without except blocks."""

    # Pattern to find try: without matching except
    # This will find lines with just "try:" at various indentation levels
    lines = content.split("\n")
    result = []
    skip_next = False

    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue

        # Check if this is a standalone try:
        if line.strip() == "try:":
            # Look ahead to see if there's an except
            has_except = False
            for j in range(i + 1, min(i + 50, len(lines))):
                if lines[j].strip().startswith("except"):
                    has_except = True
                    break
                # If we hit another function or decorator, stop looking
                if (
                    lines[j].strip().startswith("@")
                    or lines[j].strip().startswith("def ")
                    or lines[j].strip().startswith("async def")
                ):
                    break

            # If no except found, skip this try line
            if not has_except:
                print(f"Removing orphan try: at line {i + 1}")
                continue

        result.append(line)

    return "\n".join(result)


def remove_with_request_context(content: str) -> str:
    """Remove all 'with RequestContext():' blocks and dedent their content."""

    lines = content.split("\n")
    result = []
    in_context = False
    context_indent = 0

    for i, line in enumerate(lines):
        # Check for RequestContext
        if "with RequestContext" in line:
            in_context = True
            context_indent = len(line) - len(line.lstrip())
            print(f"Removing RequestContext at line {i + 1}")
            continue

        # If we're in a context block
        if in_context:
            # Check if we've exited the block
            if (line and not line[0].isspace()) or (
                line.strip() and len(line) - len(line.lstrip()) <= context_indent
            ):
                in_context = False
                result.append(line)
            elif line.strip():
                # Dedent by 4 spaces
                if line.startswith("    "):
                    result.append(line[4:])
                else:
                    result.append(line)
            else:
                result.append(line)
        else:
            result.append(line)

    return "\n".join(result)


def add_missing_imports(content: str) -> str:
    """Add missing imports and definitions."""

    # Check what's missing and add
    additions = []

    if "logger = " not in content and "logger." in content:
        additions.append("logger = get_logger(__name__)")

    if "class ToolResult" not in content and "ToolResult" in content:
        additions.append("ToolResult = dict[str, Any]  # Type alias for tool results")

    if "TResult = " not in content and "TResult" in content:
        additions.append("TResult = TypeVar('TResult')")

    if additions:
        # Find where to insert (after imports)
        import_end = content.rfind("\nfrom ")
        if import_end == -1:
            import_end = content.rfind("\nimport ")

        if import_end != -1:
            # Find the end of that line
            newline_pos = content.find("\n", import_end + 1)
            if newline_pos != -1:
                # Insert after imports
                content = (
                    content[:newline_pos]
                    + "\n\n# Type definitions and logger\n"
                    + "\n".join(additions)
                    + "\n"
                    + content[newline_pos:]
                )

    return content


def fix_mcp_undefined(content: str) -> str:
    """Fix undefined mcp variable."""

    # Check if mcp is defined
    if "mcp = " not in content:
        # Add mcp = FastMCP() after imports
        import_end = content.rfind("\nfrom ")
        if import_end == -1:
            import_end = content.rfind("\nimport ")

        if import_end != -1:
            # Find the end of that line
            newline_pos = content.find("\n", import_end + 1)
            if newline_pos != -1:
                # Check if it's not already there
                if "mcp = FastMCP" not in content:
                    # Insert after imports
                    mcp_init = """
# Initialize MCP server
mcp = FastMCP(
    "Semantic Scholar MCP Server",
    version="0.2.2"
)
"""
                    content = (
                        content[:newline_pos] + "\n" + mcp_init + content[newline_pos:]
                    )

    return content


def main():
    """Main function."""
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    content = server_path.read_text(encoding="utf-8")

    print("\n1. Removing orphan try blocks...")
    content = fix_try_blocks(content)

    print("\n2. Removing RequestContext blocks...")
    content = remove_with_request_context(content)

    print("\n3. Adding missing imports and definitions...")
    content = add_missing_imports(content)

    print("\n4. Fixing undefined mcp...")
    content = fix_mcp_undefined(content)

    print(f"\n5. Writing back to {server_path}")
    server_path.write_text(content, encoding="utf-8")

    print("\n✅ Fixed structural issues!")


if __name__ == "__main__":
    main()
