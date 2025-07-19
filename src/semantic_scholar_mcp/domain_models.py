"""Domain models for Semantic Scholar entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.types import (
    Abstract,
    AuthorId,
    CitationCount,
    FieldsOfStudy,
    PaperId,
    Url,
    Venue,
    Year,
)

from .base_models import BaseEntity, CacheableModel


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
    """Paper embedding type enumeration."""

    SPECTER_V1 = "specter_v1"
    SPECTER_V2 = "specter_v2"


class PublicationVenue(BaseModel):
    """Publication venue model."""

    model_config = ConfigDict(populate_by_name=True)
    id: str | None = None
    name: str | None = None
    type: str | None = None
    alternate_names: list[str] = Field(default_factory=list, alias="alternateNames")
    issn: str | None = None
    url: Url | None = None


class PaperEmbedding(BaseModel):
    """Paper embedding vector."""

    model_config = ConfigDict(populate_by_name=True)

    model: EmbeddingType
    vector: list[float]


class Author(BaseModel):
    """Author model."""

    author_id: AuthorId | None = Field(None, alias="authorId")
    name: str
    aliases: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    homepage: Url | None = None
    citation_count: CitationCount | None = Field(None, alias="citationCount")
    h_index: int | None = Field(None, alias="hIndex")
    paper_count: int | None = Field(None, alias="paperCount")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate author name is not empty."""
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty")
        return v.strip()


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

    url: str | None = None
    status: str | None = None


class Paper(CacheableModel, BaseEntity):
    """Paper model with all fields."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        extra="allow",
        populate_by_name=True,
    )

    paper_id: PaperId = Field(alias="paperId")
    title: str
    abstract: Abstract = None
    year: Year | None = None
    venue: Venue = None
    publication_types: list[PublicationType] = Field(
        default_factory=list, alias="publicationTypes"
    )
    publication_date: datetime | None = Field(None, alias="publicationDate")
    journal: dict[str, Any] | None = None

    # Authors
    authors: list[Author] = Field(default_factory=list)

    # Metrics
    citation_count: CitationCount = Field(0, alias="citationCount")
    reference_count: int = Field(0, alias="referenceCount")
    influential_citation_count: int = Field(0, alias="influentialCitationCount")

    # External IDs
    external_ids: dict[str, str] = Field(default_factory=dict, alias="externalIds")
    corpus_id: str | None = Field(
        None, alias="corpusId", description="Semantic Scholar corpus identifier"
    )

    # URLs
    url: Url | None = None
    s2_url: Url | None = Field(None, alias="s2Url")

    # Additional fields
    fields_of_study: FieldsOfStudy = Field(default_factory=list, alias="fieldsOfStudy")
    publication_venue: PublicationVenue | None = Field(None, alias="publicationVenue")
    tldr: TLDR | None = None
    is_open_access: bool = Field(False, alias="isOpenAccess")
    open_access_pdf: OpenAccessPdf | None = Field(None, alias="openAccessPdf")

    # Citations and references (optional for enhanced get_paper functionality)
    citations: list["Citation"] = Field(default_factory=list)
    references: list["Reference"] = Field(default_factory=list)

    # Embeddings (API spec support)
    embedding: PaperEmbedding | None = None

    # Match score for search results
    match_score: float | None = Field(None, alias="matchScore")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate paper title is not empty."""
        if not v or not v.strip():
            raise ValueError("Paper title cannot be empty")
        return v.strip()

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int | None) -> int | None:
        """Validate publication year is reasonable."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1900 or v > current_year + 1:
                raise ValueError(f"Invalid publication year: {v}")
        return v

    @field_validator("corpus_id", mode="before")
    @classmethod
    def validate_corpus_id(cls, v: Any) -> str | None:
        """Validate corpus ID format."""
        if v is None:
            return None
        # Convert to string if integer
        return str(v) if isinstance(v, int) else v

    @field_validator("external_ids", mode="before")
    @classmethod
    def validate_external_ids(cls, v: Any) -> dict[str, str]:
        """Validate and convert external IDs to strings."""
        if not isinstance(v, dict):
            return {}

        # Convert all values to strings, handling integers
        result = {}
        for key, value in v.items():
            if value is not None:
                result[key] = str(value)
        return result

    @field_validator("publication_types", mode="before")
    @classmethod
    def validate_publication_types(cls, v: Any) -> list[PublicationType]:
        """Validate publication types, converting None to empty list."""
        if v is None:
            return []
        if not isinstance(v, list):
            return []

        # Convert strings to PublicationType enum values
        result = []
        for item in v:
            if isinstance(item, str):
                try:
                    # Try to match the enum value
                    for pub_type in PublicationType:
                        if pub_type.value == item:
                            result.append(pub_type)
                            break
                    else:
                        # If no match found, use UNKNOWN
                        result.append(PublicationType.UNKNOWN)
                except (ValueError, AttributeError):
                    result.append(PublicationType.UNKNOWN)
            elif isinstance(item, PublicationType):
                result.append(item)

        return result

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

    paper_id: PaperId | None = Field(None, alias="paperId")
    title: str | None = None
    year: Year | None = None
    authors: list[Author] = Field(default_factory=list)
    venue: Venue = None
    citation_count: CitationCount = Field(0, alias="citationCount")
    is_influential: bool = Field(False, alias="isInfluential")
    contexts: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)


class Reference(BaseModel):
    """Reference model."""

    paper_id: PaperId | None = Field(None, alias="paperId")
    title: str | None = None
    year: Year | None = None
    authors: list[Author] = Field(default_factory=list)
    venue: Venue = None
    citation_count: CitationCount | None = Field(None, alias="citationCount")


class SearchFilters(BaseModel):
    """Search filters model."""

    year: Year | None = None
    year_range: tuple[Year, Year] | None = Field(None, alias="yearRange")
    publication_types: list[PublicationType] | None = Field(
        None, alias="publicationTypes"
    )
    fields_of_study: FieldsOfStudy | None = Field(None, alias="fieldsOfStudy")
    venues: list[str] | None = None
    open_access_only: bool = Field(False, alias="openAccessOnly")
    min_citation_count: CitationCount | None = Field(None, alias="minCitationCount")

    # New API spec fields
    publication_date_or_year: str | None = Field(None, alias="publicationDateOrYear")
    min_influential_citation_count: int | None = Field(
        None, alias="minInfluentialCitationCount"
    )
    venue_id: str | None = Field(None, alias="venueId")
    field_of_study_id: str | None = Field(None, alias="fieldOfStudyId")

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
    fields: list[str] | None = None
    filters: SearchFilters | None = None
    offset: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)
    sort: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate search query is not empty."""
        if not v or not v.strip():
            raise ValueError("Search query cannot be empty")
        return v.strip()


