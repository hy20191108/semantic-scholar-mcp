#!/usr/bin/env python3
"""
Remove only incomplete try: blocks from server.py
"""

from pathlib import Path


def main():
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        lines = f.readlines()

    print("\nAnalyzing try: statements...")
    lines_to_remove = set()

    for i, line in enumerate(lines):
        if line.strip() == "try:":
            # Check if there's an except within next 20 lines
            has_except = False
            for j in range(i + 1, min(i + 20, len(lines))):
                if "except" in lines[j] and ":" in lines[j]:
                    has_except = True
                    break
                # If we hit a decorator or new function, this try is incomplete
                if lines[j].strip().startswith("@") and j > i + 2:
                    break
                if ("async def" in lines[j] or "def " in lines[j]) and j > i + 2:
                    break

            if not has_except:
                print(f"  Found incomplete try: at line {i + 1}")
                lines_to_remove.add(i)

    # Remove only incomplete try blocks
    new_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_remove:
            new_lines.append(line)

    print(f"\nRemoved {len(lines_to_remove)} incomplete try: statements")

    # Write back
    print(f"Writing to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
