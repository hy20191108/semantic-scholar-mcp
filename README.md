# Semantic Scholar MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

An enterprise-grade MCP (Model Context Protocol) server that provides seamless access to the Semantic Scholar academic database. This server enables AI assistants like Claude to search, retrieve, and analyze academic papers with advanced features including caching, rate limiting, and circuit breaker patterns.

## 🚀 Features

- **Comprehensive Paper Search**: Search academic papers with filters for year, fields of study, and sorting options
- **Detailed Paper Information**: Retrieve complete paper details including abstracts, authors, citations, and references
- **Author Search and Profiles**: Find authors and explore their publication history
- **Citation Analysis**: Analyze paper citations and references with pagination support
- **Paper Recommendations**: Get AI-powered paper recommendations based on a given paper
- **Batch Operations**: Retrieve multiple papers in a single request (up to 500)
- **Enterprise Features**:
  - 🔄 Circuit breaker pattern for fault tolerance
  - ⏱️ Exponential backoff retry with jitter
  - 💾 In-memory LRU caching
  - 🚦 Token bucket rate limiting
  - 📊 Structured logging with correlation IDs
  - 🔍 Comprehensive error handling
  - 🏥 Health check endpoints

## 📋 Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Claude Desktop or any MCP-compatible client
- (Optional) Semantic Scholar API key for higher rate limits

## 🛠️ Installation

### Quick Install with Claude Desktop

```bash
claude mcp add semantic-scholar -- uvx semantic-scholar-mcp
```

### Install from PyPI

```bash
# Using pip
pip install semantic-scholar-mcp

# Using uv (recommended)
uv add semantic-scholar-mcp
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/semantic-scholar-mcp.git
cd semantic-scholar-mcp

# Install with uv
uv install

# Or with pip
pip install -e .
```

## ⚙️ Configuration

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### Environment Variables

Create a `.env` file in your project directory (see `.env.example`):

```bash
# Optional: Semantic Scholar API key for higher rate limits
SEMANTIC_SCHOLAR_API_KEY=your-api-key-here

# Logging configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Cache settings
CACHE__ENABLED=true
CACHE__TTL_SECONDS=3600

# Rate limiting
RATE_LIMIT__REQUESTS_PER_SECOND=1.0
RATE_LIMIT__BURST_SIZE=10
```

## 📖 Usage

Once configured, you can use the following commands in Claude Desktop:

### Search for Papers

```
Search for papers on "large language models" published after 2020
```

### Get Paper Details

```
Get details for paper "2020arXiv200308271R" including citations and references
```

### Find Authors

```
Search for authors named "Yoshua Bengio"
```

### Get Paper Recommendations

```
Get recommendations based on paper "2017arXiv170603762V"
```

### Batch Operations

```
Get details for multiple papers: ["paper-id-1", "paper-id-2", "paper-id-3"]
```

## 🔧 API Reference

### Tools

#### `search_papers`
Search for academic papers with advanced filtering options.

**Parameters:**
- `query` (str, required): Search query string
- `limit` (int, optional): Number of results (1-100, default: 10)
- `offset` (int, optional): Pagination offset (default: 0)
- `year` (int, optional): Filter by publication year
- `fields_of_study` (List[str], optional): Filter by fields
- `sort` (str, optional): Sort order (relevance, citationCount, year)

#### `get_paper`
Get detailed information about a specific paper.

**Parameters:**
- `paper_id` (str, required): Paper ID (Semantic Scholar ID, DOI, or ArXiv ID)
- `include_citations` (bool, optional): Include citation details
- `include_references` (bool, optional): Include reference details

#### `get_paper_citations`
Get citations for a specific paper.

**Parameters:**
- `paper_id` (str, required): Paper ID
- `limit` (int, optional): Maximum citations (1-1000, default: 100)
- `offset` (int, optional): Pagination offset

#### `get_paper_references`
Get references for a specific paper.

**Parameters:**
- `paper_id` (str, required): Paper ID
- `limit` (int, optional): Maximum references (1-1000, default: 100)
- `offset` (int, optional): Pagination offset

#### `get_author`
Get detailed information about an author.

**Parameters:**
- `author_id` (str, required): Author ID

#### `get_author_papers`
Get papers by a specific author.

**Parameters:**
- `author_id` (str, required): Author ID
- `limit` (int, optional): Maximum papers (1-1000, default: 100)
- `offset` (int, optional): Pagination offset

#### `search_authors`
Search for authors by name.

**Parameters:**
- `query` (str, required): Author name search query
- `limit` (int, optional): Number of results (1-100, default: 10)
- `offset` (int, optional): Pagination offset

#### `get_recommendations`
Get paper recommendations based on a given paper.

**Parameters:**
- `paper_id` (str, required): Paper ID for recommendations
- `limit` (int, optional): Number of recommendations (1-100, default: 10)

#### `health_check`
Check the health status of the Semantic Scholar MCP server.

**Parameters:**
- None

**Returns:**
- Server health status, API connectivity, cache status, and system information

#### `batch_get_papers`
Get multiple papers in a single request.

**Parameters:**
- `paper_ids` (List[str], required): List of paper IDs (max 500)
- `fields` (List[str], optional): Fields to include in response

### Resources

#### `papers/{paper_id}`
Get paper information as a formatted resource.

#### `authors/{author_id}`
Get author information as a formatted resource.

### Prompts

#### `literature_review`
Generate a literature review prompt for a given topic.

**Parameters:**
- `topic` (str, required): Research topic
- `max_papers` (int, optional): Maximum papers to include (5-50, default: 20)
- `start_year` (int, optional): Starting year for paper search

#### `citation_analysis`
Generate a citation analysis prompt for a paper.

**Parameters:**
- `paper_id` (str, required): Paper ID to analyze
- `depth` (int, optional): Analysis depth (1-3, default: 1)

#### `research_trend_analysis`
Generate a research trend analysis prompt.

**Parameters:**
- `field` (str, required): Research field to analyze
- `years` (int, optional): Years to analyze (1-20, default: 5)

#### `paper_summary`
Generate a paper summary prompt for a specific paper.

**Parameters:**
- `paper_id` (str, required): Paper ID to summarize
- `include_context` (bool, optional): Include citation context (default: true)

## 🏗️ Architecture

The server is built with enterprise-grade patterns:

- **Dependency Injection**: IoC container for loose coupling
- **Repository Pattern**: Abstract data access layer
- **Circuit Breaker**: Fault tolerance for external API calls
- **Caching Layer**: LRU cache with TTL support
- **Structured Logging**: JSON logging with correlation IDs
- **Type Safety**: Comprehensive type hints and Pydantic models
- **Async/Await**: Non-blocking I/O operations throughout

## 🧪 Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/semantic-scholar-mcp.git
cd semantic-scholar-mcp

# Install dependencies with uv
uv install --dev

# Copy environment variables
cp .env.example .env

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

### Running the Server Locally

```bash
# Using MCP inspector
uv run mcp dev src/semantic_scholar_mcp/server.py

# Direct execution
uv run python -m semantic_scholar_mcp
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Semantic Scholar](https://www.semanticscholar.org/) for providing the academic graph API
- [Anthropic](https://www.anthropic.com/) for the MCP specification
- The open-source community for various tools and libraries used in this project

## 📧 Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/yourusername/semantic-scholar-mcp).

---

Built with ❤️ for the academic community