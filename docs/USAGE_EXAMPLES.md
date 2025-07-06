# Semantic Scholar MCP - Usage Examples

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Advanced Search](#advanced-search)
3. [Citation Analysis](#citation-analysis)
4. [Author Research](#author-research)
5. [Literature Review Workflow](#literature-review-workflow)
6. [Integration Examples](#integration-examples)

## Basic Usage

### Search for Papers

#### Simple keyword search
```
User: Search for papers about "transformer architecture"

Assistant: I'll search for papers about transformer architecture.

Response:
```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "transformer architecture",
    "limit": 10
  }
}
```

Results:
1. **Attention Is All You Need** (2017) - 98,451 citations
   - Authors: Vaswani, A., Shazeer, N., Parmar, N., et al.
   - Venue: NeurIPS
   - Abstract: The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...

2. **BERT: Pre-training of Deep Bidirectional Transformers** (2018) - 76,234 citations
   - Authors: Devlin, J., Chang, M., Lee, K., Toutanova, K.
   - Venue: NAACL

#### Search with filters
```
User: Find recent papers on transformers in computer vision from 2022-2024
```

```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "transformer computer vision",
    "year_filter": "2022-2024",
    "fields_of_study": ["Computer Science"],
    "sort": "publicationDate",
    "limit": 5
  }
}
```

### Get Specific Paper Details

```
User: Get details about the paper "Attention Is All You Need"
```

```json
{
  "tool": "get_paper",
  "arguments": {
    "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
    "include_citations": true,
    "include_references": true
  }
}
```

## Advanced Search

### Multi-criteria Search

```
User: Find highly cited open access papers on neural machine translation from top conferences
```

```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "neural machine translation",
    "venue_filter": "ACL EMNLP NAACL NeurIPS ICML",
    "open_access_only": true,
    "sort": "citationCount",
    "limit": 20
  }
}
```

### Pagination Example

```
User: Get the next page of results
```

```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "neural machine translation",
    "offset": 20,
    "limit": 20
  }
}
```

## Citation Analysis

### Analyze Paper Impact

```
User: Show me papers that cite "Attention Is All You Need" and analyze their impact
```

```json
[
  {
    "tool": "get_paper_citations",
    "arguments": {
      "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
      "limit": 50
    }
  },
  {
    "tool": "get_paper",
    "arguments": {
      "paper_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776"
    }
  }
]
```

Analysis Output:
- Total citations: 98,451
- Influential citations: 12,456
- Top citing papers by field:
  - Natural Language Processing: 45%
  - Computer Vision: 25%
  - Speech Recognition: 15%
  - Other: 15%

### Reference Analysis

```
User: What papers did BERT build upon?
```

```json
{
  "tool": "get_paper_references",
  "arguments": {
    "paper_id": "df2b0e26d0599ce3e70df8a9da02e51594e0e992",
    "limit": 30
  }
}
```

## Author Research

### Find Author by Name

```
User: Find papers by Yoshua Bengio
```

```json
[
  {
    "tool": "search_authors",
    "arguments": {
      "query": "Yoshua Bengio",
      "limit": 5
    }
  },
  {
    "tool": "get_author_papers",
    "arguments": {
      "author_id": "161269817",
      "sort": "citationCount",
      "limit": 10
    }
  }
]
```

### Author Collaboration Network

```
User: Show me Geoffrey Hinton's most frequent collaborators
```

```json
[
  {
    "tool": "get_author",
    "arguments": {
      "author_id": "563069026"
    }
  },
  {
    "tool": "get_author_papers",
    "arguments": {
      "author_id": "563069026",
      "limit": 50
    }
  }
]
```

## Literature Review Workflow

### Step 1: Initial Search

```
User: I need to do a literature review on "federated learning privacy"
```

```json
{
  "tool": "search_papers",
  "arguments": {
    "query": "federated learning privacy",
    "year_filter": "2019-2024",
    "sort": "citationCount",
    "limit": 30
  }
}
```

### Step 2: Identify Key Papers

```json
{
  "tool": "batch_get_papers",
  "arguments": {
    "paper_ids": [
      "paper_id_1",
      "paper_id_2",
      "paper_id_3",
      "paper_id_4",
      "paper_id_5"
    ]
  }
}
```

### Step 3: Find Related Work

```json
{
  "tool": "get_recommendations",
  "arguments": {
    "paper_id": "key_paper_id",
    "limit": 20
  }
}
```

### Step 4: Generate Literature Review

```
User: Generate a literature review based on these papers
```

Using the literature_review prompt:
```json
{
  "prompt": "literature_review",
  "arguments": {
    "topic": "Federated Learning Privacy Techniques",
    "year_range": "2019-2024",
    "max_papers": 25
  }
}
```

## Integration Examples

### Claude Desktop Workflow

```
# Research Assistant Mode
User: I'm writing a paper on vision transformers. Help me find:
1. Seminal papers in the field
2. Recent developments (2023-2024)
3. Open problems and future directions

