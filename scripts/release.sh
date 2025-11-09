#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current version
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

echo -e "${GREEN}Current version: ${CURRENT_VERSION}${NC}"
echo ""
echo "Enter new version (e.g., 0.2.7):"
read NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo -e "${RED}Error: Version cannot be empty${NC}"
    exit 1
fi

# Validate version format (semantic versioning)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}Error: Invalid version format. Use semantic versioning (e.g., 0.2.7)${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}This will:${NC}"
echo "  1. Update version to ${NEW_VERSION} in pyproject.toml and __init__.py"
echo "  2. Commit the changes"
echo "  3. Create and push tag v${NEW_VERSION}"
echo "  4. Automatically create GitHub Release (via GitHub Actions)"
echo "  5. Automatically publish to PyPI (via GitHub Actions)"
echo ""
echo "Continue? (y/N)"
read CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Aborted${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Updating version files...${NC}"

# Update pyproject.toml
sed -i.bak "s/^version = \".*\"/version = \"${NEW_VERSION}\"/" pyproject.toml
rm -f pyproject.toml.bak

# Update __init__.py
sed -i.bak "s/__version__ = \".*\"/__version__ = \"${NEW_VERSION}\"/" src/semantic_scholar_mcp/__init__.py
rm -f src/semantic_scholar_mcp/__init__.py.bak

echo -e "${GREEN}✓ Version updated to ${NEW_VERSION}${NC}"

echo ""
echo -e "${GREEN}Step 2: Committing changes...${NC}"

git add pyproject.toml src/semantic_scholar_mcp/__init__.py
git commit -m "chore: bump version to ${NEW_VERSION}"

echo -e "${GREEN}✓ Changes committed${NC}"

echo ""
echo -e "${GREEN}Step 3: Creating and pushing tag...${NC}"

git tag -a "v${NEW_VERSION}" -m "Release ${NEW_VERSION}"
git push origin HEAD
git push origin "v${NEW_VERSION}"

echo -e "${GREEN}✓ Tag v${NEW_VERSION} created and pushed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Release initiated successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps (automatic):"
echo "  1. GitHub Actions will create a GitHub Release"
echo "  2. GitHub Actions will publish to PyPI"
echo ""
echo "Monitor progress:"
echo "  - GitHub Actions: https://github.com/hy20191108/semantic-scholar-mcp/actions"
echo "  - GitHub Releases: https://github.com/hy20191108/semantic-scholar-mcp/releases"
echo "  - PyPI: https://pypi.org/project/semantic-scholar-mcp/"
echo ""
