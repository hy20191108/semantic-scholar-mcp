#!/usr/bin/env python3
"""Test script to verify all imports in the server module work correctly."""

import sys
import traceback
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test all imports from server.py."""
    print("Testing imports for Semantic Scholar MCP server...")
    print("-" * 60)
    
    errors = []
    
    # Test standard library imports
    print("\n1. Testing standard library imports:")
    try:
        import asyncio
        print("✓ asyncio")
    except ImportError as e:
        errors.append(("asyncio", e))
        print(f"✗ asyncio: {e}")
    
    try:
        from typing import Optional, List, Dict, Any, Union
        print("✓ typing")
    except ImportError as e:
        errors.append(("typing", e))
        print(f"✗ typing: {e}")
    
    try:
        from datetime import datetime
        print("✓ datetime")
    except ImportError as e:
        errors.append(("datetime", e))
        print(f"✗ datetime: {e}")
    
    try:
        import os
        print("✓ os")
    except ImportError as e:
        errors.append(("os", e))
        print(f"✗ os: {e}")
    
    # Test third-party imports
    print("\n2. Testing third-party imports:")
    try:
        from mcp.server.fastmcp import FastMCP
        print("✓ mcp.server.fastmcp")
    except ImportError as e:
        errors.append(("mcp.server.fastmcp", e))
        print(f"✗ mcp.server.fastmcp: {e}")
    
    try:
        from pydantic import BaseModel, Field
        print("✓ pydantic")
    except ImportError as e:
        errors.append(("pydantic", e))
        print(f"✗ pydantic: {e}")
    
    # Test local imports from core module
    print("\n3. Testing core module imports:")
    try:
        from core.config import get_config, ApplicationConfig
        print("✓ core.config")
    except ImportError as e:
        errors.append(("core.config", e))
        print(f"✗ core.config: {e}")
    
    try:
        from core.logging import get_logger, initialize_logging, RequestContext
        print("✓ core.logging")
    except ImportError as e:
        errors.append(("core.logging", e))
        print(f"✗ core.logging: {e}")
    
    try:
        from core.container import ServiceCollection, ServiceProvider
        print("✓ core.container")
    except ImportError as e:
        errors.append(("core.container", e))
        print(f"✗ core.container: {e}")
    
    try:
        from core.exceptions import ValidationError, APIError
        print("✓ core.exceptions")
    except ImportError as e:
        errors.append(("core.exceptions", e))
        print(f"✗ core.exceptions: {e}")
    
    try:
        from core.cache import InMemoryCache
        print("✓ core.cache")
    except ImportError as e:
        errors.append(("core.cache", e))
        print(f"✗ core.cache: {e}")
    
    # Test local imports from semantic_scholar_mcp module
    print("\n4. Testing semantic_scholar_mcp module imports:")
    try:
        from semantic_scholar_mcp.api_client_enhanced import SemanticScholarClient
        print("✓ semantic_scholar_mcp.api_client_enhanced")
    except ImportError as e:
        errors.append(("semantic_scholar_mcp.api_client_enhanced", e))
        print(f"✗ semantic_scholar_mcp.api_client_enhanced: {e}")
    
    try:
        from semantic_scholar_mcp.domain_models import Paper, Author, Citation, Reference, SearchQuery, SearchFilters
        print("✓ semantic_scholar_mcp.domain_models")
    except ImportError as e:
        errors.append(("semantic_scholar_mcp.domain_models", e))
        print(f"✗ semantic_scholar_mcp.domain_models: {e}")
    
    # Test importing the server module itself
    print("\n5. Testing server module import:")
    try:
        import semantic_scholar_mcp.server
        print("✓ semantic_scholar_mcp.server")
    except ImportError as e:
        errors.append(("semantic_scholar_mcp.server", e))
        print(f"✗ semantic_scholar_mcp.server: {e}")
        traceback.print_exc()
    
    # Summary
    print("\n" + "-" * 60)
    if errors:
        print(f"\n❌ Found {len(errors)} import error(s):")
        for module, error in errors:
            print(f"   - {module}: {error}")
        print("\nPlease install missing dependencies or fix import paths.")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)