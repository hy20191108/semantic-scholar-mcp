"""Unified data models for Semantic Scholar MCP Server.

This module consolidates all data models from the original 4 model files:
- models.py: Basic API models
- domain_models.py: Comprehensive business models
- base_models.py: Base infrastructure models
- models_enhanced.py: Enhanced patterns (simplified)

Provides all necessary models for the 22 MCP tools and 3 prompts while
maintaining simplicity and avoiding over-abstraction.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type variables
T = TypeVar("T")


# =============================================================================
# ENUMS AND CONSTANTS
# =============================================================================


class PublicationType(str, Enum):
    """Publication type enumeration."""

    JOURNAL_ARTICLE = "JournalArticle"
    CONFERENCE = "Conference"
    REVIEW = "Review"
    DATASET = "Dataset"
    BOOK = "Book"
    BOOK_CHAPTER = "BookChapter"
    THESIS = "Thesis"
    EDITORIAL = "Editorial"
    NEWS = "News"
    STUDY = "Study"
    LETTER = "Letter"
    REPOSITORY = "Repository"
    UNKNOWN = "Unknown"

    def __str__(self):
        return self.value


class ExternalIdType(str, Enum):
    """External ID type enumeration."""

    DOI = "DOI"
    ARXIV = "ArXiv"
    MAG = "MAG"
    ACMID = "ACM"
    PUBMED = "PubMed"
    PUBMED_CENTRAL = "PubMedCentral"
    DBLP = "DBLP"
    CORPUS_ID = "CorpusId"


class EmbeddingType(str, Enum):
    """Embedding type for semantic analysis."""

    SPECTER_V1 = "specter_v1"
    SPECTER_V2 = "specter_v2"


# =============================================================================
# CORE DOMAIN MODELS
# =============================================================================


class PublicationVenue(BaseModel):
    """Publication venue information."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str | None = None
    name: str | None = None
    type: str | None = None
    alternate_names: list[str] = Field(default_factory=list, alias="alternateNames")
    issn: str | None = None
    url: str | None = None


class TLDR(BaseModel):
    """TL;DR summary of a paper."""

    text: str
    model: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate TLDR text is not empty."""
        if not v or not v.strip():
            raise ValueError("TLDR text cannot be empty")
        return v.strip()


class OpenAccessPdf(BaseModel):
    """Open access PDF information."""

    url: str | None = None
    status: str | None = None


class PaperEmbedding(BaseModel):
    """Paper embedding for semantic analysis."""

    model: str
    vector: list[float]


class Author(BaseModel):
    """Author information."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    author_id: str | None = Field(None, alias="authorId")
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate author name is not empty."""
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty")
        return v.strip()

    aliases: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    homepage: str | None = None
    paper_count: int = Field(0, alias="paperCount")
    citation_count: int = Field(0, alias="citationCount")
    h_index: int | None = Field(None, alias="hIndex")
    url: str | None = None


class Paper(BaseModel):
    """Unified paper model with all fields."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core identifiers
    paper_id: str = Field(alias="paperId")
    corpus_id: str | None = Field(None, alias="corpusId")

    @field_validator("corpus_id", mode="before")
    @classmethod
    def validate_corpus_id(cls, v):
        """Convert corpus_id to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    # Basic information
    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate paper title is not empty."""
        if not v or not v.strip():
            raise ValueError("Paper title cannot be empty")
        return v.strip()

    abstract: str | None = None
    year: int | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        """Validate publication year is reasonable."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1900 or v > current_year + 1:
                raise ValueError("Invalid publication year")
        return v

    venue: str | None = None

    # Publication details
    publication_types: list[PublicationType] = Field(
        default_factory=list, alias="publicationTypes"
    )
    publication_date: datetime | None = Field(None, alias="publicationDate")
    publication_venue: PublicationVenue | None = Field(None, alias="publicationVenue")
    journal: dict[str, Any] | None = None

    # Authors
    authors: list[Author] = Field(default_factory=list)

    # Metrics
    citation_count: int = Field(0, alias="citationCount")
    reference_count: int = Field(0, alias="referenceCount")
    influential_citation_count: int = Field(0, alias="influentialCitationCount")

    # External identifiers
    external_ids: dict[str, str] = Field(default_factory=dict, alias="externalIds")
    doi: str | None = None
    arxiv_id: str | None = Field(None, alias="arxivId")

    # URLs
    url: str | None = None
    s2_url: str | None = Field(None, alias="s2Url")

    # Additional fields
    fields_of_study: list[str] = Field(default_factory=list, alias="fieldsOfStudy")
    tldr: TLDR | None = None
    is_open_access: bool = Field(False, alias="isOpenAccess")
    open_access_pdf: OpenAccessPdf | None = Field(None, alias="openAccessPdf")

    # Search-specific
    match_score: float | None = Field(None, alias="matchScore")

    # Optional embeddings
    embedding: PaperEmbedding | None = None

    citations: list["Citation"] = Field(default_factory=list)
    references: list["Reference"] = Field(default_factory=list)


class Citation(BaseModel):
    """Citation relationship between papers."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    paper_id: str = Field(alias="paperId")
    corpus_id: str | None = Field(None, alias="corpusId")

    @field_validator("corpus_id", mode="before")
    @classmethod
    def validate_corpus_id(cls, v):
        """Convert corpus_id to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    title: str | None = None
    year: int | None = None
    authors: list[Author] = Field(default_factory=list)
    venue: str | None = None
    citation_count: int = Field(0, alias="citationCount")
    contexts: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)
    is_influential: bool = Field(False, alias="isInfluential")


class Reference(BaseModel):
    """Reference relationship between papers."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    paper_id: str = Field(alias="paperId")
    corpus_id: str | None = Field(None, alias="corpusId")

    @field_validator("corpus_id", mode="before")
    @classmethod
    def validate_corpus_id(cls, v):
        """Convert corpus_id to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v

    title: str | None = None
    year: int | None = None
    authors: list[Author] = Field(default_factory=list)
    venue: str | None = None
    citation_count: int = Field(0, alias="citationCount")
    contexts: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)
    is_influential: bool = Field(False, alias="isInfluential")


# =============================================================================
# SEARCH AND QUERY MODELS
# =============================================================================


class SearchFilters(BaseModel):
    """Search filters for paper queries."""

    year_range: str | None = Field(None, alias="year")
    fields_of_study: list[str] | None = Field(None, alias="fieldsOfStudy")
    publication_types: list[str] | None = Field(None, alias="publicationTypes")
    venue: str | None = None
    min_citation_count: int | None = Field(None, alias="minCitationCount")
    open_access_pdf: bool | None = Field(None, alias="openAccessPdf")


class SearchQuery(BaseModel):
    """Search query with filters and parameters."""

    query: str
    limit: int = 10
    offset: int = 0
    fields: list[str] | None = None
    sort: str | None = None
    filters: SearchFilters | None = None


class SearchResult(BaseModel):
    """Search results container."""

    total: int
    offset: int
    next: int | None = None
    data: list[Paper]


# =============================================================================
# API RESPONSE MODELS
# =============================================================================


class ApiResponse(BaseModel):
    """Base API response model."""

    model_config = ConfigDict(extra="allow")

    success: bool = True
    data: Any = None
    error: str | None = None
    request_id: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response."""

    model_config = ConfigDict(extra="allow")

    total: int
    limit: int
    offset: int
    next_offset: int | None = Field(None, alias="next")
    data: list[T]


