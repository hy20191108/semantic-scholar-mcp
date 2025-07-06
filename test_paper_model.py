#!/usr/bin/env python3
"""Quick test for Paper model."""

from semantic_scholar_mcp.domain_models import Paper, Author

# Test minimal paper creation
try:
    paper = Paper(
        paperId="test123",
        title="Test Paper"
    )
    print(f"✓ Created paper: {paper.paper_id}")
    print(f"  Title: {paper.title}")
    print(f"  Citations: {paper.citation_count}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test with authors
try:
    paper2 = Paper(
        paperId="test456",
        title="Test Paper with Authors",
        authors=[
            {"name": "John Doe"},
            {"name": "Jane Smith", "authorId": "123"}
        ],
        citationCount=10,
        year=2024
    )
    print(f"\n✓ Created paper with authors: {paper2.paper_id}")
    print(f"  Authors: {[a.name for a in paper2.authors]}")
    print(f"  Year: {paper2.year}")
    print(f"  Citations: {paper2.citation_count}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()