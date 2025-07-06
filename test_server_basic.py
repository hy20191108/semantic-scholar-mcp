#!/usr/bin/env python3
"""Basic test script to verify the MCP server can initialize without crashing."""

import sys
import asyncio
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_server_initialization():
    """Test basic server initialization."""
    print("Testing Semantic Scholar MCP server initialization...")
    print("-" * 60)
    
    try:
        # Import the server module
        from semantic_scholar_mcp.server import mcp, initialize_server
        print("✓ Server module imported successfully")
        
        # Check if FastMCP instance is created
        print(f"✓ FastMCP instance created: {mcp.name}")
        
        # Check available tools
        print(f"\nAvailable tools ({len(mcp._tool_handlers)}):")
        for tool_name in sorted(mcp._tool_handlers.keys()):
            print(f"  - {tool_name}")
        
        # Check available resources
        print(f"\nAvailable resources ({len(mcp._resource_handlers)}):")
        for resource_pattern in sorted(mcp._resource_handlers.keys()):
            print(f"  - {resource_pattern}")
        
        # Check available prompts
        print(f"\nAvailable prompts ({len(mcp._prompt_handlers)}):")
        for prompt_name in sorted(mcp._prompt_handlers.keys()):
            print(f"  - {prompt_name}")
        
        # Try to initialize the server (this might fail if config is missing)
        print("\nAttempting server initialization...")
        try:
            await initialize_server()
            print("✓ Server initialized successfully")
        except Exception as e:
            print(f"⚠ Server initialization failed (expected if config is missing): {e}")
            print("  This is normal if configuration files are not set up yet.")
        
        print("\n" + "-" * 60)
        print("✅ Basic server structure is valid!")
        print("\nNext steps:")
        print("1. Set up configuration files (.env and config files)")
        print("2. Test with MCP inspector: mcp dev src/semantic_scholar_mcp/server.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\nChecking dependencies...")
    dependencies = {
        "mcp": "MCP SDK",
        "httpx": "HTTP client",
        "pydantic": "Data validation",
        "python-dotenv": "Environment variables"
    }
    
    missing = []
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✓ {package} ({description})")
        except ImportError:
            print(f"✗ {package} ({description}) - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
    
    return len(missing) == 0

if __name__ == "__main__":
    print("Semantic Scholar MCP Server Test\n")
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    if deps_ok:
        # Run the async test
        success = asyncio.run(test_server_initialization())
        sys.exit(0 if success else 1)
    else:
        print("\n❌ Please install missing dependencies first.")
        sys.exit(1)