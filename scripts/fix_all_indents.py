#!/usr/bin/env python3
"""
Fix all indentation issues after try block removal.
"""

from pathlib import Path


def main():
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        content = f.read()

    # Fix patterns where code after try removal has wrong indent
    # Pattern: 8 spaces at start of line where it should be 4
    lines = content.split("\n")

    for i in range(len(lines)):
        line = lines[i]

        # Check if this line has 8 spaces but should have 4
        # This happens after try: removal
        if line.startswith("        ") and not line.startswith("            "):
            # Check context - if previous non-empty line has 0-4 spaces, this needs fixing
            prev_i = i - 1
            while prev_i >= 0 and not lines[prev_i].strip():
                prev_i -= 1

            if prev_i >= 0:
                prev_line = lines[prev_i]
                prev_indent = len(prev_line) - len(prev_line.lstrip())

                # If previous line is at function level (4 spaces) or less,
                # and current line starts an await call or assignment
                if prev_indent <= 4 and ("await " in line or "=" in line):
                    # Fix: remove 4 spaces
                    lines[i] = line[4:]
                    print(f"Fixed indentation at line {i + 1}")

    # Join back
    content = "\n".join(lines)

    # Write back
    print(f"Writing to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Done!")


if __name__ == "__main__":
    main()
