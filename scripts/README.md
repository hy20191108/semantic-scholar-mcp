# Scripts Directory

This directory contains development and testing scripts for the Semantic Scholar MCP server.

## Tool Testing

### MCP Inspector (Recommended)

For comprehensive testing of all 24 tools, use the official MCP Inspector:

```bash
npx @modelcontextprotocol/inspector semantic-scholar-dev
```

This provides:
- ✅ Full MCP protocol support
- ✅ Interactive tool testing
- ✅ Real-time request/response inspection
- ✅ All 24 tools available

### Alternative: Pytest Test Suite

For automated testing in CI/CD:

```bash
uv run pytest tests/test_all_tools.py -v
```

This test suite covers all 24 tools across 6 categories.

## Development Scripts

### release.sh

Automated release script for version management and GitHub/PyPI publishing.

```bash
./scripts/release.sh
```

### debug_mcp.sh

Debug MCP server startup and behavior.

```bash
./scripts/debug_mcp.sh
```

## Utility Scripts

Other scripts in this directory are development utilities:
- `batch_*.py`: Batch processing tools
- `convert_*.py`: Migration and conversion scripts
- `fix_*.py`: Code fixing utilities
- `quality_checks.sh`: Quality assurance checks

Most of these are historical and may not be actively maintained.
