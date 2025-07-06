#!/usr/bin/env python3
"""Simple test to verify the server can start."""

import subprocess
import sys
import time
import os

def test_server_startup():
    """Test that the server can start without errors."""
    print("=== Testing MCP Server Startup ===\n")
    
    # Test 1: Import test
    print("1. Testing imports...")
    try:
        import semantic_scholar_mcp.server
        print("   ✓ Server module imported successfully")
    except Exception as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: Run server with --help
    print("\n2. Testing server help...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "semantic_scholar_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   ✓ Server help displayed successfully")
        else:
            print(f"   ✗ Server help failed: {result.stderr}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Check if server can be started
    print("\n3. Testing server startup (5 second test)...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "semantic_scholar_mcp"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print("   ✓ Server started successfully")
            process.terminate()
            process.wait(timeout=3)
            print("   ✓ Server terminated cleanly")
        else:
            stdout, stderr = process.communicate()
            print(f"   ✗ Server exited with code: {process.returncode}")
            if stderr:
                print(f"   Error output: {stderr}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n✅ Basic tests completed!")
    return True

def test_with_mcp_dev():
    """Test using mcp dev command."""
    print("\n=== Testing with MCP Dev ===\n")
    
    print("To test the server interactively, run:")
    print("  uv run mcp dev src/semantic_scholar_mcp/server.py")
    print("\nThis will start the MCP Inspector where you can:")
    print("  1. View available tools")
    print("  2. Test tool execution")
    print("  3. Check resources and prompts")
    
    print("\nExample tool calls to try:")
    print('  - search_papers: {"query": "machine learning", "limit": 5}')
    print('  - health_check: {}')
    print('  - search_authors: {"query": "Yoshua Bengio", "limit": 3}')

def main():
    """Run tests."""
    # Run basic tests
    test_server_startup()
    
    # Show interactive testing instructions
    test_with_mcp_dev()

if __name__ == "__main__":
    main()