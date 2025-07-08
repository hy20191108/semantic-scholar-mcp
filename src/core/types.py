"""Type definitions and aliases for the Semantic Scholar MCP server."""

from typing import TypeVar, TypeAlias, Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

# Generic type variables
T = TypeVar("T")
TModel = TypeVar("TModel", bound="BaseModel")

# Type aliases for common structures
JSON: TypeAlias = Dict[str, Any]
JSONList: TypeAlias = List[JSON]
PaperId: TypeAlias = str
AuthorId: TypeAlias = str
FieldsOfStudy: TypeAlias = List[str]

# Semantic Scholar specific types
CitationCount: TypeAlias = int
Year: TypeAlias = int
Venue: TypeAlias = Optional[str]
Abstract: TypeAlias = Optional[str]
Url: TypeAlias = str

# API response types
SearchResult: TypeAlias = Dict[str, Union[int, List[JSON]]]
PaperDetails: TypeAlias = JSON
AuthorDetails: TypeAlias = JSON
CitationsList: TypeAlias = JSONList
ReferencesList: TypeAlias = JSONList
RecommendationsList: TypeAlias = JSONList

# Error types
ErrorCode: TypeAlias = str
ErrorMessage: TypeAlias = str
ErrorDetails: TypeAlias = Optional[JSON]

# Configuration types
ApiKey: TypeAlias = Optional[str]
Timeout: TypeAlias = float
RetryCount: TypeAlias = int
RateLimit: TypeAlias = int

# Cache types
CacheKey: TypeAlias = str
CacheTTL: TypeAlias = int
CacheValue: TypeAlias = Any

# Pagination types
Offset: TypeAlias = int
Limit: TypeAlias = int
Total: TypeAlias = int

# Field selection types
Fields: TypeAlias = List[str]
IncludeFields: TypeAlias = Optional[Fields]
ExcludeFields: TypeAlias = Optional[Fields]

# Sort options
SortBy: TypeAlias = str
SortOrderDirection: TypeAlias = str

# Pagination and sorting types

@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 10
    offset: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class SortOrder:
    """Sort order specification."""
    field: str
    direction: str = "asc"  # asc or desc


@dataclass
class SearchQuery:
    """Search query specification."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    fields: Optional[List[str]] = None


# Metric names
MetricName: TypeAlias = str

# Common field sets for API requests
BASIC_PAPER_FIELDS: List[str] = [
    "paperId",
    "title",
    "abstract",
    "year",
    "authors",
    "venue",
    "publicationTypes",
    "citationCount",
    "influentialCitationCount",
]

DETAILED_PAPER_FIELDS: List[str] = BASIC_PAPER_FIELDS + [
    "externalIds",
    "url",
    "publicationDate",
    "referenceCount",
    "fieldsOfStudy",
]

AUTHOR_FIELDS: List[str] = [
    "authorId",
    "name",
    "affiliations",
    "paperCount",
]

CITATION_FIELDS: List[str] = [
    "paperId",
    "title",
    "year",
    "authors",
    "venue",
    "citationCount",
    "isInfluential",
]