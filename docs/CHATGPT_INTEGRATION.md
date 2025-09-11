# ChatGPT Integration Guide

This guide explains how to integrate the Semantic Scholar MCP server with ChatGPT using Custom GPTs or direct API access.

## Overview

The Semantic Scholar MCP server now includes a REST API wrapper that enables integration with ChatGPT Custom GPTs and other HTTP-based services. This allows you to access millions of academic papers directly from ChatGPT conversations.

## Quick Start

### Method 1: Using the REST API Server

1. **Start the ChatGPT connector server:**
   ```bash
   # Install the package
   pip install semantic-scholar-mcp
   
   # Start the HTTP server
   semantic-scholar-chatgpt
   ```
   
   The server will start on `http://localhost:8000` by default.

2. **Test the API:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/papers/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "machine learning transformers",
       "limit": 5,
       "year": "2020-2023"
     }'
   ```

### Method 2: Creating a ChatGPT Custom GPT

1. **Go to ChatGPT and create a new Custom GPT**
2. **Configure the GPT:**
   - **Name**: Semantic Scholar Research Assistant
   - **Description**: Access millions of academic papers and research insights
   - **Instructions**: Add the instructions from the [GPT Instructions](#gpt-instructions) section below
   - **Actions**: Import the OpenAPI schema from `docs/chatgpt-openapi.json`

3. **Set up the API endpoint:**
   - Use your server URL (e.g., `http://localhost:8000` for local, or your deployed server URL)
   - No authentication required for basic usage

## GPT Instructions

Use these instructions when creating your Custom GPT:

```
You are a research assistant that helps users find and analyze academic papers using the Semantic Scholar database. You have access to millions of research papers and can help with:

1. **Paper Search**: Find papers by keywords, authors, topics, year ranges, and other filters
2. **Paper Details**: Get comprehensive information about specific papers including abstracts, citations, and references  
3. **Citation Analysis**: Explore citation networks and research impact
4. **Author Profiles**: Find researchers and their publications
5. **Research Recommendations**: Get AI-powered paper recommendations
6. **Trend Analysis**: Identify emerging research areas and patterns

## Key Capabilities:

- Search for papers with advanced filtering (year, venue, citation count, open access, etc.)
- Get detailed paper information including abstracts, authors, and metrics
- Find papers that cite or are cited by a specific paper
- Search for authors and explore their publication histories
- Get AI-powered recommendations based on paper content
- Autocomplete search queries for better discovery

## Usage Examples:

**Paper Search:**
- "Find recent papers on transformer architectures in NLP"
- "Search for machine learning papers from 2022-2023 with more than 50 citations"
- "Show me papers about quantum computing published in Nature"

**Author Research:**
- "Find papers by Geoffrey Hinton"
- "Who are the top researchers working on computer vision?"
- "Show me recent publications by authors at Stanford"

**Citation Analysis:**
- "Find papers that cite the original Transformer paper (Attention Is All You Need)"
- "Show me what papers reference BERT"
- "Get citation statistics for paper ID abc123"

**Recommendations:**
- "Recommend papers similar to the GPT-3 paper"
- "Find related work to this computer vision paper"

Always provide clear, well-formatted responses with paper titles, authors, publication years, and brief summaries. Include relevant paper IDs and DOIs when available. Format citations properly and suggest follow-up searches when appropriate.

When users ask for papers, prioritize recent, highly-cited, and relevant results. Explain search strategies and help users refine their queries for better results.
```

## API Endpoints

The REST API provides the following endpoints:

### Paper Operations
- `POST /api/v1/papers/search` - Search for papers
- `GET /api/v1/papers/{paper_id}` - Get paper details  
- `GET /api/v1/papers/{paper_id}/citations` - Get citing papers
- `GET /api/v1/papers/{paper_id}/references` - Get referenced papers

### Author Operations  
- `POST /api/v1/authors/search` - Search for authors
- `GET /api/v1/authors/{author_id}` - Get author details
- `GET /api/v1/authors/{author_id}/papers` - Get author's papers

