"""Data models for Semantic Scholar API responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author information."""

    author_id: Optional[str] = Field(None, alias="authorId")
    name: str


class Paper(BaseModel):
    """Paper information from Semantic Scholar."""

    paper_id: str = Field(alias="paperId")
    title: str
    abstract: Optional[str] = None
    year: Optional[int] = None
    authors: List[Author] = []
    venue: Optional[str] = None
    citation_count: int = Field(0, alias="citationCount")
    reference_count: int = Field(0, alias="referenceCount")
    url: Optional[str] = None
    arxiv_id: Optional[str] = Field(None, alias="arxivId")
    doi: Optional[str] = None
    fields_of_study: List[str] = Field(default_factory=list, alias="fieldsOfStudy")


class SearchResult(BaseModel):
    """Search results from Semantic Scholar API."""

    total: int
    offset: int
    next: Optional[int] = None
    data: List[Paper]


class AuthorDetails(BaseModel):
    """Detailed author information."""

    author_id: str = Field(alias="authorId")
    name: str
    aliases: List[str] = []
    affiliations: List[str] = []
    homepage: Optional[str] = None
    paper_count: int = Field(0, alias="paperCount")
    citation_count: int = Field(0, alias="citationCount")
    h_index: Optional[int] = Field(None, alias="hIndex")
    papers: List[Paper] = []