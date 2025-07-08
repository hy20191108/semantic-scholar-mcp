"""Enhanced domain models with enterprise patterns.

This module provides enhanced models with builder patterns, factory methods,
value objects, and comprehensive validation for the Semantic Scholar domain.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.abstractions import IValidator
from ..core.exceptions import ValidationError
from .base_models import BaseEntity, CacheableModel
from .domain_models import Author as BaseAuthor
from .domain_models import Citation as BaseCitation
from .domain_models import ExternalIdType, PublicationType
from .domain_models import Paper as BasePaper

T = TypeVar("T", bound=BaseModel)


class ValueObject(BaseModel, ABC):
    """Base class for value objects with immutability."""

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )

    @abstractmethod
    def __hash__(self) -> int:
        """Value objects must be hashable."""

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Value objects must be comparable."""


class PaperId(ValueObject):
    """Paper ID value object with validation.
    
    Examples:
        >>> # Create from Semantic Scholar ID
        >>> paper_id = PaperId(value="649def34f8be52c8b66281af98ae884c09aef38b")
        >>> print(paper_id.format())
        'S2:649def34f8be52c8b66281af98ae884c09aef38b'
        
        >>> # Create from DOI
        >>> doi_id = PaperId(value="10.1038/nature12373", id_type=ExternalIdType.DOI)
        >>> print(doi_id.format())
        'DOI:10.1038/nature12373'
        
        >>> # Value objects are immutable and hashable
        >>> paper_set = {paper_id, doi_id}
        >>> len(paper_set)
        2
    """

    value: str
    id_type: ExternalIdType = Field(default=ExternalIdType.CORPUS_ID)

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        """Validate paper ID format."""
        if not v or not v.strip():
            raise ValueError("Paper ID cannot be empty")

        # Remove common prefixes
        v = v.strip()
        for prefix in ["S2:", "DOI:", "ArXiv:", "MAG:", "ACM:", "PMID:", "PMC:"]:
            if v.upper().startswith(prefix.upper()):
                v = v[len(prefix):]

        return v

    def __hash__(self) -> int:
        """Hash based on normalized value and type."""
        return hash((self.value.lower(), self.id_type))

    def __eq__(self, other: object) -> bool:
        """Compare paper IDs."""
        if not isinstance(other, PaperId):
            return False
        return self.value.lower() == other.value.lower() and self.id_type == other.id_type

    def format(self) -> str:
        """Format paper ID with type prefix."""
        if self.id_type == ExternalIdType.CORPUS_ID:
            return f"S2:{self.value}"
        return f"{self.id_type.value}:{self.value}"

    @classmethod
    def from_string(cls, paper_id: str) -> PaperId:
        """Create from string with optional prefix."""
        if ":" in paper_id:
            prefix, value = paper_id.split(":", 1)
            try:
                id_type = ExternalIdType(prefix.upper())
            except ValueError:
                id_type = ExternalIdType.CORPUS_ID
            return cls(value=value, id_type=id_type)
        return cls(value=paper_id)


class AuthorName(ValueObject):
    """Author name value object with normalization.
    
    Examples:
        >>> name = AuthorName(first="John", middle="Q.", last="Doe")
        >>> print(name.full_name)
        'John Q. Doe'
        >>> print(name.normalized)
        'doe, john q'
        
        >>> # Names are comparable
        >>> name1 = AuthorName(first="John", last="Doe")
        >>> name2 = AuthorName(first="john", last="doe")
        >>> name1 == name2
        True
    """

    first: str
    middle: str | None = None
    last: str
    suffix: str | None = None

    @field_validator("first", "last")
    @classmethod
    def validate_required(cls, v: str) -> str:
        """Validate required name parts."""
        if not v or not v.strip():
            raise ValueError("Name part cannot be empty")
        return v.strip()

    @property
    def full_name(self) -> str:
        """Get full name."""
        parts = [self.first]
        if self.middle:
            parts.append(self.middle)
        parts.append(self.last)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)

    @property
    def normalized(self) -> str:
        """Get normalized name for comparison."""
        parts = [self.last.lower()]
        parts.append(self.first.lower())
        if self.middle:
            parts.append(self.middle.lower())
        return ", ".join(parts)

    @property
    def initials(self) -> str:
        """Get initials."""
        initials = [self.first[0].upper()]
        if self.middle:
            initials.append(self.middle[0].upper())
        initials.append(self.last[0].upper())
        return "".join(initials)

    def __hash__(self) -> int:
        """Hash based on normalized name."""
        return hash(self.normalized)

    def __eq__(self, other: object) -> bool:
        """Compare names."""
        if not isinstance(other, AuthorName):
            return False
        return self.normalized == other.normalized

    @classmethod
    def from_string(cls, name: str) -> AuthorName:
        """Parse name from string."""
        # Handle "Last, First Middle" format
        if "," in name:
            last, rest = name.split(",", 1)
            parts = rest.strip().split()
            first = parts[0] if parts else ""
            middle = " ".join(parts[1:]) if len(parts) > 1 else None
        else:
            # Handle "First Middle Last" format
            parts = name.strip().split()
            if len(parts) == 1:
                first = last = parts[0]
                middle = None
            elif len(parts) == 2:
                first, last = parts
                middle = None
            else:
                first = parts[0]
                last = parts[-1]
                middle = " ".join(parts[1:-1])

        return cls(first=first, middle=middle, last=last)


