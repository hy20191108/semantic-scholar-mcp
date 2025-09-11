"""ChatGPT connector for Semantic Scholar MCP server.

This module provides a REST API wrapper around the MCP tools to enable
integration with ChatGPT Custom GPTs and other HTTP-based services.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from .server import (
    initialize_server,
    search_papers,
    get_paper,
    get_paper_citations,
    get_paper_references,
    get_paper_authors,
    batch_get_papers,
    search_authors,
    get_author,
    get_author_papers,
    batch_get_authors,
    get_recommendations_for_paper,
    get_recommendations_batch,
    bulk_search_papers,
    search_papers_match,
    autocomplete_query,
    search_snippets,
    get_paper_with_embeddings,
    search_papers_with_embeddings,
    get_dataset_releases,
    get_dataset_info,
    get_dataset_download_links,
    get_incremental_dataset_updates,
)


# Pydantic models for request/response validation
class SearchPapersRequest(BaseModel):
    """Request model for search_papers endpoint."""
    query: str = Field(..., description="Search query for papers")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in response")
    year: Optional[str] = Field(default=None, description="Year filter (e.g., '2020', '2020-2023')")
    publication_types: Optional[List[str]] = Field(default=None, description="Publication types to filter")
    fields_of_study: Optional[List[str]] = Field(default=None, description="Fields of study to filter")
    venue: Optional[str] = Field(default=None, description="Venue filter")
    min_citation_count: Optional[int] = Field(default=None, description="Minimum citation count")
    open_access_pdf: Optional[bool] = Field(default=None, description="Filter for open access PDFs")
    sort: Optional[str] = Field(default=None, description="Sort order")


class PaperResponse(BaseModel):
    """Response model for paper data."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None


class AuthorSearchRequest(BaseModel):
    """Request model for author search."""
    query: str = Field(..., description="Author search query")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in response")


class RecommendationsRequest(BaseModel):
    """Request model for paper recommendations."""
    paper_id: str = Field(..., description="Paper ID for recommendations")
    limit: int = Field(default=10, ge=1, le=100, description="Number of recommendations")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in response")


class BatchRecommendationsRequest(BaseModel):
    """Request model for batch recommendations."""
    positive_paper_ids: List[str] = Field(..., description="List of positive example paper IDs")
    negative_paper_ids: Optional[List[str]] = Field(default=None, description="List of negative example paper IDs")
    limit: int = Field(default=10, ge=1, le=500, description="Number of recommendations")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in response")


