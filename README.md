# Semantic Scholar MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

Access millions of academic papers from Semantic Scholar using the Model Context Protocol (MCP). Works with Claude Code, Claude Desktop, and other MCP-compatible editors.

## Features

✅ **33 comprehensive tools** - Search papers, analyze citations, manage research  
✅ **Smart AI prompts** - Literature reviews and citation analysis  
✅ **Project & memory management** - Organize your research workflow  
✅ **Fast & reliable** - Built-in caching and error recovery  
✅ **Free to use** - No API key required (optional for higher limits)

## Installation

**One command** (recommended):
```bash
claude mcp add semantic-scholar -- uvx semantic-scholar-mcp
```

**Manual setup** (add to MCP settings):
```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": ["semantic-scholar-mcp"]
    }
  }
}
```

**With API key** (for higher rate limits):
```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": ["semantic-scholar-mcp"],
      "env": {
        "SEMANTIC_SCHOLAR_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Get your free API key at: https://www.semanticscholar.org/product/api

## Quick Start

Ask in natural language:

```
"Find recent papers on transformer architectures"
"Show me details for paper DOI 10.1038/nature14539"
"Get recommendations based on the BERT paper"
"Create a literature review on quantum computing"
"Save this review to memory as 'quantum_survey'"
```

## What You Can Do

### 📄 Paper Research
- Search papers with advanced filters (year, citations, fields)
- Get full details: abstracts, authors, citations, references
- Convert PDFs to Markdown for analysis
- Find related papers with AI recommendations

### 👤 Author Analysis
- Search researchers by name or field
- Get author profiles with h-index and metrics
- List all publications by author
- Batch operations for multiple authors

### 🧠 Smart Features
- AI-powered paper recommendations
- Semantic search with SPECTER embeddings
- Citation network analysis
- Research trend identification

### 💾 Research Organization
- Create multiple research projects
- Save literature reviews and notes
- Manage research memories
- Switch between project contexts

### 📊 Datasets
- Access Semantic Scholar datasets
- Download paper/author data
- Get incremental updates

## License

MIT License - see [LICENSE](LICENSE) for details.

> ⚠️ The `get_paper_fulltext` tool uses [PyMuPDF4LLM](https://github.com/pymupdf/PyMuPDF4LLM) (AGPL licensed). Commercial usage may require a commercial PyMuPDF license.

## Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/) for the academic graph API
- [Anthropic](https://www.anthropic.com/) for the MCP specification
- The academic community for making research accessible

---

Built for researchers worldwide 🌍