class CitationContext(ValueObject):
    """Citation context value object.
    
    Examples:
        >>> context = CitationContext(
        ...     text="This method improves upon Smith et al. [15] by...",
        ...     section="Methods",
        ...     intent="methodology"
        ... )
        >>> print(context.summary)
        'Cited in Methods section for methodology'
    """

    text: str
    section: str | None = None
    intent: str | None = None
    sentiment: str | None = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate context text."""
        if not v or not v.strip():
            raise ValueError("Citation context cannot be empty")
        return v.strip()

    @property
    def summary(self) -> str:
        """Get context summary."""
        parts = []
        if self.section:
            parts.append(f"Cited in {self.section} section")
        if self.intent:
            parts.append(f"for {self.intent}")
        if self.sentiment:
            parts.append(f"({self.sentiment})")
        return " ".join(parts) if parts else "Citation context available"

    def __hash__(self) -> int:
        """Hash based on text."""
        return hash(self.text.lower()[:100])  # Use first 100 chars

    def __eq__(self, other: object) -> bool:
        """Compare contexts."""
        if not isinstance(other, CitationContext):
            return False
        return self.text.lower() == other.text.lower()


class ModelBuilder(ABC, BaseModel):
    """Abstract builder pattern for complex models."""

    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    @abstractmethod
    def build(self) -> BaseModel:
        """Build the final model."""

    def validate(self) -> ModelBuilder:
        """Validate the builder state."""
        # Trigger Pydantic validation
        self.model_validate(self.model_dump())
        return self


class AuthorBuilder(ModelBuilder):
    """Builder for Author entities.
    
    Examples:
        >>> author = (AuthorBuilder()
        ...     .with_id("12345")
        ...     .with_name("John", "Doe")
        ...     .with_affiliations(["MIT", "Harvard"])
        ...     .with_metrics(h_index=25, citation_count=1500)
        ...     .build())
        >>> print(author.name)
        'John Doe'
    """

    author_id: str | None = None
    name: AuthorName | None = None
    aliases: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    homepage: str | None = None
    citation_count: int | None = None
    h_index: int | None = None
    paper_count: int | None = None

    def with_id(self, author_id: str) -> AuthorBuilder:
        """Set author ID."""
        self.author_id = author_id
        return self

    def with_name(self, first: str, last: str, middle: str | None = None) -> AuthorBuilder:
        """Set author name."""
        self.name = AuthorName(first=first, middle=middle, last=last)
        return self

    def with_name_string(self, name: str) -> AuthorBuilder:
        """Set author name from string."""
        self.name = AuthorName.from_string(name)
        return self

    def with_aliases(self, aliases: list[str]) -> AuthorBuilder:
        """Set author aliases."""
        self.aliases = aliases
        return self

    def add_alias(self, alias: str) -> AuthorBuilder:
        """Add an alias."""
        self.aliases.append(alias)
        return self

    def with_affiliations(self, affiliations: list[str]) -> AuthorBuilder:
        """Set affiliations."""
        self.affiliations = affiliations
        return self

    def add_affiliation(self, affiliation: str) -> AuthorBuilder:
        """Add an affiliation."""
        self.affiliations.append(affiliation)
        return self

    def with_homepage(self, homepage: str) -> AuthorBuilder:
        """Set homepage URL."""
        self.homepage = homepage
        return self

    def with_metrics(
        self,
        citation_count: int | None = None,
        h_index: int | None = None,
        paper_count: int | None = None
    ) -> AuthorBuilder:
        """Set author metrics."""
        if citation_count is not None:
            self.citation_count = citation_count
        if h_index is not None:
            self.h_index = h_index
        if paper_count is not None:
            self.paper_count = paper_count
        return self

    def build(self) -> EnhancedAuthor:
        """Build the author."""
        if not self.name:
            raise ValidationError("Author name is required", field="name")

        return EnhancedAuthor(
            author_id=self.author_id,
            name=self.name.full_name,
            name_parts=self.name,
            aliases=self.aliases,
            affiliations=self.affiliations,
            homepage=self.homepage,
            citation_count=self.citation_count,
            h_index=self.h_index,
            paper_count=self.paper_count
        )


class PaperBuilder(ModelBuilder):
    """Builder for Paper entities.
    
    Examples:
        >>> paper = (PaperBuilder()
        ...     .with_id("12345")
        ...     .with_title("Deep Learning for NLP")
        ...     .with_authors([("John", "Doe"), ("Jane", "Smith")])
        ...     .with_year(2023)
        ...     .with_venue("Nature")
        ...     .with_abstract("This paper presents...")
        ...     .with_metrics(citations=100, references=50)
        ...     .build())
        >>> print(paper.title)
        'Deep Learning for NLP'
    """

    paper_id: PaperId | None = None
    title: str | None = None
    abstract: str | None = None
    year: int | None = None
    venue: str | None = None
    publication_types: list[PublicationType] = Field(default_factory=list)
    publication_date: datetime | None = None
    authors: list[AuthorName] = Field(default_factory=list)
    citation_count: int = 0
    reference_count: int = 0
    influential_citation_count: int = 0
    external_ids: dict[str, str] = Field(default_factory=dict)
    fields_of_study: list[str] = Field(default_factory=list)
    url: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None

    def with_id(self, paper_id: str, id_type: ExternalIdType = ExternalIdType.CORPUS_ID) -> PaperBuilder:
        """Set paper ID."""
        self.paper_id = PaperId(value=paper_id, id_type=id_type)
        return self

    def with_title(self, title: str) -> PaperBuilder:
        """Set paper title."""
        self.title = title
        return self

    def with_abstract(self, abstract: str) -> PaperBuilder:
        """Set abstract."""
        self.abstract = abstract
        return self

    def with_year(self, year: int) -> PaperBuilder:
        """Set publication year."""
        self.year = year
        return self

    def with_venue(self, venue: str) -> PaperBuilder:
        """Set venue."""
        self.venue = venue
        return self

    def with_publication_date(self, date: datetime) -> PaperBuilder:
        """Set publication date."""
        self.publication_date = date
        return self

    def with_publication_types(self, types: list[PublicationType]) -> PaperBuilder:
        """Set publication types."""
        self.publication_types = types
        return self

    def add_publication_type(self, pub_type: PublicationType) -> PaperBuilder:
        """Add a publication type."""
        self.publication_types.append(pub_type)
        return self

    def with_authors(self, authors: list[tuple | AuthorName]) -> PaperBuilder:
        """Set authors from tuples or AuthorName objects."""
        self.authors = []
        for author in authors:
            if isinstance(author, tuple):
                if len(author) == 2:
                    first, last = author
                    self.authors.append(AuthorName(first=first, last=last))
                elif len(author) == 3:
                    first, middle, last = author
                    self.authors.append(AuthorName(first=first, middle=middle, last=last))
            elif isinstance(author, AuthorName):
                self.authors.append(author)
        return self

    def add_author(self, first: str, last: str, middle: str | None = None) -> PaperBuilder:
        """Add an author."""
        self.authors.append(AuthorName(first=first, middle=middle, last=last))
        return self

    def with_metrics(
        self,
        citations: int | None = None,
        references: int | None = None,
        influential_citations: int | None = None
    ) -> PaperBuilder:
        """Set paper metrics."""
        if citations is not None:
            self.citation_count = citations
        if references is not None:
            self.reference_count = references
        if influential_citations is not None:
            self.influential_citation_count = influential_citations
        return self

    def with_external_ids(self, ids: dict[str, str]) -> PaperBuilder:
        """Set external IDs."""
        self.external_ids = ids
        return self

    def add_external_id(self, id_type: str, value: str) -> PaperBuilder:
        """Add an external ID."""
        self.external_ids[id_type] = value
        return self

    def with_fields_of_study(self, fields: list[str]) -> PaperBuilder:
        """Set fields of study."""
        self.fields_of_study = fields
        return self

    def add_field_of_study(self, field: str) -> PaperBuilder:
        """Add a field of study."""
        self.fields_of_study.append(field)
        return self

    def with_doi(self, doi: str) -> PaperBuilder:
        """Set DOI."""
        self.doi = doi
        self.external_ids["DOI"] = doi
        return self

    def with_arxiv_id(self, arxiv_id: str) -> PaperBuilder:
        """Set ArXiv ID."""
        self.arxiv_id = arxiv_id
        self.external_ids["ArXiv"] = arxiv_id
        return self

    def with_url(self, url: str) -> PaperBuilder:
        """Set URL."""
        self.url = url
        return self

    def build(self) -> EnhancedPaper:
        """Build the paper."""
        if not self.paper_id:
            raise ValidationError("Paper ID is required", field="paper_id")
        if not self.title:
            raise ValidationError("Paper title is required", field="title")

        return EnhancedPaper(
            paper_id=self.paper_id.value,
            paper_id_object=self.paper_id,
            title=self.title,
            abstract=self.abstract,
            year=self.year,
            venue=self.venue,
            publication_types=self.publication_types,
            publication_date=self.publication_date,
            authors=[BaseAuthor(name=a.full_name) for a in self.authors],
            author_names=self.authors,
            citation_count=self.citation_count,
            reference_count=self.reference_count,
            influential_citation_count=self.influential_citation_count,
            external_ids=self.external_ids,
            fields_of_study=self.fields_of_study,
            url=self.url,
            doi=self.doi,
            arxiv_id=self.arxiv_id
        )


class EnhancedAuthor(BaseAuthor, CacheableModel, BaseEntity):
    """Enhanced author model with value objects and validation.
    
    Examples:
        >>> author = EnhancedAuthor.create(
        ...     author_id="12345",
        ...     name="John Doe",
        ...     affiliations=["MIT"]
        ... )
        >>> print(author.name_parts.initials)
        'JD'
    """

    name_parts: AuthorName | None = None

    @classmethod
    def create(
        cls,
        author_id: str | None = None,
        name: str = "",
        **kwargs: Any
    ) -> EnhancedAuthor:
        """Factory method to create author."""
        name_parts = AuthorName.from_string(name) if name else None
        return cls(
            author_id=author_id,
            name=name,
            name_parts=name_parts,
            **kwargs
        )

    @classmethod
    def builder(cls) -> AuthorBuilder:
        """Get author builder."""
        return AuthorBuilder()

    def generate_cache_key(self) -> str:
        """Generate cache key based on author ID."""
        if self.author_id:
            return f"author:{self.author_id}"
        return f"author:{hashlib.md5(self.name.encode()).hexdigest()}"

    def validate_invariants(self) -> None:
        """Validate business invariants."""
        if self.h_index and self.citation_count:
            if self.h_index > self.citation_count:
                raise ValidationError(
                    "H-index cannot exceed citation count",
                    field="h_index",
                    value=self.h_index
                )

        if self.paper_count and self.h_index:
            if self.h_index > self.paper_count:
                raise ValidationError(
                    "H-index cannot exceed paper count",
                    field="h_index",
                    value=self.h_index
                )


class EnhancedPaper(BasePaper):
    """Enhanced paper model with value objects and validation.
    
    Examples:
        >>> paper = EnhancedPaper.create(
        ...     paper_id="12345",
        ...     title="Deep Learning",
        ...     year=2023,
        ...     authors=["John Doe", "Jane Smith"]
        ... )
        >>> print(paper.citation_rate)
        0.0
    """

    paper_id_object: PaperId | None = None
    author_names: list[AuthorName] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        paper_id: str,
        title: str,
        authors: list[str | BaseAuthor] | None = None,
        **kwargs: Any
    ) -> EnhancedPaper:
        """Factory method to create paper."""
        paper_id_obj = PaperId.from_string(paper_id)

        # Process authors
        author_objects = []
        author_names = []

        if authors:
            for author in authors:
                if isinstance(author, str):
                    name = AuthorName.from_string(author)
                    author_objects.append(BaseAuthor(name=author))
                    author_names.append(name)
                elif isinstance(author, BaseAuthor):
                    author_objects.append(author)
                    if author.name:
                        author_names.append(AuthorName.from_string(author.name))

        return cls(
            paper_id=paper_id_obj.value,
            paper_id_object=paper_id_obj,
            title=title,
            authors=author_objects,
            author_names=author_names,
            **kwargs
        )

    @classmethod
    def builder(cls) -> PaperBuilder:
        """Get paper builder."""
        return PaperBuilder()

    @property
    def citation_rate(self) -> float:
        """Calculate average citations per year."""
        if not self.year:
            return 0.0

        years_since_publication = datetime.now().year - self.year
        if years_since_publication <= 0:
            return float(self.citation_count)

        return self.citation_count / years_since_publication

    @property
    def influence_ratio(self) -> float:
        """Calculate ratio of influential to total citations."""
        if self.citation_count == 0:
            return 0.0
        return self.influential_citation_count / self.citation_count

    def validate_invariants(self) -> None:
        """Validate business invariants."""
        # Call parent validation
        super().validate_metrics()

        # Additional validations
        if self.publication_date and self.year:
            if self.publication_date.year != self.year:
                raise ValidationError(
                    "Publication date year must match year field",
                    field="publication_date",
                    value=self.publication_date
                )

        # Validate external IDs match
        if self.doi and self.external_ids.get("DOI") != self.doi:
            raise ValidationError(
                "DOI mismatch in external IDs",
                field="doi",
                value=self.doi
            )

        if self.arxiv_id and self.external_ids.get("ArXiv") != self.arxiv_id:
            raise ValidationError(
                "ArXiv ID mismatch in external IDs",
                field="arxiv_id",
                value=self.arxiv_id
            )


class EnhancedCitation(BaseCitation):
    """Enhanced citation model with context.
    
    Examples:
        >>> citation = EnhancedCitation.create(
        ...     paper_id="12345",
        ...     title="Related Work",
        ...     contexts=["This method improves upon..."],
        ...     is_influential=True
        ... )
        >>> print(citation.has_context)
        True
    """

    citation_contexts: list[CitationContext] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        paper_id: str,
        title: str,
        contexts: list[str | CitationContext] | None = None,
        **kwargs: Any
    ) -> EnhancedCitation:
        """Factory method to create citation."""
        citation_contexts = []
        context_strings = []

        if contexts:
            for context in contexts:
                if isinstance(context, str):
                    citation_contexts.append(CitationContext(text=context))
                    context_strings.append(context)
                elif isinstance(context, CitationContext):
                    citation_contexts.append(context)
                    context_strings.append(context.text)

        return cls(
            paper_id=paper_id,
            title=title,
            contexts=context_strings,
            citation_contexts=citation_contexts,
            **kwargs
        )

    @property
    def has_context(self) -> bool:
        """Check if citation has context."""
        return len(self.citation_contexts) > 0

    @property
    def context_summary(self) -> str:
        """Get summary of all contexts."""
        if not self.citation_contexts:
            return "No context available"

        summaries = [ctx.summary for ctx in self.citation_contexts[:3]]
        if len(self.citation_contexts) > 3:
            summaries.append(f"and {len(self.citation_contexts) - 3} more...")

        return "; ".join(summaries)


class ModelFactory:
    """Factory for creating domain models.
    
    Examples:
        >>> factory = ModelFactory()
        >>> paper = factory.create_paper(
        ...     paper_id="12345",
        ...     title="AI Research",
        ...     year=2023
        ... )
        >>> author = factory.create_author_from_string("John Doe")
    """

    @staticmethod
    def create_paper(paper_id: str, title: str, **kwargs: Any) -> EnhancedPaper:
        """Create enhanced paper."""
        return EnhancedPaper.create(paper_id=paper_id, title=title, **kwargs)

    @staticmethod
    def create_author(author_id: str | None, name: str, **kwargs: Any) -> EnhancedAuthor:
        """Create enhanced author."""
        return EnhancedAuthor.create(author_id=author_id, name=name, **kwargs)

    @staticmethod
    def create_author_from_string(name: str) -> EnhancedAuthor:
        """Create author from name string."""
        name_parts = AuthorName.from_string(name)
        return EnhancedAuthor(
            name=name_parts.full_name,
            name_parts=name_parts
        )

    @staticmethod
    def create_citation(paper_id: str, title: str, **kwargs: Any) -> EnhancedCitation:
        """Create enhanced citation."""
        return EnhancedCitation.create(paper_id=paper_id, title=title, **kwargs)

    @staticmethod
    def create_paper_id(value: str, id_type: str | None = None) -> PaperId:
        """Create paper ID value object."""
        if id_type:
            return PaperId(value=value, id_type=ExternalIdType(id_type))
        return PaperId.from_string(value)


class DomainValidator(IValidator[BaseModel]):
    """Validator for domain models."""

    def __init__(self) -> None:
        """Initialize validator."""
        self._rules: list[Callable[[BaseModel], str | None]] = []

    def add_rule(self, rule: Callable[[BaseModel], str | None]) -> None:
        """Add validation rule."""
        self._rules.append(rule)

    def validate(self, data: BaseModel) -> bool:
        """Validate model."""
        errors = self.get_errors(data)
        return len(errors) == 0

    def get_errors(self, data: BaseModel) -> list[str]:
        """Get validation errors."""
        errors = []

        # Run custom rules
        for rule in self._rules:
            error = rule(data)
            if error:
                errors.append(error)

        # Run model's own validation if available
        if hasattr(data, "validate_invariants"):
            try:
                data.validate_invariants()
            except ValidationError as e:
                errors.append(str(e))

        return errors
