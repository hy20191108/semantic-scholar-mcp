# Release Process

This document describes the **fully automated** release process for the semantic-scholar-mcp project.

## Overview

The project uses **manual version management with automated releases**:
- Version numbers are explicitly set in source files
- Git tags automatically trigger GitHub Release creation
- GitHub Releases automatically trigger PyPI publishing
- Complete automation: version bump → tag push → everything else is automatic

## Quick Release Guide (Automated)

### One-Command Release

Use the automated release script:

```bash
# Run the release script
./scripts/release.sh

# It will prompt you for the new version
# Then automatically:
# 1. Update version in pyproject.toml and __init__.py
# 2. Commit changes
# 3. Create and push git tag
# 4. Trigger automatic GitHub Release creation
# 5. Trigger automatic PyPI publishing
```

### Manual Release (Alternative)

If you prefer manual control:

**Step 1: Update Version**

```bash
# 1. pyproject.toml
version = "0.2.7"

# 2. src/semantic_scholar_mcp/__init__.py
__version__ = "0.2.7"
```

**Step 2: Commit and Push Tag**

```bash
# Commit version bump
git add pyproject.toml src/semantic_scholar_mcp/__init__.py
git commit -m "chore: bump version to 0.2.7"
git push

# Create and push tag (this triggers automatic release)
git tag -a v0.2.7 -m "Release 0.2.7"
git push origin v0.2.7
```

That's it! The automation will:
1. Create GitHub Release (auto-release.yml)
2. Verify version matches tag (release.yml)
3. Build distribution packages (release.yml)
4. Publish to PyPI (release.yml)

## Pre-Release Checklist

Before releasing, ensure all quality gates pass:

```bash
# 1. Run linting and formatting
uv run --frozen ruff check . --fix --unsafe-fixes
uv run --frozen ruff format .

# 2. Run type checking
uv run --frozen mypy src/

# 3. Run all tests with coverage
uv run --frozen pytest tests/ -v --tb=short

# 4. Check MCP server startup
DEBUG_MCP_MODE=true uv run semantic-scholar-mcp 2>&1 | timeout 3s cat

# 5. Build package locally (verify it builds)
uv build
```

**If any of these fail, DO NOT RELEASE until fixed.**

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Patch** (0.2.2 → 0.2.3): Bug fixes, small improvements
- **Minor** (0.2.3 → 0.3.0): New features, backwards compatible
- **Major** (0.2.3 → 1.0.0): Breaking changes, API changes

## Detailed Release Steps

### 1. Prepare Release

```bash
# Ensure working directory is clean
git status

# Pull latest changes
git pull origin main

# Create release branch (optional)
git checkout -b release/v0.2.3
```

### 2. Update Version Numbers

Edit these two files:

**pyproject.toml:**
```toml
[project]
name = "semantic-scholar-mcp"
version = "0.2.3"  # Update this
```

**src/semantic_scholar_mcp/__init__.py:**
```python
__version__ = "0.2.3"  # Update this
```

### 3. Update Documentation

Update `CHANGELOG.md` (if exists) or create release notes:

```markdown
## [0.2.3] - 2024-01-15

### Added
- New feature X

### Changed
- Improved Y

### Fixed
- Bug Z
```

### 4. Commit Changes

```bash
git add pyproject.toml src/semantic_scholar_mcp/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.2.3"
git push origin main  # or release/v0.2.3
```

### 5. Create GitHub Release

Using GitHub CLI:

```bash
gh release create v0.2.3 \
  --title "Release v0.2.3" \
  --notes-file CHANGELOG.md  # or write notes directly
```

Or using GitHub web interface:

1. Go to https://github.com/hy20191108/semantic-scholar-mcp/releases
2. Click "Create a new release"
3. **Tag**: `v0.2.3` (must match version in files)
4. **Title**: `Release v0.2.3`
5. **Description**: Release notes
6. Click "Publish release"

### 6. Verify Publication

The GitHub Actions workflow will automatically:

1. **Verify** version in `pyproject.toml` matches tag
2. **Build** wheel and source distribution
3. **Publish** to PyPI using OIDC trusted publishing

Check the workflow:
- https://github.com/hy20191108/semantic-scholar-mcp/actions

Verify PyPI:
- https://pypi.org/project/semantic-scholar-mcp/

## Testing Before Release

### Test PyPI (Optional)

To test the release process without publishing to production PyPI:

```bash
# Manually trigger TestPyPI workflow
gh workflow run test-pypi.yml
```

This will publish to https://test.pypi.org/project/semantic-scholar-mcp/

### Local Build Test

```bash
# Build locally
uv build

# Check artifacts
ls -la dist/

# Verify package
uv run twine check dist/*

# Test installation locally
uvx --from dist/semantic_scholar_mcp-0.2.3-py3-none-any.whl semantic-scholar-mcp
```

## CI/CD Pipeline

### Workflow Triggers

The `release.yml` workflow is triggered by:
- **GitHub Release publication** (recommended)

### Workflow Steps

