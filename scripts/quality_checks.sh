#!/bin/bash
# Quality checks script for Semantic Scholar MCP
#
# This script runs all required quality checks before committing:
# 1. Ruff linting with auto-fixes
# 2. Ruff code formatting
# 3. Mypy type checking
# 4. Pytest test suite
#
# Usage: ./scripts/quality_checks.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed

set -e  # Exit on any error

echo "======================================================================"
echo "  QUALITY CHECKS FOR SEMANTIC SCHOLAR MCP"
echo "======================================================================"
echo ""

# Change to project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Working directory: $PROJECT_ROOT"
echo ""

# 1. Ruff linting
echo "[1/4] Running Ruff linting..."
echo "  - Checking code style violations"
echo "  - Applying auto-fixes where possible"
uv run --frozen ruff check . --fix --unsafe-fixes
echo "✅ Ruff linting passed"
echo ""

# 2. Ruff formatting
echo "[2/4] Running Ruff formatting..."
echo "  - Formatting Python code to 88 character line limit"
uv run --frozen ruff format .
echo "✅ Ruff formatting passed"
echo ""

# 3. Mypy type checking
echo "[3/4] Running Mypy type checking..."
echo "  - Verifying type hints in src/ directory"
uv run --frozen mypy src/
echo "✅ Mypy type checking passed"
echo ""

# 4. Pytest
echo "[4/4] Running Pytest..."
echo "  - Executing test suite with verbose output"
uv run --frozen pytest tests/ -v --tb=short
echo "✅ Pytest passed"
echo ""

echo "======================================================================"
echo "  ✅ ALL QUALITY CHECKS PASSED!"
echo "======================================================================"
echo ""
echo "Ready to commit. All quality gates satisfied."
echo ""
