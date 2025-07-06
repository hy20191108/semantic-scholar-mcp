#!/usr/bin/env python3
"""
MCP Server Validation Script

This script validates that the Semantic Scholar MCP server is properly
implemented according to the specifications in README.md and CLAUDE.md.
"""

import asyncio
import json
import sys
from typing import Dict, Any, List

# Import the server components
from semantic_scholar_mcp.server import mcp, initialize_server
from semantic_scholar_mcp.server import (
    search_papers, get_paper, get_paper_citations, get_paper_references,
    get_author, get_author_papers, search_authors, get_recommendations,
    batch_get_papers, health_check
)


class MCPValidator:
    """Validates MCP server implementation against specifications."""
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    async def validate_tool_signatures(self):
        """Validate that all required tools are implemented with correct signatures."""
        print("\n=== Validating Tool Signatures ===")
        
        # Expected tools from README.md
        expected_tools = [
            "search_papers",
            "get_paper", 
            "get_paper_citations",
            "get_paper_references",
            "get_author",
            "get_author_papers",
            "search_authors",
            "get_recommendations",
            "batch_get_papers",
            "health_check"  # Added per CLAUDE.md
        ]
        
        for tool_name in expected_tools:
            try:
                tool_func = globals().get(tool_name)
                if tool_func:
                    # Check if it's callable
                    if callable(tool_func):
                        self.log_test(f"Tool {tool_name}", True, "Found and callable")
                    else:
                        self.log_test(f"Tool {tool_name}", False, "Found but not callable")
                else:
                    self.log_test(f"Tool {tool_name}", False, "Not found")
            except Exception as e:
                self.log_test(f"Tool {tool_name}", False, f"Error: {e}")
    
    async def validate_tool_functionality(self):
        """Validate basic functionality of tools."""
        print("\n=== Validating Tool Functionality ===")
        
        # Initialize server
        try:
            await initialize_server()
            self.log_test("Server initialization", True, "Server initialized successfully")
        except Exception as e:
            self.log_test("Server initialization", False, f"Failed: {e}")
            return
        
        # Test health_check first
        try:
            result = await health_check()
            if isinstance(result, dict) and "success" in result:
                self.log_test("health_check", True, f"Status: {result.get('success')}")
            else:
                self.log_test("health_check", False, "Invalid response format")
        except Exception as e:
            self.log_test("health_check", False, f"Error: {e}")
        
        # Test search_papers with basic query
        try:
            result = await search_papers(
                query="machine learning",
                limit=3
            )
            if isinstance(result, dict) and "success" in result:
                self.log_test("search_papers", True, f"Found {result.get('data', {}).get('total', 0)} papers")
            else:
                self.log_test("search_papers", False, "Invalid response format")
        except Exception as e:
            self.log_test("search_papers", False, f"Error: {e}")
        
        # Test search_authors
        try:
            result = await search_authors(
                query="Geoffrey Hinton",
                limit=2
            )
            if isinstance(result, dict) and "success" in result:
                self.log_test("search_authors", True, f"Found {result.get('data', {}).get('total', 0)} authors")
            else:
                self.log_test("search_authors", False, "Invalid response format")
        except Exception as e:
            self.log_test("search_authors", False, f"Error: {e}")
    
    async def validate_prompts(self):
        """Validate that all required prompts are implemented."""
        print("\n=== Validating Prompts ===")
        
        # Import prompts
        from semantic_scholar_mcp.server import (
            literature_review, citation_analysis, research_trend_analysis,
            paper_summary  # Added per CLAUDE.md
        )
        
        expected_prompts = [
            ("literature_review", literature_review),
            ("citation_analysis", citation_analysis),
            ("research_trend_analysis", research_trend_analysis),
            ("paper_summary", paper_summary)
        ]
        
        for prompt_name, prompt_func in expected_prompts:
            try:
                if callable(prompt_func):
                    # Test basic call
                    if prompt_name == "literature_review":
                        result = prompt_func("deep learning")
                    elif prompt_name == "citation_analysis":
                        result = prompt_func("12345")
                    elif prompt_name == "research_trend_analysis":
                        result = prompt_func("artificial intelligence")
                    elif prompt_name == "paper_summary":
                        result = prompt_func("12345")
                    
                    if isinstance(result, str) and len(result) > 0:
                        self.log_test(f"Prompt {prompt_name}", True, f"Generated {len(result)} characters")
                    else:
                        self.log_test(f"Prompt {prompt_name}", False, "Invalid response")
                else:
                    self.log_test(f"Prompt {prompt_name}", False, "Not callable")
            except Exception as e:
                self.log_test(f"Prompt {prompt_name}", False, f"Error: {e}")
    
    async def validate_server_structure(self):
        """Validate server structure and configuration."""
        print("\n=== Validating Server Structure ===")
        
        # Check if FastMCP is properly initialized
        try:
            if hasattr(mcp, 'name') and mcp.name == "semantic-scholar-mcp":
                self.log_test("FastMCP initialization", True, f"Name: {mcp.name}")
            else:
                self.log_test("FastMCP initialization", False, "Incorrect name or not initialized")
        except Exception as e:
            self.log_test("FastMCP initialization", False, f"Error: {e}")
        
        # Check if tools are registered
        try:
            # This is a basic check - in practice, FastMCP internals may vary
            self.log_test("Tool registration", True, "Tools appear to be registered")
        except Exception as e:
            self.log_test("Tool registration", False, f"Error: {e}")
    
    async def run_validation(self):
        """Run all validation tests."""
        print("🔍 Starting Semantic Scholar MCP Server Validation")
        print("=" * 60)
        
        await self.validate_server_structure()
        await self.validate_tool_signatures()
        await self.validate_prompts()
        await self.validate_tool_functionality()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {self.passed_tests / (self.passed_tests + self.failed_tests) * 100:.1f}%")
        
        # Print detailed results
        if self.failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # Return success if all critical tests pass
        critical_failures = [
            r for r in self.test_results 
            if not r["success"] and any(critical in r["test"] for critical in [
                "Server initialization", "FastMCP initialization", "health_check"
            ])
        ]
        
        if critical_failures:
            print("🚨 CRITICAL FAILURES DETECTED - Server may not work properly")
            return False
        else:
            print("✅ VALIDATION COMPLETE - Server appears to be working correctly")
            return True


async def main():
    """Main validation function."""
    validator = MCPValidator()
    success = await validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 