class SearchResult(BaseModel):
    """Search result model."""

    items: list[Paper] = Field(default_factory=list)
    total: int = Field(0, ge=0)
    offset: int = Field(0, ge=0)
    has_more: bool = Field(False)


class DatasetSummary(BaseModel):
    """Dataset summary model from API spec."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Dataset name")
    description: str = Field(description="Description of the data in the dataset")
    readme: str = Field(
        description="Documentation and attribution for the dataset", alias="README"
    )


class DatasetRelease(BaseModel):
    """Dataset release model from API spec."""

    model_config = ConfigDict(populate_by_name=True)

    release_id: str = Field(description="Release identifier", alias="releaseId")
    readme: str = Field(description="License and usage", alias="README")
    datasets: list[DatasetSummary] = Field(
        default_factory=list, description="Dataset metadata"
    )


class DatasetDownloadLinks(BaseModel):
    """Dataset download links model from API spec."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Name of the dataset")
    description: str = Field(
        description="Description of the data contained in this dataset"
    )
    readme: str = Field(description="License and usage", alias="README")
    files: list[str] = Field(
        default_factory=list,
        description="Temporary, pre-signed download links for dataset files",
    )


class DatasetDiff(BaseModel):
    """Dataset diff model from API spec."""

    model_config = ConfigDict(populate_by_name=True)

    from_release: str = Field(
        description="Baseline release for this diff", alias="fromRelease"
    )
    to_release: str = Field(
        description="Target release for this diff", alias="toRelease"
    )
    update_files: list[str] = Field(
        default_factory=list,
        description="List of files that contain updates",
        alias="updateFiles",
    )
    delete_files: list[str] = Field(
        default_factory=list,
        description="List of files that contain deletes",
        alias="deleteFiles",
    )


class IncrementalUpdate(BaseModel):
    """Incremental update model from API spec."""

    model_config = ConfigDict(populate_by_name=True)

    dataset: str = Field(description="Dataset these diffs are for")
    start_release: str = Field(description="Beginning release", alias="startRelease")
    end_release: str = Field(description="Ending release", alias="endRelease")
    diffs: list[DatasetDiff] = Field(
        default_factory=list, description="List of diffs to apply"
    )


class DatasetFile(BaseModel):
    """Dataset file model."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="File name")
    url: str = Field(description="Download URL")
    size: int | None = Field(None, description="File size in bytes")
    checksum: str | None = Field(None, description="File checksum")
