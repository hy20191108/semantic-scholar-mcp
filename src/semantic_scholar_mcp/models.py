"""Data models for Semantic Scholar API responses."""


from pydantic import BaseModel, Field


class Author(BaseModel):
    """Author information."""

    author_id: str | None = Field(None, alias="authorId")
    name: str


class Paper(BaseModel):
    """Paper information from Semantic Scholar."""

    paper_id: str = Field(alias="paperId")
    title: str
    abstract: str | None = None
    year: int | None = None
    authors: list[Author] = []
    venue: str | None = None
    citation_count: int = Field(0, alias="citationCount")
    reference_count: int = Field(0, alias="referenceCount")
    url: str | None = None
    arxiv_id: str | None = Field(None, alias="arxivId")
    doi: str | None = None
    fields_of_study: list[str] = Field(default_factory=list, alias="fieldsOfStudy")


class SearchResult(BaseModel):
    """Search results from Semantic Scholar API."""

    total: int
    offset: int
    next: int | None = None
    data: list[Paper]


class AuthorDetails(BaseModel):
    """Detailed author information."""

    author_id: str = Field(alias="authorId")
    name: str
    aliases: list[str] = []
    affiliations: list[str] = []
    homepage: str | None = None
    paper_count: int = Field(0, alias="paperCount")
    citation_count: int = Field(0, alias="citationCount")
    h_index: int | None = Field(None, alias="hIndex")
    papers: list[Paper] = []
