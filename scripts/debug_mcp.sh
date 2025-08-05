#!/bin/bash
# MCP Debug Automation Script

set -e

echo "🧪 MCP Automated Debug Session"
echo "=============================="

# Change to project root
cd "$(dirname "$0")/.."

# Function to cleanup background processes
cleanup() {
    echo "🧹 Cleaning up..."
    jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

echo "📋 Phase 1: Component Testing"
echo "-----------------------------"

# Run automated component tests
if uv run python tests/test_mcp_automation.py; then
    echo "✅ Component tests completed successfully"
    COMPONENT_SUCCESS=true
else
    echo "❌ Component tests found issues"
    COMPONENT_SUCCESS=false
fi

echo ""
echo "📋 Phase 2: MCP Inspector (Manual Testing)"
echo "------------------------------------------"

if [ "$COMPONENT_SUCCESS" = true ]; then
    echo "🚀 Starting MCP Inspector for manual testing..."
    echo ""
    echo "Instructions:"
    echo "1. Inspector will start in background"
    echo "2. Open the URL in your browser"
    echo "3. Test the tools mentioned in docs/DEBUG_TEST_RESULTS.md"
    echo "4. Press Ctrl+C when done"
    echo ""
    
    # Start MCP Inspector
    uv run mcp dev scripts/server_standalone.py
else
    echo "⚠️ Skipping MCP Inspector due to component test failures"
    echo "📄 Check docs/DEBUG_TEST_RESULTS.md for details"
    exit 1
fi

echo ""
echo "🏁 Debug session complete"
echo "📊 Check docs/DEBUG_TEST_RESULTS.md for results"