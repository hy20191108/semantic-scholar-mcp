"""Type definitions and aliases for the Semantic Scholar MCP server."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:
    from pydantic import BaseModel

# Generic type variables
T = TypeVar("T")
TModel = TypeVar("TModel", bound="BaseModel")

# Type aliases for common structures
JSON: TypeAlias = dict[str, Any]
JSONList: TypeAlias = list[JSON]
PaperId: TypeAlias = str
AuthorId: TypeAlias = str
FieldsOfStudy: TypeAlias = list[str]

# Semantic Scholar specific types
CitationCount: TypeAlias = int
Year: TypeAlias = int
Venue: TypeAlias = str | None
Abstract: TypeAlias = str | None
Url: TypeAlias = str

# API response types
SearchResult: TypeAlias = dict[str, int | list[JSON]]
PaperDetails: TypeAlias = JSON
AuthorDetails: TypeAlias = JSON
CitationsList: TypeAlias = JSONList
ReferencesList: TypeAlias = JSONList
RecommendationsList: TypeAlias = JSONList

# Error types
ErrorCode: TypeAlias = str
ErrorMessage: TypeAlias = str
ErrorDetails: TypeAlias = JSON | None

# Configuration types
ApiKey: TypeAlias = str | None
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
Fields: TypeAlias = list[str]
IncludeFields: TypeAlias = Fields | None
ExcludeFields: TypeAlias = Fields | None

# Sort options
SortBy: TypeAlias = str
SortOrderDirection: TypeAlias = str

# Pagination and sorting types

@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 10
    offset: int | None = None
    limit: int | None = None


@dataclass
class SortOrder:
    """Sort order specification."""
    field: str
    direction: str = "asc"  # asc or desc


@dataclass
class SearchQuery:
    """Search query specification."""
    query: str
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None


# Metric names
MetricName: TypeAlias = str

# Common field sets for API requests
BASIC_PAPER_FIELDS: list[str] = [
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

DETAILED_PAPER_FIELDS: list[str] = BASIC_PAPER_FIELDS + [
    "externalIds",
    "url",
    "publicationDate",
    "referenceCount",
    "fieldsOfStudy",
]

AUTHOR_FIELDS: list[str] = [
    "authorId",
    "name",
    "affiliations",
    "paperCount",
]

CITATION_FIELDS: list[str] = [
    "paperId",
    "title",
    "year",
    "authors",
    "venue",
    "citationCount",
    "isInfluential",
]
