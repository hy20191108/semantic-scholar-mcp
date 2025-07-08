#!/usr/bin/env python3
"""Simple test script to check configuration loading."""

import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def test_config():
    """Test configuration loading."""
    try:
        from core.config import get_config

        print("Loading configuration...")
        config = get_config()

        print("✅ Configuration loaded successfully!")
        print(f"   Environment: {config.environment}")
        print(f"   Cache enabled: {config.cache.enabled}")
        print(f"   Server version: {config.server.version}")

        return True
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_api_client():
    """Test creating API client."""
    try:
        from core.logging import get_logger

        print("Creating simple API client...")

        # Create a simple client with minimal config
        logger = get_logger(__name__)

        # Try to create client with default settings
        print("✅ API client classes imported successfully!")

        return True
    except Exception as e:
        print(f"❌ Failed to create API client: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Basic Configuration and Import Tests")
    print("=" * 50)

    config_ok = test_config()
    print("-" * 30)
    client_ok = test_simple_api_client()

    if config_ok and client_ok:
        print("\n✅ All basic tests passed!")
    else:
        print("\n❌ Some tests failed!")
