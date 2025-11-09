#!/usr/bin/env python3
"""
Final comprehensive fix for server.py
"""

from pathlib import Path


def main():
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Track which lines to delete
    lines_to_delete = set()

    # Find all orphan try: statements
    print("\n1. Finding orphan try statements...")
    for i, line in enumerate(lines):
        if line.strip() == "try:":
            # Check if there's an except within next 30 lines
            has_except = False
            for j in range(i + 1, min(i + 30, len(lines))):
                if "except" in lines[j] and ":" in lines[j]:
                    has_except = True
                    break
                if lines[j].strip().startswith("@") or "async def " in lines[j]:
                    break

            if not has_except:
                print(f"  Found orphan try at line {i + 1}")
                lines_to_delete.add(i)

    # Find all RequestContext lines
    print("\n2. Finding RequestContext lines...")
    for i, line in enumerate(lines):
        if "with RequestContext" in line:
            print(f"  Found RequestContext at line {i + 1}")
            lines_to_delete.add(i)

    # Create new content
    print("\n3. Creating fixed content...")
    new_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_delete:
            new_lines.append(line)

    # Join and do final replacements
    content = "".join(new_lines)

    # Add missing definitions at the top (after imports)
    print("\n4. Adding missing definitions...")

    # Find the end of imports
    import_end = 0
    for i, line in enumerate(new_lines):
        if line.startswith(("from ", "import ")):
            import_end = i

    # Insert after imports
    additions = []

    # Add mcp
    if "mcp = FastMCP" not in content:
        additions.append("""
# Initialize MCP server
mcp = FastMCP(
    "Semantic Scholar MCP Server",
    version="0.2.2"
)
""")

    # Add logger
    if "logger = get_logger" not in content:
        additions.append("logger = get_logger(__name__)")

    # Add ToolResult
    if "ToolResult = " not in content:
        additions.append("ToolResult = dict[str, Any]  # Type alias for tool results")

    # Add TResult
    if "TResult = TypeVar" not in content:
        additions.append("TResult = TypeVar('TResult')")

    if additions:
        # Insert additions after imports
        new_lines.insert(import_end + 2, "\n# Definitions for Serena compliance\n")
        new_lines.insert(import_end + 3, "\n".join(additions) + "\n\n")

    # Write back
    print(f"\n5. Writing to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("\n✅ Done!")
    print("\nRemaining manual fixes needed:")
    print("1. Replace @with_tool_instructions with @inject_yaml_instructions")
    print("2. Remove @mcp_error_handler decorators")
    print("3. Change return types from dict[str, Any] to str")
    print("4. Fix return statements to use json.dumps()")


if __name__ == "__main__":
    main()