Assistant: I'll help you research vision transformers systematically.

[Executes multiple tool calls to gather comprehensive information]

Here's what I found:

**Seminal Papers:**
1. "An Image is Worth 16x16 Words" (ViT) - 25,431 citations
2. "Swin Transformer" - 12,856 citations
3. "DeiT: Data-efficient Image Transformers" - 8,234 citations

**Recent Developments (2023-2024):**
1. "Efficient Vision Transformers via Fine-Grained Manifold Distillation"
2. "Scalable Vision Transformers with Hierarchical Pooling"
3. "Vision Transformer Pruning via Matrix Decomposition"

**Open Problems:**
- Computational efficiency for high-resolution images
- Better inductive biases for small datasets
- Interpretability of attention mechanisms
- Multi-modal transformer architectures
```

### Python Script Integration

```python
import asyncio
from semantic_scholar_mcp import SemanticScholarClient
from semantic_scholar_mcp.models import SearchQuery

async def research_topic(topic: str, year_range: str):
    async with SemanticScholarClient() as client:
        # Initial search
        query = SearchQuery(
            query=topic,
            year_filter=year_range,
            limit=50,
            sort="citationCount"
        )
        results = await client.search_papers(query)
        
        # Get top papers details
        top_paper_ids = [p.paper_id for p in results.items[:10]]
        detailed_papers = await client.batch_get_papers(top_paper_ids)
        
        # Analyze citations
        citation_counts = {}
        for paper in detailed_papers:
            citations = await client.get_paper_citations(
                paper.paper_id, 
                limit=100
            )
            citation_counts[paper.title] = len(citations)
        
        return {
            "total_papers": results.total,
            "top_papers": detailed_papers,
            "citation_analysis": citation_counts
        }

# Run the research
results = asyncio.run(
    research_topic("quantum machine learning", "2020-2024")
)
```

### Jupyter Notebook Workflow

```python
# Cell 1: Setup
from semantic_scholar_mcp import SemanticScholarClient
import pandas as pd
import matplotlib.pyplot as plt

client = SemanticScholarClient()

# Cell 2: Search and collect data
papers = await client.search_papers(
    SearchQuery(query="reinforcement learning robotics", limit=100)
)

# Cell 3: Create DataFrame
df = pd.DataFrame([
    {
        "title": p.title,
        "year": p.year,
        "citations": p.citation_count,
        "venue": p.venue
    }
    for p in papers.items
])

# Cell 4: Visualize trends
df.groupby('year')['citations'].mean().plot(kind='bar')
plt.title('Average Citations by Year')
plt.xlabel('Year')
plt.ylabel('Average Citations')
plt.show()
```

### Research Pipeline Example

```bash
# 1. Search for papers
claude "Search for recent papers on 'graph neural networks' from 2023-2024"

# 2. Get specific paper
claude "Get details about paper ID abc123 including citations"

# 3. Find author's work
claude "Find all papers by the first author of that paper"

# 4. Get recommendations
claude "Get paper recommendations based on that paper"

# 5. Generate summary
claude "Generate a summary of the key findings from these papers"
```

## Best Practices

### 1. Efficient Searching

- Use specific keywords and phrases
- Apply filters to narrow results
- Sort by relevance for broad topics, by date for emerging fields
- Use field-specific terms (e.g., "transformer" vs "attention mechanism")

### 2. Batch Operations

```json
// Good: Single batch request
{
  "tool": "batch_get_papers",
  "arguments": {
    "paper_ids": ["id1", "id2", "id3", "id4", "id5"]
  }
}

// Avoid: Multiple individual requests
[
  {"tool": "get_paper", "arguments": {"paper_id": "id1"}},
  {"tool": "get_paper", "arguments": {"paper_id": "id2"}},
  {"tool": "get_paper", "arguments": {"paper_id": "id3"}}
]
```

### 3. Citation Analysis

- Use influential_citation_count for impact assessment
- Check citation contexts for understanding how papers are cited
- Look at citation velocity (citations per year) for emerging topics

### 4. Author Research

- Search by full name first, then use author ID for precise results
- Check author aliases for complete publication list
- Use h-index and citation count for impact assessment

### 5. Literature Review

- Start with broad search, then narrow down
- Use recommendations to find related work
- Check both citations and references for complete coverage
- Sort by different criteria for different perspectives