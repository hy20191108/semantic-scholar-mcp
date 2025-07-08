# Release Process

This document describes the automated release process for the semantic-scholar-mcp project.

## Overview

The project uses **hatch-vcs** for automatic version management based on Git tags. This provides:
- Single source of truth for versioning (Git tags)
- Automatic version generation during build
- No manual version updates required
- Seamless integration with PyPI publishing

## Release Workflow

### 1. Automatic Releases (Recommended)

Use the provided release script for a fully automated release:

```bash
# Patch version (e.g., 0.1.3 → 0.1.4)
./scripts/release.sh patch

# Minor version (e.g., 0.1.3 → 0.2.0)
./scripts/release.sh minor

# Major version (e.g., 0.1.3 → 1.0.0)
./scripts/release.sh major
```

The script will:
1. Validate git status and branch
2. Run tests and linting
3. Create and push a new Git tag
4. Trigger GitHub Actions for PyPI publishing

### 2. Manual Releases

If you prefer manual control:

```bash
# Create a new tag
git tag -a v0.1.4 -m "Release 0.1.4"

# Push the tag
git push origin v0.1.4
```

### 3. GitHub Releases

For creating a GitHub release (optional):

1. Go to https://github.com/hy20191108/semantic-scholar-mcp/releases
2. Click "Create a new release"
3. Select your tag or create a new one
4. Add release notes
5. Click "Publish release"

## Version Management

### How It Works

- **hatch-vcs** automatically determines the version from Git tags
- Version follows semantic versioning (MAJOR.MINOR.PATCH)
- Tags must be prefixed with 'v' (e.g., v0.1.4)
- Build process generates `_version.py` file automatically

### Version Sources

1. **Git tags** (primary): Exact version from tag
2. **Git commits**: Distance from last tag (dev versions)
3. **Fallback**: 0.2.0 (if no tags exist)

### Tag Format

```
v<MAJOR>.<MINOR>.<PATCH>
```

Examples:
- `v0.1.4` → version 0.1.4
- `v1.0.0` → version 1.0.0
- `v2.1.5` → version 2.1.5

## CI/CD Pipeline

### Triggers

GitHub Actions will automatically publish to PyPI when:
- A new tag starting with 'v' is pushed
- A GitHub release is published
- Workflow is manually triggered

### Workflow Steps

1. **Setup**: Install uv and Python
2. **Dependencies**: Install with `uv sync --locked`
3. **Quality**: Run tests and linting
4. **Build**: Create distribution packages
5. **Publish**: Upload to PyPI using trusted publishing

## Best Practices

### Before Releasing

1. **Update documentation** if needed
2. **Run tests locally**: `uv run pytest`
3. **Check linting**: `uv run ruff check .`
4. **Verify changes** are committed and pushed

### Version Bumping Guidelines

- **Patch** (0.1.3 → 0.1.4): Bug fixes, small improvements
- **Minor** (0.1.3 → 0.2.0): New features, backwards compatible
- **Major** (0.1.3 → 1.0.0): Breaking changes, API changes

### Release Notes

Consider adding release notes for:
- New features
- Breaking changes
- Bug fixes
- Performance improvements
- Security updates

## Troubleshooting

### Common Issues

1. **Tag already exists**: Use `git tag -d v0.1.4` to delete locally
2. **Tests failing**: Fix issues before releasing
3. **Linting errors**: Run `uv run ruff check . --fix`
4. **Permission denied**: Check PyPI trusted publishing configuration

### Manual Recovery

If automatic publishing fails:

```bash
# Build locally
uv build

# Check distribution
ls -la dist/

# Manually publish (if needed)
uv publish
```

## Configuration

### pyproject.toml

Key configuration sections:

```toml
[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
tag-prefix = "v"
fallback-version = "0.2.0"

[tool.hatch.build.hooks.vcs]
version-file = "src/semantic_scholar_mcp/_version.py"
```

### GitHub Actions

See `.github/workflows/release.yml` for the complete CI/CD configuration.

## Security

- Uses **OpenID Connect (OIDC)** for secure PyPI publishing
- No API tokens stored in repository
- Trusted publishing configured for GitHub Actions
- Automatic security scanning via GitHub

---

For questions or issues, please open an issue on GitHub.