#!/bin/bash

# Simple release script for semantic-scholar-mcp
# Usage: ./scripts/release.sh [patch|minor|major]

set -e

# Default to patch if no argument provided
BUMP_TYPE=${1:-patch}

echo "🚀 Starting release process..."

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Git working directory is not clean. Please commit or stash changes first."
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Not on main branch. Please switch to main branch first."
    exit 1
fi

# Get current version from git tags
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.3")
LAST_VERSION=$(echo $LAST_TAG | sed 's/^v//')

echo "📋 Current version: $LAST_VERSION"

# Parse version components
MAJOR=$(echo $LAST_VERSION | cut -d. -f1)
MINOR=$(echo $LAST_VERSION | cut -d. -f2)
PATCH=$(echo $LAST_VERSION | cut -d. -f3)

# Increment version based on type
case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    *)
        echo "❌ Invalid bump type: $BUMP_TYPE. Use patch, minor, or major."
        exit 1
        ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
NEW_TAG="v$NEW_VERSION"

echo "🔄 Bumping version: $LAST_VERSION → $NEW_VERSION"

# Check if tag already exists
if git rev-parse "$NEW_TAG" >/dev/null 2>&1; then
    echo "❌ Tag $NEW_TAG already exists!"
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Sync dependencies
echo "📦 Syncing dependencies..."
uv sync --all-extras

# Run tests
echo "🧪 Running tests..."
uv run pytest tests/ -v --tb=short || {
    echo "❌ Tests failed! Please fix them before releasing."
    exit 1
}

# Run linting
echo "🔍 Running linter..."
uv run ruff check . || {
    echo "❌ Linting failed! Please fix issues before releasing."
    exit 1
}

# Create and push tag
echo "🏷️  Creating tag $NEW_TAG..."
git tag -a "$NEW_TAG" -m "Release $NEW_VERSION"
git push origin "$NEW_TAG"

echo "✅ Release $NEW_VERSION created successfully!"
echo "📦 GitHub Actions will now build and publish to PyPI automatically."
echo "🔗 Check the workflow: https://github.com/hy20191108/semantic-scholar-mcp/actions"