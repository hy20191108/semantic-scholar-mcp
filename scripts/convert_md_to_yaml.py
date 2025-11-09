#!/usr/bin/env python3
"""
Markdown to YAML converter for tool instructions.

Converts existing Markdown tool instruction files to YAML format
for better structure and easier maintenance.
"""

import re
from pathlib import Path
from typing import Any

import yaml


def parse_markdown_sections(content: str) -> dict[str, str]:
    """
    Parse Markdown content into sections based on headers.

    Expected structure:
    - Description (first paragraph before any header)
    - ### Next Steps (bullet points)
    """
    sections: dict[str, str] = {}

    # Split by ### headers
    parts = re.split(r"^### ", content, flags=re.MULTILINE)

    # First part is the description (before any ###)
    if parts:
        description = parts[0].strip()
        sections["description"] = description

    # Parse subsequent sections
    for part in parts[1:]:
        lines = part.split("\n", 1)
        if len(lines) == 2:
            header = lines[0].strip()
            body = lines[1].strip()

            if header.lower() == "next steps":
                # Clean up bullet points
                next_steps = []
                for line in body.split("\n"):
                    line = line.strip()
                    if line.startswith("-"):
                        # Remove leading dash and clean
                        next_steps.append(line[1:].strip())
                sections["next_steps"] = next_steps

    return sections


def convert_markdown_to_yaml(md_path: Path) -> dict[str, Any]:
    """
    Convert a Markdown tool instruction file to YAML structure.

    Args:
        md_path: Path to the Markdown file

    Returns:
        Dictionary ready for YAML serialization
    """
    content = md_path.read_text(encoding="utf-8")
    sections = parse_markdown_sections(content)

    tool_name = md_path.stem
    category = md_path.parent.name

    return {
        "tool_name": tool_name,
        "category": category,
        "description": sections.get("description", ""),
        "next_steps": sections.get("next_steps", []),
    }


def convert_all_instructions(
    instructions_dir: Path, output_dir: Path | None = None, dry_run: bool = False
) -> None:
    """
    Convert all Markdown instruction files to YAML.

    Args:
        instructions_dir: Root directory containing tool_instructions/
        output_dir: Output directory (defaults to same as input)
        dry_run: If True, print conversions without writing files
    """
    if output_dir is None:
        output_dir = instructions_dir

    # Find all .md files
    md_files = list(instructions_dir.rglob("*.md"))

    print(f"Found {len(md_files)} Markdown files to convert")

    converted = 0
    for md_path in md_files:
        # Skip if not in tool_instructions directory
        if "tool_instructions" not in str(md_path):
            continue

        try:
            # Convert to YAML data
            yaml_data = convert_markdown_to_yaml(md_path)

            # Determine output path
            rel_path = md_path.relative_to(instructions_dir)
            yaml_path = output_dir / rel_path.with_suffix(".yml")

            if dry_run:
                print(f"\n{'=' * 60}")
                print(f"Would convert: {md_path}")
                print(f"         → to: {yaml_path}")
                print("\nYAML content preview:")
                print(yaml.dump(yaml_data, allow_unicode=True, sort_keys=False))
            else:
                # Create output directory
                yaml_path.parent.mkdir(parents=True, exist_ok=True)

                # Write YAML file
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        yaml_data,
                        f,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                    )

                print(f"✓ Converted: {md_path.name} → {yaml_path.name}")
                converted += 1

        except Exception as e:
            print(f"✗ Error converting {md_path}: {e}")

    if not dry_run:
        print(f"\n{'=' * 60}")
        print(f"Successfully converted {converted}/{len(md_files)} files")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Markdown tool instructions to YAML"
    )
    parser.add_argument(
        "--instructions-dir",
        type=Path,
        default=Path(__file__).parent.parent / "src/semantic_scholar_mcp/resources",
        help="Directory containing tool_instructions/ (default: src/semantic_scholar_mcp/resources)",
    )
    parser.add_argument(
        "--output-dir", type=Path, help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print conversions without writing files"
    )

    args = parser.parse_args()

    convert_all_instructions(args.instructions_dir, args.output_dir, args.dry_run)