### Recommendations
- `POST /api/v1/recommendations/paper` - Get paper recommendations

### Utilities
- `GET /api/v1/search/autocomplete` - Get search suggestions
- `GET /health` - Health check

## Configuration Options

### Environment Variables

```bash
# Optional: Semantic Scholar API key for higher rate limits
export SEMANTIC_SCHOLAR_API_KEY="your-api-key-here"

# Server configuration
export CHATGPT_HOST="0.0.0.0"
export CHATGPT_PORT="8000"

# Debug mode
export DEBUG_MCP_MODE="true"
```

### Custom Server Setup

You can customize the server configuration:

```python
from semantic_scholar_mcp.chatgpt_connector import run_chatgpt_connector

# Run with custom settings
run_chatgpt_connector(
    host="0.0.0.0",
    port=8080,
    reload=True  # Enable auto-reload for development
)
```

## Examples

### Example 1: Search for Papers

```bash
curl -X POST "http://localhost:8000/api/v1/papers/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "deep learning computer vision",
    "limit": 10,
    "year": "2020-2023",
    "fields": ["title", "authors", "year", "abstract", "citationCount"],
    "min_citation_count": 50,
    "sort": "citationCount"
  }'
```

### Example 2: Get Paper Details

```bash
curl "http://localhost:8000/api/v1/papers/204e3073870fae3d05bcbc2f6a8e263d9b72e776"
```

### Example 3: Find Author Papers

```bash
curl "http://localhost:8000/api/v1/authors/1741101/papers?limit=20"
```

### Example 4: Get Recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/recommendations/paper" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
    "limit": 10,
    "fields": ["title", "authors", "year", "abstract"]
  }'
```

## Deployment

### Local Development

```bash
# Install dependencies
pip install semantic-scholar-mcp

# Start the server
semantic-scholar-chatgpt

# Or with custom settings
python -m semantic_scholar_mcp.chatgpt_connector
```

### Production Deployment

For production deployment, consider using:

1. **Docker**: Create a Docker container with the server
2. **Cloud Services**: Deploy to AWS, GCP, Azure, or Heroku
3. **Reverse Proxy**: Use nginx or similar for HTTPS and load balancing

Example Docker setup:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install semantic-scholar-mcp

EXPOSE 8000

CMD ["semantic-scholar-chatgpt", "--host", "0.0.0.0", "--port", "8000"]
```

### HTTPS Configuration

For production use with ChatGPT Custom GPTs, you'll need HTTPS. Consider:

1. **Let's Encrypt**: Free SSL certificates
2. **Cloudflare**: CDN with SSL
3. **Cloud Load Balancers**: AWS ALB, GCP Load Balancer, etc.

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port with `--port 8001`
2. **CORS issues**: The server includes CORS headers, but check your setup
3. **Rate limiting**: Get a Semantic Scholar API key for higher limits
4. **Memory usage**: Monitor memory usage for large result sets

### Debug Mode

Enable debug logging:

```bash
export DEBUG_MCP_MODE="true"
export LOG_API_PAYLOADS="true"
semantic-scholar-chatgpt
```

### Health Check

Verify the server is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "semantic-scholar-chatgpt-connector"
}
```

## API Schema

The complete OpenAPI 3.0 schema is available at:
- **File**: `docs/chatgpt-openapi.json`
- **Interactive docs**: `http://localhost:8000/docs` (when server is running)
- **ReDoc**: `http://localhost:8000/redoc` (when server is running)

## Security Considerations

1. **API Keys**: Never expose your Semantic Scholar API key in client-side code
2. **Rate Limiting**: Implement rate limiting for production deployments
3. **CORS**: Configure CORS appropriately for your use case
4. **HTTPS**: Always use HTTPS in production
5. **Input Validation**: The API includes input validation, but monitor for abuse

## Contributing

To contribute to the ChatGPT integration:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

See the main [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

## Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: See the main README and user guide
- **Community**: Join discussions in GitHub Discussions

## License

This integration is part of the Semantic Scholar MCP project and is licensed under the MIT License.