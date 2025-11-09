#!/usr/bin/env python3
"""
Fix indentation after removing try blocks.
"""

from pathlib import Path


def main():
    server_path = Path(__file__).parent.parent / "src/semantic_scholar_mcp/server.py"

    print(f"Reading {server_path}")
    with open(server_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Fix specific known indentation issues
    fixes = [
        (696, 4),  # Line 696 should have 4 spaces indent
        (740, 4),  # And similar for other lines
        (779, 4),
        (821, 4),
        (852, 4),
        (887, 4),
        (927, 4),
        (967, 4),
        (1005, 4),
        (1075, 4),
        (1121, 4),
        (1153, 4),
        (1187, 4),
        (1219, 4),
        (1255, 4),
        (1283, 4),
        (1308, 4),
        (1335, 4),
        (1403, 4),
        (1467, 4),
        (1537, 4),
        (1572, 4),
        (1599, 4),
        (1689, 4),
        (1726, 4),
    ]

    print("\nFixing indentation...")
    for line_num, _indent_spaces in fixes:
        if line_num <= len(lines):
            line_idx = line_num - 1
            # Check if line needs fixing (starts with too many spaces)
            stripped = lines[line_idx].lstrip()
            if stripped and lines[line_idx].startswith("        "):  # 8 spaces
                # Remove 4 spaces (dedent from 8 to 4)
                lines[line_idx] = lines[line_idx][4:]
                print(f"  Fixed indentation at line {line_num}")

    # Write back
    print(f"\nWriting to {server_path}")
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("✅ Done!")


if __name__ == "__main__":
    main()