1. **Checkout code**: Fetch repository
2. **Install uv**: Set up uv package manager
3. **Setup Python 3.10**: Install Python
4. **Verify version**: Ensure tag matches package version
5. **Build package**: Create wheel and source distribution
6. **Verify artifacts**: Check build outputs exist
7. **Publish to PyPI**: Upload using OIDC trusted publishing

### Workflow Configuration

See `.github/workflows/release.yml`:

```yaml
name: Release to PyPI

on:
  release:
    types: [published]

jobs:
  build-and-publish:
    name: Build and Publish to PyPI
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Verify version matches release tag
        run: |
          PACKAGE_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
          RELEASE_TAG=${{ github.event.release.tag_name }}
          RELEASE_VERSION=${RELEASE_TAG#v}
          if [ "$PACKAGE_VERSION" != "$RELEASE_VERSION" ]; then
            echo "Error: Version mismatch"
            exit 1
          fi

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

## Troubleshooting

### Common Issues

#### Version Mismatch Error

**Problem:** GitHub Actions fails with "Version does not match release tag"

**Solution:**
```bash
# Check versions match
grep '^version = ' pyproject.toml
grep '__version__' src/semantic_scholar_mcp/__init__.py

# Update both to match the tag
```

#### Build Fails

**Problem:** `uv build` fails during workflow

**Solution:**
```bash
# Test build locally first
uv build

# Fix any errors, then commit and re-release
```

#### PyPI Upload Fails

**Problem:** Publishing to PyPI fails

**Possible causes:**
1. **Version already exists on PyPI**: Bump version and release again
2. **OIDC not configured**: Check repository settings for trusted publishing
3. **Network issues**: Re-run the workflow

**Check PyPI:**
```bash
# Check if version exists
curl -s https://pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.releases | keys[]'
```

### Manual Recovery

If automatic publishing fails, you can publish manually:

```bash
# Build locally
uv build

# Publish manually (requires PyPI credentials)
uv publish

# Or use twine
uv run twine upload dist/*
```

## Security

- **OIDC Trusted Publishing**: Secure authentication without API tokens
- **No credentials in repository**: All authentication via GitHub Actions
- **Automated security scanning**: Dependabot and GitHub security alerts
- **Version verification**: Prevents accidental publishes with wrong versions

## Best Practices

### Release Notes

Include in your GitHub Release description:

```markdown
## What's New

### Features
- Added new feature X
- Improved feature Y

### Bug Fixes
- Fixed issue Z

### Breaking Changes (if any)
- Changed API endpoint format

### Upgrade Guide (if needed)
- Update config file
- Run migration script
```

### Version Management Tips

1. **Keep versions in sync**: Always update both files together
2. **Test before releasing**: Run all quality checks locally
3. **Write clear release notes**: Help users understand changes
4. **Follow semantic versioning**: Make breaking changes clear
5. **Tag releases**: Use `v` prefix (e.g., `v0.2.3`)

### Communication

- Announce major releases on project channels
- Update documentation with new features
- Notify users of breaking changes in advance

## Version Checking Commands

```bash
# Check current PyPI version
curl -s https://pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.info.version'

# Check local version
uv run python -c "from semantic_scholar_mcp import __version__; print(__version__)"

# Check all available versions on PyPI
curl -s https://pypi.org/pypi/semantic-scholar-mcp/json | jq -r '.releases | keys[]' | sort -V

# Check git tags
git tag --list --sort=-version:refname | head -5
```

## Release Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│               SIMPLIFIED RELEASE WORKFLOW                   │
├─────────────────────────────────────────────────────────────┤
│ 1. UPDATE VERSION                                           │
│    ├─── Edit pyproject.toml: version = "X.Y.Z"             │
│    └─── Edit __init__.py: __version__ = "X.Y.Z"            │
│                                                             │
│ 2. RUN QUALITY CHECKS                                       │
│    ├─── uv run ruff check . --fix                          │
│    ├─── uv run mypy src/                                   │
│    └─── uv run pytest tests/                               │
│                                                             │
│ 3. COMMIT & PUSH                                            │
│    └─── git commit -m "chore: bump version to X.Y.Z"       │
│                                                             │
│ 4. CREATE GITHUB RELEASE                                    │
│    └─── gh release create vX.Y.Z                           │
│                                                             │
│ 5. AUTOMATED BUILD & PUBLISH                                │
│    ├─── Verify version matches tag                         │
│    ├─── Build packages (uv build)                          │
│    ├─── Validate artifacts                                 │
│    └─── Publish to PyPI (OIDC)                             │
│                                                             │
│ 6. VERIFY                                                   │
│    └─── Check PyPI: pip install semantic-scholar-mcp       │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "semantic-scholar-mcp"
version = "0.2.2"  # Manual version management
```

### GitHub Actions

- **Main workflow**: `.github/workflows/release.yml`
- **Test workflow**: `.github/workflows/test-pypi.yml` (manual trigger only)
- **CI workflow**: `.github/workflows/ci.yml` (runs on PR/push)

---

For questions or issues with the release process, please open an issue on GitHub.
