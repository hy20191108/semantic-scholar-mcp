# Semantic Scholar MCP Server User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Common Use Cases](#common-use-cases)
4. [Integration with Claude Desktop](#integration-with-claude-desktop)
5. [Advanced Features](#advanced-features)
6. [Search Syntax](#search-syntax)
7. [Tips and Tricks](#tips-and-tricks)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Getting Started

### What is Semantic Scholar MCP Server?

The Semantic Scholar MCP Server is a bridge that allows AI assistants like Claude to access and search academic papers from the Semantic Scholar database. It provides powerful search capabilities, citation analysis, and author information retrieval.

### Installation

#### Quick Install

```bash
# Using pip
pip install semantic-scholar-mcp

# Using uv (faster)
uv add semantic-scholar-mcp
```

#### Verify Installation

```bash
# Check installation
semantic-scholar-mcp --version

# Test the server
semantic-scholar-mcp test
```

### First Time Setup

1. **Get a Semantic Scholar API Key (Optional)**
   
   While not required, an API key provides higher rate limits:
   - Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
   - Sign up for an account
   - Generate an API key

2. **Configure the Server**
   
   Create a `.env` file:
   ```env
   SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
   LOG_LEVEL=INFO
   CACHE_ENABLED=true
   ```

3. **Test Your Setup**
   
   ```bash
   # Run a test search
   semantic-scholar-mcp search "machine learning"
   ```

## Basic Usage

### With Claude Desktop

Once configured, you can use natural language to interact with Semantic Scholar:

```
You: Can you find recent papers about transformer architectures in NLP?

Claude: I'll search for recent papers about transformer architectures in NLP.

[Searches Semantic Scholar...]

I found several relevant papers. Here are the top results:

1. "Attention Is All You Need" (2017) - Vaswani et al.
   - Citations: 45,832
   - This seminal paper introduced the Transformer architecture...

2. "BERT: Pre-training of Deep Bidirectional Transformers" (2019) - Devlin et al.
   - Citations: 28,451
   - BERT revolutionized NLP by introducing bidirectional pre-training...

Would you like me to get more details about any of these papers?
```

### Command Line Usage

```bash
# Search for papers
semantic-scholar-mcp search "deep learning" --limit 10

# Get paper details
semantic-scholar-mcp paper "10.18653/v1/2020.acl-main.703"

# Get author information
semantic-scholar-mcp author "1741101"

# Get citations for a paper
semantic-scholar-mcp citations "649def34f8be52c8b66281af98ae884c09aef38b"
```

## Common Use Cases

### 1. Literature Review

**Scenario**: You're starting research on a new topic and need to understand the landscape.

```
You: I need to do a literature review on "federated learning in healthcare". Can you help me find the key papers and identify the main research themes?

Claude: I'll help you with a literature review on federated learning in healthcare. Let me search for relevant papers and analyze the research landscape.

[Performs comprehensive search...]

Based on my search, here's a structured literature review:

## Key Papers (by citation count):

1. "Federated Learning: Challenges, Methods, and Future Directions" (2020)
   - Authors: Li et al.
   - Citations: 1,847
   - Overview: Comprehensive survey of federated learning techniques

2. "Privacy-Preserving Deep Learning via Federated Learning in Healthcare" (2021)
   - Authors: Zhang et al.
   - Citations: 892
   - Focus: Privacy techniques specific to medical data

## Main Research Themes:

1. **Privacy and Security**
   - Differential privacy in medical federated learning
   - Secure aggregation protocols
   - HIPAA compliance considerations

2. **Medical Applications**
   - Disease prediction models
   - Medical imaging analysis
   - Electronic health record analysis

3. **Technical Challenges**
   - Non-IID data distribution in hospitals
   - Communication efficiency
   - Model personalization

Would you like me to dive deeper into any of these themes?
```

### 2. Citation Analysis

**Scenario**: You want to understand the impact and influence of a specific paper.

```
You: Can you analyze the citations for the paper "Attention Is All You Need" and tell me about its influence?

Claude: I'll analyze the citations for "Attention Is All You Need" by Vaswani et al.

[Retrieves citation data...]

## Citation Analysis:

**Total Citations**: 45,832 (as of 2024)
**Influential Citations**: 4,281 (9.3%)

## Citation Growth:
- 2017: 12 citations
- 2018: 892 citations
- 2019: 3,421 citations
- 2020: 7,832 citations
- 2021: 11,243 citations
- 2022: 12,891 citations
- 2023: 9,541 citations

## Key Citing Papers:
1. "BERT: Pre-training of Deep Bidirectional Transformers" - Built on transformer architecture
2. "GPT-3: Language Models are Few-Shot Learners" - Scaled up the transformer approach
3. "Vision Transformer (ViT)" - Applied transformers to computer vision

## Research Areas Influenced:
- Natural Language Processing (68%)
- Computer Vision (15%)
- Speech Recognition (8%)
- Multimodal Learning (9%)

The paper fundamentally changed the field by introducing the self-attention mechanism...
```

### 3. Author Profile Analysis

**Scenario**: You want to learn about a researcher's work and contributions.

```
You: Tell me about Yoshua Bengio's research profile and recent work.

Claude: I'll look up Yoshua Bengio's research profile for you.

[Retrieves author information...]

## Yoshua Bengio - Research Profile

**Affiliation**: University of Montreal, Mila
**Total Papers**: 542
**Total Citations**: 289,451
**H-Index**: 128

## Research Areas:
1. Deep Learning (45%)
2. Neural Networks (30%)
3. Machine Learning Theory (15%)
4. AI Safety and Ethics (10%)

## Most Cited Papers:
1. "Gradient-based learning applied to document recognition" (1998)
   - Citations: 35,892
   - Introduced LeNet and popularized CNNs

2. "Learning Deep Architectures for AI" (2009)
   - Citations: 12,451
   - Foundational work on deep learning theory

## Recent Work (2023-2024):
1. "Towards Understanding Mechanistic Interpretability"
2. "GFlowNets: Generative Flow Networks for Discrete Objects"
3. "Consciousness and AI: Theoretical Foundations"

## Collaborators:
- Geoffrey Hinton (32 papers)
- Yann LeCun (28 papers)
- Aaron Courville (45 papers)

Would you like me to explore any specific aspect of his work?
```

### 4. Research Trend Analysis

**Scenario**: You want to understand emerging trends in a field.

```
You: What are the emerging trends in computer vision over the past 2 years?

Claude: I'll analyze recent trends in computer vision research from 2022-2024.

[Analyzes recent papers...]

## Emerging Trends in Computer Vision (2022-2024)

### 1. Vision-Language Models (VLMs)
**Growth**: 312% increase in papers
**Key Papers**:
- "CLIP: Connecting Text and Images" derivatives
- "Flamingo: Visual Language Model"
**Applications**: Zero-shot recognition, image captioning

### 2. Diffusion Models for Vision
**Growth**: 428% increase
**Key Papers**:
- "Stable Diffusion for Image Generation"
- "DiffusionDet: Diffusion Model for Object Detection"
**Applications**: Image generation, editing, restoration

### 3. Neural Radiance Fields (NeRF) Evolution
**Growth**: 156% increase
**Key Innovations**:
- Instant-NGP: Real-time rendering
- NeRF in the Wild: Unconstrained photos
**Applications**: 3D reconstruction, view synthesis

### 4. Self-Supervised Learning
**Key Methods**:
- Masked Autoencoders (MAE)
- Contrastive learning variants
**Impact**: Reduced dependency on labeled data

### 5. Efficient Vision Transformers
**Focus**: Making ViTs practical
- MobileViT for edge devices
- Efficient attention mechanisms
**Trade-off**: Accuracy vs. computational cost

Would you like details on any specific trend?
```

## Integration with Claude Desktop

### Configuration

1. **Locate Configuration File**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/claude/claude_desktop_config.json`

2. **Add MCP Server Configuration**
   ```json
   {
     "mcpServers": {
       "semantic-scholar": {
         "command": "semantic-scholar-mcp",
         "env": {
           "SEMANTIC_SCHOLAR_API_KEY": "your_api_key_here",
           "LOG_LEVEL": "INFO",
           "CACHE_ENABLED": "true"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

### Available Commands in Claude

Once configured, you can use these natural language patterns:

- "Search for papers about [topic]"
- "Find recent papers by [author name]"
- "What papers cite [paper title]?"
- "Get details about DOI: [doi]"
- "Show me influential papers in [field] from [year]"
- "Analyze citations for [paper]"
- "Find papers similar to [paper title]"

### Example Conversations

**Research Planning**:
```
You: I'm starting a PhD in quantum machine learning. Can you help me identify the foundational papers I should read?

Claude: I'll help you identify foundational papers in quantum machine learning. Let me search for the most important works in this field...

[Provides curated list with explanations]
```

**Paper Discovery**:
```
You: I just read "Neural Ordinary Differential Equations". Can you find related work that builds on this?

Claude: I'll search for papers that cite and build upon "Neural Ordinary Differential Equations"...

[Lists related papers with descriptions]
```

## Advanced Features

### 1. Complex Search Queries

The search system supports advanced query syntax:

```
# Boolean operators
"neural networks" AND "medical imaging"
"deep learning" OR "machine learning"
"transformer" NOT "vision"

# Field-specific search
author:"Yann LeCun" 
title:"attention mechanism"
venue:"NeurIPS"
year:2023

# Combining criteria
author:"Hinton" AND year:>2020 AND venue:"ICML"

# Phrase search
"exact phrase search"

# Wildcard search
transform*  # matches transformer, transformation, etc.
```

### 2. Batch Operations

Process multiple papers efficiently:

```python
# In a Python script
from semantic_scholar_mcp import SemanticScholarClient

async def batch_analysis():
    client = SemanticScholarClient()
    
    paper_ids = [
        "10.18653/v1/2020.acl-main.703",
        "10.5555/3295222.3295349",
        "arXiv:2010.11929"
    ]
    
    # Get all papers in one request
    papers = await client.get_papers_batch(paper_ids)
    
    # Analyze
    for paper in papers:
        print(f"{paper.title}: {paper.citation_count} citations")
```

### 3. Citation Network Analysis

Explore citation relationships:

```
You: Can you create a citation network for the top papers in "graph neural networks"?

Claude: I'll create a citation network analysis for top papers in graph neural networks.

[Analyzes citation relationships...]

## Citation Network Structure:

### Hub Papers (Most Cited):
1. "Graph Attention Networks" (2018) - 8,234 citations
   ├── Cited by: "Heterogeneous Graph Transformer"
   ├── Cited by: "Graph Transformer Networks"
   └── Cites: "Graph Convolutional Networks"

2. "Graph Convolutional Networks" (2017) - 12,451 citations
   ├── Foundation for: GAT, GraphSAGE, GIN
   └── Cites: "Spectral Networks and Deep Locally Connected Networks"

### Emerging Clusters:
- **Temporal GNNs**: Papers focusing on dynamic graphs
- **Heterogeneous GNNs**: Multi-type node/edge graphs
- **GNN Explainability**: Interpreting GNN decisions

### Key Research Groups:
- Stanford (Leskovec group): 15 papers
- NYU (LeCun group): 8 papers
- DeepMind: 12 papers
```

### 4. Research Metrics

Calculate various research metrics:

```
You: Calculate research metrics for the field of "reinforcement learning" over the past 5 years.

Claude: I'll calculate comprehensive research metrics for reinforcement learning (2019-2024).

[Analyzes the field...]

## Reinforcement Learning Research Metrics (2019-2024)

### Publication Volume:
- Total Papers: 12,847
- Growth Rate: 34% year-over-year
- Peak Year: 2023 (3,241 papers)

### Citation Impact:
- Average Citations per Paper: 28.4
- Median Citations: 8
- Highly Cited Papers (>100 citations): 423

### Top Venues:
1. NeurIPS: 892 papers (31.2 avg citations)
2. ICML: 743 papers (29.8 avg citations)
3. ICLR: 681 papers (35.2 avg citations)

### Collaboration Patterns:
- Average Authors per Paper: 4.2
- International Collaborations: 42%
- Industry-Academia Collaborations: 38%

### Hot Topics (by paper count growth):
1. Offline RL (+312%)
2. Multi-Agent RL (+248%)
3. Meta-RL (+189%)
4. RL for LLMs (+567%)

### Funding Landscape:
- NSF Funded: 18%
- Industry Funded: 34%
- EU Grants: 12%
```

### 5. Custom Filters and Sorting

Create complex filtered searches:

```python
# Advanced filtering example
filters = {
    "year_range": (2020, 2024),
    "min_citations": 50,
    "fields_of_study": ["Computer Science", "AI"],
    "open_access": True,
    "venues": ["NeurIPS", "ICML", "ICLR"]
}

# Sort options
sort_by = "citations"  # or "year", "relevance"
sort_order = "desc"    # or "asc"
```

## Search Syntax

### Basic Search

```
# Simple keyword search
machine learning

# Phrase search (exact match)
"neural architecture search"

# Multiple terms (implicit AND)
deep learning transformers
```

### Advanced Operators

```
# Boolean operators
deep AND learning
neural OR networks
transformer NOT vision

# Field searches
author:"Geoffrey Hinton"
title:"attention is all you need"
venue:"Nature"
year:2023
doi:"10.1038/s41586-023-06294-z"

# Range queries
year:>2020
year:[2020 TO 2023]
citationCount:>100
```

### Combining Searches

```
# Complex query example
(author:"Yann LeCun" OR author:"Geoffrey Hinton") 
AND year:>2018 
AND (deep learning OR neural networks) 
AND venue:"NeurIPS"
```

### Special Characters

```
# Wildcard (* for multiple characters)
trans*  # matches transformer, translation, etc.

# Escape special characters with backslash
title:"What is \"AI\"?"
```

## Tips and Tricks

### 1. Efficient Literature Reviews

**Start Broad, Then Narrow**:
```
1. Initial search: "federated learning"
2. Refine by year: "federated learning" AND year:>2021
3. Add domain: "federated learning" AND healthcare
4. Focus on methods: "federated learning" AND healthcare AND privacy
```

**Use Citation Chains**:
- Find a seminal paper
- Look at papers that cite it (forward citations)
- Look at papers it cites (backward citations)
- Identify common citations across papers

### 2. Stay Updated

**Create Search Alerts**:
```python
# Save searches for regular updates
saved_searches = [
    {
        "name": "My Research Area",
        "query": "graph neural networks AND molecular",
        "frequency": "weekly"
    },
    {
        "name": "Competitor Watch",
        "query": "author:\"John Doe\" OR author:\"Jane Smith\"",
        "frequency": "monthly"
    }
]
```

**Track Trending Papers**:
```
You: What papers in my field (computer vision) are gaining citations rapidly this month?

Claude: I'll identify rapidly rising papers in computer vision...
```

### 3. Research Planning

**Identify Research Gaps**:
```
You: Based on recent papers in "explainable AI for healthcare", what research gaps exist?

Claude: I'll analyze recent papers to identify research gaps...

[Provides analysis of understudied areas]
```

**Find Collaborators**:
```
You: Who are the active researchers working on "quantum machine learning" that I might collaborate with?

Claude: I'll find active researchers in quantum machine learning...

[Lists researchers with contact info and recent work]
```

### 4. Writing Support

**Literature Review Sections**:
```
You: Help me write a related work section about "vision transformers" for my paper.

Claude: I'll help you create a related work section on vision transformers...

[Provides structured literature review]
```

**Citation Formatting**:
```
You: Format these papers in BibTeX format: [list of papers]

Claude: I'll format these papers in BibTeX...

[Provides formatted citations]
```

## Troubleshooting

### Common Issues

#### 1. No Results Found

**Problem**: Search returns no results
**Solutions**:
- Check spelling and typos
- Use fewer/broader search terms
- Remove quotes from phrase searches
- Try alternative terms or synonyms

#### 2. Too Many Results

**Problem**: Search returns thousands of results
**Solutions**:
- Add more specific terms
- Use filters (year, venue, etc.)
- Use phrase search with quotes
- Add field-specific searches

#### 3. Rate Limit Errors

**Problem**: "Rate limit exceeded" message
**Solutions**:
- Add API key for higher limits
- Enable caching to reduce requests
- Wait for the specified retry time
- Batch requests when possible

#### 4. Connection Errors

**Problem**: Cannot connect to Semantic Scholar
**Solutions**:
- Check internet connection
- Verify API endpoint is accessible
- Check if Semantic Scholar is down
- Try again with increased timeout

### Debug Mode

Enable debug mode for detailed information:

```bash
# Command line
LOG_LEVEL=DEBUG semantic-scholar-mcp search "test"

# In Claude Desktop config
"env": {
  "LOG_LEVEL": "DEBUG"
}
```

### Getting Help

1. **Check Logs**:
   ```bash
   # View recent logs
   tail -f ~/.semantic-scholar-mcp/logs/server.log
   ```

2. **Test Connection**:
   ```bash
   # Test API connectivity
   semantic-scholar-mcp test-connection
   ```

3. **Version Check**:
   ```bash
   # Ensure you have the latest version
   semantic-scholar-mcp --version
   pip install --upgrade semantic-scholar-mcp
   ```

## FAQ

### General Questions

**Q: Do I need an API key?**
A: No, but having one increases rate limits from 100 to 1000 requests per minute.

**Q: How current is the data?**
A: Semantic Scholar updates continuously. New papers appear within days to weeks of publication.

**Q: Can I search for preprints?**
A: Yes, arXiv papers are included and can be searched using arXiv IDs.

**Q: What fields of study are covered?**
A: All academic fields, with particularly strong coverage in:
- Computer Science
- Medicine/Biology
- Physics
- Engineering
- Mathematics

### Technical Questions

**Q: How do I export results?**
A: Results can be exported in various formats:
```bash
# Export to JSON
semantic-scholar-mcp search "AI" --format json > results.json

# Export to CSV
semantic-scholar-mcp search "AI" --format csv > results.csv

# Export to BibTeX
semantic-scholar-mcp search "AI" --format bibtex > results.bib
```

**Q: Can I use this in my own Python scripts?**
A: Yes, you can import and use the client directly:
```python
from semantic_scholar_mcp import SemanticScholarClient

async def my_research():
    async with SemanticScholarClient() as client:
        results = await client.search_papers("my topic")
        return results
```

**Q: How does caching work?**
A: Results are cached locally for 1 hour by default. Cache behavior can be configured:
```env
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
```

**Q: What's the difference between citations and references?**
A: 
- **Citations**: Papers that cite the current paper (forward citations)
- **References**: Papers cited by the current paper (backward citations)

### Usage Questions

**Q: How do I find the most influential papers in a field?**
A: Search with sorting by citations:
```
You: Find the most influential papers in deep learning sorted by citation count

Or use: citationCount:>1000 AND "deep learning"
```

**Q: Can I track my own publications?**
A: Yes, search by your name and/or ORCID:
```
author:"Your Name" OR author:"Your ORCID"
```

**Q: How do I find open access papers only?**
A: Add the open access filter:
```
"machine learning" AND isOpenAccess:true
```

**Q: Can I search in languages other than English?**
A: Yes, but results are primarily in English. Use quotes for non-English terms:
```
"apprentissage automatique"  # French for machine learning
```

### Privacy Questions

**Q: Is my search history stored?**
A: 
- Local caching stores results temporarily
- No personal data is sent to Semantic Scholar
- Search queries are not logged by the MCP server

**Q: Can I use this for commercial research?**
A: Check Semantic Scholar's terms of service. The MCP server itself is open source (MIT license).

## Conclusion

The Semantic Scholar MCP Server provides powerful academic search capabilities directly within Claude and other MCP-compatible applications. Whether you're conducting literature reviews, tracking research trends, or exploring citation networks, this tool streamlines your academic research workflow.

For more information:
- [GitHub Repository](https://github.com/hy20191108/semantic-scholar-mcp)
- [API Documentation](./api-specification.yaml)
- [Developer Guide](./DEVELOPER_GUIDE.md)
- [Report Issues](https://github.com/hy20191108/semantic-scholar-mcp/issues)