# Initialize FastAPI app
app = FastAPI(
    title="Semantic Scholar API for ChatGPT",
    description="REST API wrapper for Semantic Scholar MCP server, compatible with ChatGPT Custom GPTs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global initialization flag
_initialized = False


async def ensure_initialized():
    """Ensure the MCP server is initialized."""
    global _initialized
    if not _initialized:
        await initialize_server()
        _initialized = True


@app.on_event("startup")
async def startup_event():
    """Initialize the server on startup."""
    await ensure_initialized()


# Paper endpoints
@app.post("/api/v1/papers/search", response_model=PaperResponse)
async def api_search_papers(request: SearchPapersRequest) -> PaperResponse:
    """Search for academic papers."""
    await ensure_initialized()
    try:
        result = await search_papers(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            fields=request.fields,
            year=request.year,
            publication_types=request.publication_types,
            fields_of_study=request.fields_of_study,
            venue=request.venue,
            min_citation_count=request.min_citation_count,
            open_access_pdf=request.open_access_pdf,
            sort=request.sort,
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/papers/{paper_id}", response_model=PaperResponse)
async def api_get_paper(
    paper_id: str,
    fields: Optional[List[str]] = Query(default=None, description="Fields to include")
) -> PaperResponse:
    """Get detailed information about a specific paper."""
    await ensure_initialized()
    try:
        result = await get_paper(paper_id=paper_id, fields=fields)
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/papers/{paper_id}/citations", response_model=PaperResponse)
async def api_get_paper_citations(
    paper_id: str,
    limit: int = Query(default=10, ge=1, le=1000, description="Number of citations to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    fields: Optional[List[str]] = Query(default=None, description="Fields to include")
) -> PaperResponse:
    """Get papers that cite this paper."""
    await ensure_initialized()
    try:
        result = await get_paper_citations(
            paper_id=paper_id,
            limit=limit,
            offset=offset,
            fields=fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/papers/{paper_id}/references", response_model=PaperResponse)
async def api_get_paper_references(
    paper_id: str,
    limit: int = Query(default=10, ge=1, le=1000, description="Number of references to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    fields: Optional[List[str]] = Query(default=None, description="Fields to include")
) -> PaperResponse:
    """Get papers referenced by this paper."""
    await ensure_initialized()
    try:
        result = await get_paper_references(
            paper_id=paper_id,
            limit=limit,
            offset=offset,
            fields=fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/papers/{paper_id}/authors", response_model=PaperResponse)
async def api_get_paper_authors(paper_id: str) -> PaperResponse:
    """Get detailed author information for a paper."""
    await ensure_initialized()
    try:
        result = await get_paper_authors(paper_id=paper_id)
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Author endpoints
@app.post("/api/v1/authors/search", response_model=PaperResponse)
async def api_search_authors(request: AuthorSearchRequest) -> PaperResponse:
    """Search for authors."""
    await ensure_initialized()
    try:
        result = await search_authors(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            fields=request.fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/authors/{author_id}", response_model=PaperResponse)
async def api_get_author(
    author_id: str,
    fields: Optional[List[str]] = Query(default=None, description="Fields to include")
) -> PaperResponse:
    """Get detailed information about an author."""
    await ensure_initialized()
    try:
        result = await get_author(author_id=author_id, fields=fields)
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/authors/{author_id}/papers", response_model=PaperResponse)
async def api_get_author_papers(
    author_id: str,
    limit: int = Query(default=10, ge=1, le=1000, description="Number of papers to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    fields: Optional[List[str]] = Query(default=None, description="Fields to include")
) -> PaperResponse:
    """Get papers by an author."""
    await ensure_initialized()
    try:
        result = await get_author_papers(
            author_id=author_id,
            limit=limit,
            offset=offset,
            fields=fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Recommendations endpoints
@app.post("/api/v1/recommendations/paper", response_model=PaperResponse)
async def api_get_recommendations_for_paper(request: RecommendationsRequest) -> PaperResponse:
    """Get paper recommendations based on a single paper."""
    await ensure_initialized()
    try:
        result = await get_recommendations_for_paper(
            paper_id=request.paper_id,
            limit=request.limit,
            fields=request.fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/recommendations/batch", response_model=PaperResponse)
async def api_get_recommendations_batch(request: BatchRecommendationsRequest) -> PaperResponse:
    """Get paper recommendations based on multiple positive/negative examples."""
    await ensure_initialized()
    try:
        result = await get_recommendations_batch(
            positive_paper_ids=request.positive_paper_ids,
            negative_paper_ids=request.negative_paper_ids,
            limit=request.limit,
            fields=request.fields
        )
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search utilities
@app.get("/api/v1/search/autocomplete", response_model=PaperResponse)
async def api_autocomplete_query(
    query: str = Query(..., description="Query to autocomplete"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of suggestions")
) -> PaperResponse:
    """Get query autocomplete suggestions."""
    await ensure_initialized()
    try:
        result = await autocomplete_query(query=query, limit=limit)
        return PaperResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "semantic-scholar-chatgpt-connector"}


# Main function to run the HTTP server
def run_chatgpt_connector(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False
):
    """Run the ChatGPT connector HTTP server."""
    uvicorn.run(
        "semantic_scholar_mcp.chatgpt_connector:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_chatgpt_connector()