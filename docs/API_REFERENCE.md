# Semantic Scholar MCP - API Reference

## Table of Contents

1. [Tools](#tools)
2. [Resources](#resources)
3. [Prompts](#prompts)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Configuration](#configuration)

## Tools

### search_papers

Search for academic papers using various filters and sorting options.

#### Request

```typescript
{
  tool: "search_papers",
  arguments: {
    query: string,              // Required: Search query
    limit?: number,             // Optional: 1-100, default 10
    offset?: number,            // Optional: Pagination offset, default 0
    year_filter?: string,       // Optional: "2023" or "2020-2023"
    venue_filter?: string,      // Optional: Conference/journal name
    fields_of_study?: string[], // Optional: ["Computer Science", "Mathematics"]
    open_access_only?: boolean, // Optional: Filter for OA papers, default false
    sort?: "relevance" | "citationCount" | "paperId" | "publicationDate"
  }
}
```

#### Response

```typescript
{
  success: true,
  data: {
    items: Paper[],  // Array of paper objects
    total: number,   // Total matching papers
    offset: number,  // Current offset
    limit: number,   // Current limit
    has_more: boolean // More results available
  }
}
```

#### Example

```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "transformer neural networks",
    "limit": 5,
    "year_filter": "2020-2024",
    "fields_of_study": ["Computer Science"],
    "sort": "citationCount"
  }
}
```

### get_paper

Retrieve detailed information about a specific paper.

#### Request

```typescript
{
  tool: "get_paper",
  arguments: {
    paper_id: string,           // Required: Semantic Scholar paper ID
    include_citations?: boolean, // Optional: Include citation details
    include_references?: boolean // Optional: Include reference details
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Paper // Complete paper object with requested details
}
```

### get_paper_citations

Get papers that cite a specific paper.

#### Request

```typescript
{
  tool: "get_paper_citations",
  arguments: {
    paper_id: string,  // Required: Paper ID
    limit?: number,    // Optional: 1-100, default 10
    offset?: number    // Optional: Pagination offset
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Citation[] // Array of citation objects
}
```

### get_paper_references

Get papers referenced by a specific paper.

#### Request

```typescript
{
  tool: "get_paper_references",
  arguments: {
    paper_id: string,  // Required: Paper ID
    limit?: number,    // Optional: 1-100, default 10
    offset?: number    // Optional: Pagination offset
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Reference[] // Array of reference objects
}
```

### get_author

Retrieve detailed author information.

#### Request

```typescript
{
  tool: "get_author",
  arguments: {
    author_id: string  // Required: Semantic Scholar author ID
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Author // Complete author object
}
```

### get_author_papers

Get papers written by a specific author.

#### Request

```typescript
{
  tool: "get_author_papers",
  arguments: {
    author_id: string,  // Required: Author ID
    limit?: number,     // Optional: 1-100, default 10
    offset?: number,    // Optional: Pagination offset
    sort?: "citationCount" | "publicationDate"
  }
}
```

#### Response

```typescript
{
  success: true,
  data: {
    items: Paper[],
    total: number,
    offset: number,
    limit: number,
    has_more: boolean
  }
}
```

### search_authors

Search for authors by name.

#### Request

```typescript
{
  tool: "search_authors",
  arguments: {
    query: string,   // Required: Author name query
    limit?: number,  // Optional: 1-50, default 10
    offset?: number  // Optional: Pagination offset
  }
}
```

#### Response

```typescript
{
  success: true,
  data: {
    items: Author[],
    total: number,
    offset: number,
    limit: number,
    has_more: boolean
  }
}
```

### batch_get_papers

Retrieve multiple papers in a single request.

#### Request

```typescript
{
  tool: "batch_get_papers",
  arguments: {
    paper_ids: string[]  // Required: Array of paper IDs (max 100)
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Paper[] // Array of paper objects
}
```

### get_recommendations

Get paper recommendations based on a seed paper.

#### Request

```typescript
{
  tool: "get_recommendations",
  arguments: {
    paper_id: string,  // Required: Seed paper ID
    limit?: number     // Optional: 1-100, default 10
  }
}
```

#### Response

```typescript
{
  success: true,
  data: Paper[] // Array of recommended papers
}
```

### health_check

Check service health and API connectivity.

#### Request

```typescript
{
  tool: "health_check",
  arguments: {}
}
```

#### Response

```typescript
{
  success: true,
  data: {
    status: "healthy" | "degraded" | "unhealthy",
    api_accessible: boolean,
    cache_enabled: boolean,
    rate_limit_remaining: number,
    version: string,
    uptime_seconds: number
  }
}
```

## Resources

Resources provide read-only access to specific entities.

### paper://{paper_id}

Access paper information as a resource.

#### URI Format
```
paper://e88783e2887e6039deb12c0b0b8c9d1d045d1e1a
```

#### Response
```typescript
{
  uri: string,
  name: string,        // Paper title
  mimeType: "application/json",
  size: number,        // JSON size in bytes
  description: string, // Brief paper description
  metadata: {
    authors: string[],
    year: number,
    venue: string,
    citation_count: number
  }
}
```

### author://{author_id}

Access author information as a resource.

#### URI Format
```
author://1234567
```

#### Response
```typescript
{
  uri: string,
  name: string,        // Author name
  mimeType: "application/json",
  size: number,
  description: string, // Author profile summary
  metadata: {
    h_index: number,
    citation_count: number,
    paper_count: number,
    affiliations: string[]
  }
}
```

## Prompts

### literature_review

Generate a comprehensive literature review on a topic.

#### Arguments
- `topic`: The research topic to review
- `year_range`: Optional year range (e.g., "2020-2024")
- `max_papers`: Maximum papers to include (default: 20)

#### Template Variables
- `papers`: List of relevant papers with metadata
- `topic`: The research topic
- `current_date`: Today's date

### paper_summary

Create a concise summary of a paper.

#### Arguments
- `paper_id`: The paper ID to summarize

#### Template Variables
- `paper`: Complete paper object
- `key_points`: Extracted key contributions

### citation_analysis

Analyze citation patterns and impact.

#### Arguments
- `paper_id`: The paper to analyze

#### Template Variables
- `paper`: Paper object
- `citations`: Citation list with contexts
- `metrics`: Citation metrics and trends

## Data Models

### Paper

```typescript
interface Paper {
  paper_id: string;           // Unique identifier
  title: string;              // Paper title
  abstract?: string;          // Paper abstract
  year?: number;              // Publication year
  venue?: string;             // Conference/journal
  authors: Author[];          // Author list
  citation_count: number;     // Total citations
  reference_count: number;    // Total references
  influential_citation_count: number; // Influential citations
  external_ids: {             // External identifiers
    DOI?: string;
    ArXiv?: string;
    PubMed?: string;
    MAG?: string;
  };
  url?: string;               // Paper URL
  fields_of_study: string[];  // Research fields
  is_open_access: boolean;    // Open access status
  created_at: string;         // ISO timestamp
  updated_at?: string;        // ISO timestamp
}
```

### Author

```typescript
interface Author {
  author_id?: string;         // Unique identifier
  name: string;               // Author name
  aliases: string[];          // Alternative names
  affiliations: string[];     // Institutions
  homepage?: string;          // Personal website
  citation_count?: number;    // Total citations
  h_index?: number;           // H-index
  paper_count?: number;       // Total papers
}
```

### Citation

```typescript
interface Citation {
  paper_id: string;           // Citing paper ID
  title: string;              // Paper title
  year?: number;              // Publication year
  authors: Author[];          // Author list
  venue?: string;             // Venue
  citation_count: number;     // Citations of citing paper
  is_influential: boolean;    // Influential citation flag
  contexts: string[];         // Citation contexts
  intents: string[];          // Citation intents
}
```

### Reference

```typescript
interface Reference {
  paper_id: string;           // Referenced paper ID
  title: string;              // Paper title
  year?: number;              // Publication year
  authors: Author[];          // Author list
  venue?: string;             // Venue
  citation_count: number;     // Total citations
}
```

## Error Handling

### Error Response Format

```typescript
{
  success: false,
  error: {
    code: string,           // Error code
    message: string,        // Human-readable message
    details?: any,          // Additional error details
    timestamp: string       // ISO timestamp
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid input parameters | 400 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT_ERROR` | Rate limit exceeded | 429 |
| `API_ERROR` | External API error | 502 |
| `TIMEOUT_ERROR` | Request timeout | 504 |
| `CIRCUIT_OPEN` | Circuit breaker open | 503 |
| `INTERNAL_ERROR` | Internal server error | 500 |

### Rate Limit Headers

When rate limited, the response includes:

```typescript
{
  success: false,
  error: {
    code: "RATE_LIMIT_ERROR",
    message: "Rate limit exceeded",
    details: {
      retry_after: 300,     // Seconds until reset
      limit: 100,           // Request limit
      remaining: 0,         // Remaining requests
      reset: "2024-01-01T00:05:00Z" // Reset time
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SEMANTIC_SCHOLAR_API_KEY` | string | - | API key for authentication |
| `SEMANTIC_SCHOLAR_BASE_URL` | string | `https://api.semanticscholar.org` | API base URL |
| `SEMANTIC_SCHOLAR_TIMEOUT` | float | `30.0` | Request timeout in seconds |
| `CACHE_MAX_SIZE` | int | `1000` | Maximum cache entries |
| `CACHE_TTL` | int | `3600` | Cache TTL in seconds |
| `RATE_LIMIT_REQUESTS` | int | `100` | Requests per window |
| `RATE_LIMIT_WINDOW` | int | `300` | Window size in seconds |
| `CIRCUIT_BREAKER_THRESHOLD` | int | `5` | Failure threshold |
| `CIRCUIT_BREAKER_TIMEOUT` | float | `60.0` | Recovery timeout |
| `LOG_LEVEL` | string | `INFO` | Logging level |
| `ENVIRONMENT` | string | `production` | Environment name |

### Configuration File

Create a `.env` file in the project root:

```bash
# API Configuration
SEMANTIC_SCHOLAR_API_KEY=your-api-key-here
SEMANTIC_SCHOLAR_TIMEOUT=45.0

# Cache Configuration
CACHE_MAX_SIZE=2000
CACHE_TTL=7200

# Resilience Configuration
RATE_LIMIT_REQUESTS=200
CIRCUIT_BREAKER_THRESHOLD=10

# Logging
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Advanced Configuration

For enterprise deployments, use the configuration file:

```json
{
  "semantic_scholar": {
    "base_url": "https://api.semanticscholar.org",
    "api_key": "${SEMANTIC_SCHOLAR_API_KEY}",
    "timeout": 30.0,
    "max_connections": 100,
    "max_keepalive_connections": 20,
    "default_fields": [
      "paperId", "title", "abstract", "year", "authors",
      "venue", "citationCount", "referenceCount", "fieldsOfStudy"
    ]
  },
  "cache": {
    "backend": "memory",
    "max_size": 1000,
    "ttl": 3600,
    "eviction_policy": "lru"
  },
  "rate_limit": {
    "requests_per_window": 100,
    "window_seconds": 300,
    "burst_size": 20
  },
  "circuit_breaker": {
    "failure_threshold": 5,
    "recovery_timeout": 60.0,
    "half_open_requests": 3
  },
  "retry": {
    "max_attempts": 3,
    "initial_delay": 1.0,
    "max_delay": 30.0,
    "exponential_base": 2.0,
    "jitter": true
  }
}
```