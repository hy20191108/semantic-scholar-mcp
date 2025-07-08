"""Domain models for Semantic Scholar entities."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

from .base_models import BaseEntity, CacheableModel
from core.types import (
    PaperId, AuthorId, CitationCount, Year, Venue, Abstract, Url,
    FieldsOfStudy
)


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
    UNKNOWN = "Unknown"


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


class Author(BaseModel):
    """Author model."""
    
    author_id: Optional[AuthorId] = Field(None, alias="authorId")
    name: str
    aliases: List[str] = Field(default_factory=list)
    affiliations: List[str] = Field(default_factory=list)
    homepage: Optional[Url] = None
    citation_count: Optional[CitationCount] = Field(None, alias="citationCount")
    h_index: Optional[int] = Field(None, alias="hIndex")
    paper_count: Optional[int] = Field(None, alias="paperCount")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate author name is not empty."""
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty")
        return v.strip()


class PublicationVenue(BaseModel):
    """Publication venue model."""
    
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    alternate_names: List[str] = Field(default_factory=list, alias="alternateNames")
    issn: Optional[str] = None
    url: Optional[Url] = None


class TLDR(BaseModel):
    """TL;DR (Too Long; Didn't Read) summary model."""
    
    model: str = Field(description="Model used to generate the summary")
    text: str = Field(description="Generated summary text")
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate TLDR text is not empty."""
        if not v or not v.strip():
            raise ValueError("TLDR text cannot be empty")
        return v.strip()


class OpenAccessPdf(BaseModel):
    """Open access PDF information model."""
    
    url: Optional[str] = None
    status: Optional[str] = None


class Paper(CacheableModel, BaseEntity):
    """Paper model with all fields."""
    
    paper_id: PaperId = Field(alias="paperId")
    title: str
    abstract: Abstract = None
    year: Optional[Year] = None
    venue: Venue = None
    publication_types: List[PublicationType] = Field(
        default_factory=list,
        alias="publicationTypes"
    )
    publication_date: Optional[datetime] = Field(None, alias="publicationDate")
    journal: Optional[Dict[str, Any]] = None
    
    # Authors
    authors: List[Author] = Field(default_factory=list)
    
    # Metrics
    citation_count: CitationCount = Field(0, alias="citationCount")
    reference_count: int = Field(0, alias="referenceCount")
    influential_citation_count: int = Field(0, alias="influentialCitationCount")
    
    # External IDs
    external_ids: Dict[str, str] = Field(default_factory=dict, alias="externalIds")
    
    # URLs
    url: Optional[Url] = None
    s2_url: Optional[Url] = Field(None, alias="s2Url")
    
    # Additional fields
    fields_of_study: FieldsOfStudy = Field(default_factory=list, alias="fieldsOfStudy")
    publication_venue: Optional[PublicationVenue] = Field(None, alias="publicationVenue")
    tldr: Optional[TLDR] = None
    is_open_access: bool = Field(False, alias="isOpenAccess")
    open_access_pdf: Optional[OpenAccessPdf] = Field(None, alias="openAccessPdf")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate paper title is not empty."""
        if not v or not v.strip():
            raise ValueError("Paper title cannot be empty")
        return v.strip()
    
    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        """Validate publication year is reasonable."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1900 or v > current_year + 1:
                raise ValueError(f"Invalid publication year: {v}")
        return v
    
    @model_validator(mode="after")
    def validate_metrics(self) -> "Paper":
        """Validate citation metrics are consistent."""
        if self.influential_citation_count > self.citation_count:
            raise ValueError(
                "Influential citation count cannot exceed total citation count"
            )
        return self
    
    def generate_cache_key(self) -> str:
        """Generate cache key based on paper ID."""
        return f"paper:{self.paper_id}"


class Citation(BaseModel):
    """Citation model."""
    
    paper_id: PaperId = Field(alias="paperId")
    title: str
    year: Optional[Year] = None
    authors: List[Author] = Field(default_factory=list)
    venue: Venue = None
    citation_count: CitationCount = Field(0, alias="citationCount")
    is_influential: bool = Field(False, alias="isInfluential")
    contexts: List[str] = Field(default_factory=list)
    intents: List[str] = Field(default_factory=list)


class Reference(BaseModel):
    """Reference model."""
    
    paper_id: Optional[PaperId] = Field(None, alias="paperId")
    title: str
    year: Optional[Year] = None
    authors: List[Author] = Field(default_factory=list)
    venue: Venue = None
    citation_count: Optional[CitationCount] = Field(None, alias="citationCount")


class SearchFilters(BaseModel):
    """Search filters model."""
    
    year: Optional[Year] = None
    year_range: Optional[tuple[Year, Year]] = Field(None, alias="yearRange")
    publication_types: Optional[List[PublicationType]] = Field(
        None,
        alias="publicationTypes"
    )
    fields_of_study: Optional[FieldsOfStudy] = Field(None, alias="fieldsOfStudy")
    venues: Optional[List[str]] = None
    open_access_only: bool = Field(False, alias="openAccessOnly")
    min_citation_count: Optional[CitationCount] = Field(None, alias="minCitationCount")
    
    @model_validator(mode="after")
    def validate_year_range(self) -> "SearchFilters":
        """Validate year range is valid."""
        if self.year_range:
            start, end = self.year_range
            if start > end:
                raise ValueError("Year range start must be before end")
            current_year = datetime.now().year
            if start < 1900 or end > current_year + 1:
                raise ValueError("Invalid year range")
        return self


class SearchQuery(BaseModel):
    """Search query model."""
    
    query: str
    fields: Optional[List[str]] = None
    filters: Optional[SearchFilters] = None
    offset: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)
    sort: Optional[str] = None
    
    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()