# =============================================================================
# DATASET MODELS
# =============================================================================


class DatasetSummary(BaseModel):
    """Dataset summary information."""

    name: str
    description: str | None = None
    version: str | None = None
    release_date: datetime | None = Field(None, alias="releaseDate")
    paper_count: int | None = Field(None, alias="paperCount")
    readme: str | None = Field(None, alias="README")


class DatasetRelease(BaseModel):
    """Dataset release information."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    release_id: str = Field(alias="releaseId")
    release_date: datetime | None = Field(None, alias="releaseDate")
    description: str | None = None
    paper_count: int | None = Field(None, alias="paperCount")
    citation_count: int | None = Field(None, alias="citationCount")
    readme: str | None = Field(None, alias="README")
    datasets: list[DatasetSummary] | None = None


class DatasetDownloadLinks(BaseModel):
    """Dataset download links."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str
    description: str | None = None
    readme: str | None = Field(None, alias="README")
    files: list[str] = Field(default_factory=list)

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: list[str]) -> list[str]:
        """Validate download files are valid URLs."""
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")
        return v


class DatasetDiff(BaseModel):
    """Dataset difference between releases."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    from_release: str = Field(alias="fromRelease")
    to_release: str = Field(alias="toRelease")
    added_papers: int = Field(0, alias="addedPapers")
    updated_papers: int = Field(0, alias="updatedPapers")
    removed_papers: int = Field(0, alias="removedPapers")
    update_files: list[str] = Field(default_factory=list, alias="updateFiles")
    delete_files: list[str] = Field(default_factory=list, alias="deleteFiles")


class IncrementalUpdate(BaseModel):
    """Incremental dataset update."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    dataset: str
    start_release: str = Field(alias="startRelease")
    end_release: str = Field(alias="endRelease")
    diffs: list[DatasetDiff] = Field(default_factory=list)


class DatasetFile(BaseModel):
    """Dataset file information."""

    filename: str
    url: str
    size_bytes: int | None = Field(None, alias="sizeBytes")
    checksum: str | None = None
    format: str | None = None


# =============================================================================
# RECOMMENDATIONS MODELS
# =============================================================================


class PaperInput(BaseModel):
    """Input paper for recommendations."""

    paper_id: str = Field(alias="paperId")


class BasePaper(BaseModel):
    """Base paper for recommendations response."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    paper_id: str = Field(alias="paperId")
    title: str | None = None
    abstract: str | None = None
    year: int | None = None
    authors: list[Author] = Field(default_factory=list)
    venue: str | None = None
    citation_count: int = Field(0, alias="citationCount")


class AuthorInfo(BaseModel):
    """Author info for recommendations."""

    author_id: str = Field(alias="authorId")
    name: str


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


def validate_paper_id(paper_id: str) -> str:
    """Validate paper ID format."""
    if not paper_id or not isinstance(paper_id, str):
        raise ValueError("Paper ID must be a non-empty string")
    return paper_id.strip()


def validate_author_id(author_id: str) -> str:
    """Validate author ID format."""
    if not author_id or not isinstance(author_id, str):
        raise ValueError("Author ID must be a non-empty string")
    return author_id.strip()


# =============================================================================
# CONVENIENCE TYPES
# =============================================================================

# Common response types
PaperList = list[Paper]
AuthorList = list[Author]
CitationList = list[Citation]
ReferenceList = list[Reference]

# API result types
PaperSearchResult = SearchResult
AuthorSearchResult = PaginatedResponse
