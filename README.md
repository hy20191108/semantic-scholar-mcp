# Semantic Scholar MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

Access millions of academic papers from Semantic Scholar using the Model Context Protocol (MCP). Works with Claude Code, Claude Desktop, Cursor, VS Code, and other MCP-compatible editors.

## Features

- **Smart Search**: Search papers with filters for year, fields of study, and sorting
- **Full Paper Details**: Get abstracts, authors, citations, and references
- **Author Profiles**: Explore researcher profiles and their publications
- **Citation Network**: Analyze citation relationships and impact
- **AI-Powered**: Get paper recommendations and research insights
- **Fast & Reliable**: Built-in caching, rate limiting, and error recovery

## Installation

### One-Command Setup

**Claude Code** (recommended):
```bash
claude mcp add semantic-scholar -- uvx semantic-scholar-mcp
```


### Manual Configuration (if needed)

Basic setup:
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

With API key for higher limits:
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

## Usage

Ask in natural language:
- *"Find recent papers on transformer architectures in NLP"*
- *"Show me details about paper with DOI 10.1038/nature14539"*
- *"Find papers by Yoshua Bengio from 2020 onwards"*  
- *"Get recommendations based on the BERT paper"*
- *"Create a literature review on quantum computing"*

## Available Tools

### 📄 Paper Tools

| Tool                   | Description                        | Example                                                |
| ---------------------- | ---------------------------------- | ------------------------------------------------------ |
| `search_papers`        | Search papers with filters         | *"Search for deep learning papers from 2023"*          |
| `get_paper`            | Get detailed paper info            | *"Get full details for paper ID abc123"*               |
| `get_paper_citations`  | Get papers citing this paper       | *"Find papers that cite the attention paper"*          |
| `get_paper_references` | Get papers this paper cites        | *"Show references from the BERT paper"*                |
| `get_paper_authors`    | Get detailed author info for paper | *"Show authors of paper abc123"*                       |
| `batch_get_papers`     | Get multiple papers efficiently    | *"Get details for papers: abc123, def456, ghi789"*     |
| `bulk_search_papers`   | Advanced search with filters       | *"Search ML papers from 2020-2023 with 50+ citations"* |
| `search_papers_match`  | Search by exact title match        | *"Find paper with title 'Attention Is All You Need'"*  |

### 👤 Author Tools

| Tool                | Description                      | Example                                     |
| ------------------- | -------------------------------- | ------------------------------------------- |
| `search_authors`    | Search for researchers           | *"Find authors working on computer vision"* |
| `get_author`        | Get author profile               | *"Get profile for author ID 12345"*         |
| `get_author_papers` | List author's publications       | *"Show papers by Geoffrey Hinton"*          |
| `batch_get_authors` | Get multiple authors efficiently | *"Get details for authors: 123, 456, 789"*  |

### 🤖 AI Tools

| Tool                            | Description                      | Example                                                 |
| ------------------------------- | -------------------------------- | ------------------------------------------------------- |
| `get_recommendations_for_paper` | AI-powered paper recommendations | *"Recommend papers similar to GPT-3"*                   |
| `get_recommendations_batch`     | Advanced ML recommendations      | *"Get recommendations from positive/negative examples"* |

### 🔍 Advanced Search Tools

| Tool                 | Description            | Example                                               |
| -------------------- | ---------------------- | ----------------------------------------------------- |
| `autocomplete_query` | Get search suggestions | *"Complete query 'machine lear...'"*                  |
| `search_snippets`    | Search text snippets   | *"Find papers mentioning 'transformer architecture'"* |

### 🧠 Semantic Analysis Tools

| Tool                            | Description                      | Example                               |
| ------------------------------- | -------------------------------- | ------------------------------------- |
| `get_paper_with_embeddings`     | Get paper with vector embeddings | *"Get paper with SPECTER embeddings"* |
| `search_papers_with_embeddings` | Search with semantic vectors     | *"Find semantically similar papers"*  |

### 📊 Dataset Tools

| Tool                              | Description             | Example                                   |
| --------------------------------- | ----------------------- | ----------------------------------------- |
| `get_dataset_releases`            | List available datasets | *"Show available dataset releases"*       |
| `get_dataset_info`                | Get dataset information | *"Get info for dataset release 2023-01"*  |
| `get_dataset_download_links`      | Get download links      | *"Get download links for papers dataset"* |
| `get_incremental_dataset_updates` | Get dataset updates     | *"Get updates between releases"*          |

## Advanced Features

### 📚 Resources (Direct Access)

| Resource              | Description                  | Usage                           |
| --------------------- | ---------------------------- | ------------------------------- |
| `papers/{paper_id}`   | Direct paper data access     | Auto-populated in conversations |
| `authors/{author_id}` | Direct author profile access | Auto-populated in conversations |

### 🎯 AI Prompts (Smart Templates)

| Prompt                    | Description                               | Usage                                              |
| ------------------------- | ----------------------------------------- | -------------------------------------------------- |
| `literature_review`       | Generate comprehensive literature reviews | *"Create a literature review on machine learning"* |
| `citation_analysis`       | Analyze citation networks and impact      | *"Analyze citations for the transformer paper"*    |
| `research_trend_analysis` | Identify emerging research trends         | *"Analyze trends in NLP over the last 5 years"*    |

## Practical Examples

### Search and Explore
```
"Find recent papers on graph neural networks published after 2022"
"Show me the most cited papers in computer vision from 2023"
"Search for papers about attention mechanisms with more than 100 citations"
```

### Deep Analysis
```
"Get full details including citations and references for paper DOI 10.1038/nature14539"
"Show me all papers by Yann LeCun from the last 3 years"
"Find papers that cite 'Attention Is All You Need' and analyze their impact"
```

### AI-Powered Research
```
"Based on the GPT-4 paper, recommend 5 related papers I should read"
"Create a literature review covering the evolution of transformer architectures"
"Analyze citation patterns for deep learning papers in the last decade"
```

## Features

✅ **22 research tools** covering all Semantic Scholar API endpoints  
✅ **Smart AI prompts** for literature reviews and citation analysis  
✅ **Fast & reliable** with built-in caching and error recovery  
✅ **Free to use** - no API key required (optional for higher limits)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/) for the academic graph API
- [Anthropic](https://www.anthropic.com/) for the MCP specification
- The academic community for making research accessible

---

Built for researchers worldwide 🌍