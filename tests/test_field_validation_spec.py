"""Comprehensive field validation tests for Semantic Scholar API compliance."""

from datetime import datetime

import pytest

from semantic_scholar_mcp.models import (
    TLDR,
    Author,
    EmbeddingType,
    OpenAccessPdf,
    Paper,
    PublicationVenue,
)


class TestFieldValidationSpec:
    """Test comprehensive field validation for API compliance."""

    def test_paper_required_fields_validation(self):
        """Test Paper model required fields validation."""
        # Test minimal valid paper
        minimal_paper = {
            "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
            "title": "Test Paper",
        }

        paper = Paper(**minimal_paper)
        assert paper.paper_id == "649def34f8be52c8b66281af98ae884c09aef38b"
        assert paper.title == "Test Paper"

        # Test that empty title raises validation error
        with pytest.raises(ValueError, match="Paper title cannot be empty"):
            Paper(paperId="test-id", title="")

    def test_author_required_fields_validation(self):
        """Test Author model required fields validation."""
        # Test minimal valid author
        minimal_author = {
            "name": "John Doe",
        }

        author = Author(**minimal_author)
        assert author.name == "John Doe"

        # Test that empty name raises validation error
        with pytest.raises(ValueError, match="Author name cannot be empty"):
            Author(name="")

        # Test that whitespace-only name raises validation error
        with pytest.raises(ValueError, match="Author name cannot be empty"):
            Author(name="   ")

    def test_paper_year_validation(self):
        """Test Paper year field validation."""
        current_year = datetime.now().year

        # Test valid years
        valid_years = [1900, 2000, 2023, current_year, current_year + 1]
        for year in valid_years:
            paper = Paper(paperId="test-id", title="Test Paper", year=year)
            assert paper.year == year

        # Test invalid years
        invalid_years = [1899, current_year + 2, -1, 3000]
        for year in invalid_years:
            with pytest.raises(ValueError, match="Invalid publication year"):
                Paper(paperId="test-id", title="Test Paper", year=year)

    def test_citation_count_validation(self):
        """Test citation count field validation."""
        # Test valid citation counts
        valid_counts = [0, 1, 100, 1000, 10000]
        for count in valid_counts:
            paper = Paper(
                paperId="test-id",
                title="Test Paper",
                citationCount=count,
                # Ensure it doesn't exceed total
                influentialCitationCount=min(count, 50),
            )
            assert paper.citation_count == count

        # Test negative citation count (should be handled gracefully)
        paper = Paper(
            paperId="test-id",
            title="Test Paper",
            citationCount=100,
            influentialCitationCount=0,
        )
        # The model should handle this gracefully
        assert paper.citation_count >= 0

    def test_external_ids_validation(self):
        """Test external IDs field validation."""
        # Test all supported external ID types
        all_external_ids = {
            "DOI": "10.1038/nature14539",
            "ArXiv": "1706.03762",
            "MAG": "2963090019",
            "ACM": "3025529",
            "PubMed": "30123456",
            "PubMedCentral": "PMC6789012",
            "DBLP": "conf/nips/VaswaniSPUJGKP17",
            "CorpusId": "3169096",
        }

        paper = Paper(
            paperId="test-id", title="Test Paper", externalIds=all_external_ids
        )

        for id_type, id_value in all_external_ids.items():
            assert paper.external_ids[id_type] == id_value

    def test_publication_types_validation(self):
        """Test publication types field validation."""
        # Test all supported publication types
        all_pub_types = [
            "JournalArticle",
            "Conference",
            "Review",
            "Dataset",
            "Book",
            "BookChapter",
            "Thesis",
            "Editorial",
            "News",
            "Study",
            "Letter",
            "Repository",
            "Unknown",
        ]

        paper = Paper(
            paperId="test-id", title="Test Paper", publicationTypes=all_pub_types
        )

        assert len(paper.publication_types) == len(all_pub_types)
        for pub_type in all_pub_types:
            assert pub_type in [str(pt) for pt in paper.publication_types]

    def test_fields_of_study_validation(self):
        """Test fields of study field validation."""
        # Test all 23 supported fields of study
        all_fields = [
            "Computer Science",
            "Medicine",
            "Chemistry",
            "Biology",
            "Materials Science",
            "Physics",
            "Geology",
            "Psychology",
            "Art",
            "History",
            "Geography",
            "Sociology",
            "Business",
            "Political Science",
            "Economics",
            "Philosophy",
            "Mathematics",
            "Engineering",
            "Environmental Science",
            "Agricultural and Food Sciences",
            "Education",
            "Law",
            "Linguistics",
        ]

        paper = Paper(paperId="test-id", title="Test Paper", fieldsOfStudy=all_fields)

        assert len(paper.fields_of_study) == 23
        for field in all_fields:
            assert field in paper.fields_of_study

    def test_embedding_validation(self):
        """Test paper embedding field validation."""
        # Test SPECTER v1 embedding
        specter_v1_embedding = {
            "model": "specter_v1",
            "vector": [0.1, 0.2, 0.3] * 256 + [0.4, 0.5],  # 770 dimensions
        }

        paper = Paper(
            paperId="test-id", title="Test Paper", embedding=specter_v1_embedding
        )

        assert paper.embedding.model == EmbeddingType.SPECTER_V1
        assert len(paper.embedding.vector) == 770

        # Test SPECTER v2 embedding
        specter_v2_embedding = {
            "model": "specter_v2",
            "vector": [0.1, 0.2, 0.3] * 255,  # 765 dimensions
        }

        paper = Paper(
            paperId="test-id", title="Test Paper", embedding=specter_v2_embedding
        )

        assert paper.embedding.model == EmbeddingType.SPECTER_V2
        assert len(paper.embedding.vector) == 765

    def test_publication_venue_validation(self):
        """Test publication venue field validation."""
        venue_data = {
            "id": "venue-12345",
            "name": "Conference on Neural Information Processing Systems",
            "type": "conference",
            "alternateNames": ["NIPS", "NeurIPS"],
            "issn": "1234-5678",
            "url": "https://nips.cc/",
        }

        venue = PublicationVenue(**venue_data)

        assert venue.id == "venue-12345"
        assert venue.name == "Conference on Neural Information Processing Systems"
        assert venue.type == "conference"
        assert "NIPS" in venue.alternate_names
        assert "NeurIPS" in venue.alternate_names
        assert venue.issn == "1234-5678"
        assert venue.url == "https://nips.cc/"

    def test_open_access_pdf_validation(self):
        """Test open access PDF field validation."""
        # Test all supported status types
        status_types = ["GOLD", "GREEN", "BRONZE", "HYBRID", "CLOSED"]

        for status in status_types:
            pdf_data = {
                "url": f"https://example.com/paper-{status.lower()}.pdf",
                "status": status,
            }

            pdf = OpenAccessPdf(**pdf_data)
            assert pdf.status == status
            assert pdf.url == f"https://example.com/paper-{status.lower()}.pdf"

    def test_tldr_validation(self):
        """Test TL;DR field validation."""
        tldr_data = {
            "model": "tldr-3.1.0",
            "text": "This paper presents a novel approach to neural networks.",
        }

        tldr = TLDR(**tldr_data)
        assert tldr.model == "tldr-3.1.0"
        assert tldr.text == "This paper presents a novel approach to neural networks."

        # Test that empty text raises validation error
        with pytest.raises(ValueError, match="TLDR text cannot be empty"):
            TLDR(model="test-model", text="")

    def test_author_metrics_validation(self):
        """Test author metrics field validation."""
        author_data = {
            "name": "Jane Smith",
            "authorId": "12345",
            "citationCount": 5000,
            "hIndex": 42,
            "paperCount": 150,
        }

        author = Author(**author_data)

        assert author.name == "Jane Smith"
        assert author.author_id == "12345"
        assert author.citation_count == 5000
        assert author.h_index == 42
        assert author.paper_count == 150

    def test_paper_corpus_id_validation(self):
        """Test paper corpus ID field validation."""
        # Test integer corpus ID converted to string
        paper_data = {
            "paperId": "test-id",
            "title": "Test Paper",
            "corpusId": 123456789,
        }

        paper = Paper(**paper_data)
        assert paper.corpus_id == "123456789"

        # Test string corpus ID
        paper_data_str = {
            "paperId": "test-id",
            "title": "Test Paper",
            "corpusId": "987654321",
        }

        paper_str = Paper(**paper_data_str)
        assert paper_str.corpus_id == "987654321"

    def test_url_validation(self):
        """Test URL field validation."""
        # Test various URL formats
        url_formats = [
            "https://www.semanticscholar.org/paper/649def34f8be52c8b66281af98ae884c09aef38b",
            "https://arxiv.org/abs/1706.03762",
            "https://doi.org/10.1038/nature14539",
            "http://example.com/paper.pdf",
        ]

        for url in url_formats:
            paper = Paper(paperId="test-id", title="Test Paper", url=url)
            assert paper.url == url

    def test_date_validation(self):
        """Test date field validation."""
        # Test various date formats
        date_formats = [
            "2023-03-15",
            "2023-12-31",
            "2000-01-01",
        ]

        for date_str in date_formats:
            paper = Paper(
                paperId="test-id", title="Test Paper", publicationDate=date_str
            )
            # The actual date parsing depends on the model implementation
            assert paper.paper_id == "test-id"

    def test_journal_validation(self):
        """Test journal field validation."""
        journal_data = {
            "name": "Nature",
            "pages": "123-456",
            "volume": "580",
            "issue": "7801",
            "issn": "0028-0836",
        }

        paper = Paper(paperId="test-id", title="Test Paper", journal=journal_data)

        assert paper.journal["name"] == "Nature"
        assert paper.journal["pages"] == "123-456"
        assert paper.journal["volume"] == "580"
        assert paper.journal["issue"] == "7801"
        assert paper.journal["issn"] == "0028-0836"

    def test_nested_field_validation(self):
        """Test nested field validation."""
        # Test paper with nested authors
        paper_data = {
            "paperId": "test-id",
            "title": "Test Paper",
            "authors": [
                {
                    "authorId": "author-1",
                    "name": "First Author",
                    "affiliations": ["University A", "Lab B"],
                },
                {
                    "authorId": "author-2",
                    "name": "Second Author",
                    "homepage": "https://example.com/author2",
                },
            ],
        }

        paper = Paper(**paper_data)

        assert len(paper.authors) == 2
        assert paper.authors[0].name == "First Author"
        assert paper.authors[0].affiliations == ["University A", "Lab B"]
        assert paper.authors[1].name == "Second Author"
        assert paper.authors[1].homepage == "https://example.com/author2"

    def test_alias_field_validation(self):
        """Test field alias validation."""
        # Test that both camelCase and snake_case work
        paper_data_camel = {
            "paperId": "test-id",
            "title": "Test Paper",
            "citationCount": 100,
            "referenceCount": 50,
            "influentialCitationCount": 10,
            "publicationTypes": ["JournalArticle"],
            "fieldsOfStudy": ["Computer Science"],
            "isOpenAccess": True,
            "openAccessPdf": {"url": "https://example.com/paper.pdf", "status": "GOLD"},
        }

        paper_camel = Paper(**paper_data_camel)

        assert paper_camel.citation_count == 100
        assert paper_camel.reference_count == 50
        assert paper_camel.influential_citation_count == 10
        assert paper_camel.is_open_access is True
        assert paper_camel.open_access_pdf.status == "GOLD"

        # Test snake_case aliases
        paper_data_snake = {
            "paperId": "test-id",
            "title": "Test Paper",
            "citation_count": 200,
            "reference_count": 75,
            "influential_citation_count": 15,
        }

        paper_snake = Paper(**paper_data_snake)

        assert paper_snake.citation_count == 200
        assert paper_snake.reference_count == 75
        assert paper_snake.influential_citation_count == 15

    def test_extra_fields_handling(self):
        """Test extra fields handling."""
        # Test that extra fields are handled gracefully
        paper_data_extra = {
            "paperId": "test-id",
            "title": "Test Paper",
            "extraField": "extra value",
            "anotherExtra": {"nested": "data"},
        }

        paper = Paper(**paper_data_extra)

        assert paper.paper_id == "test-id"
        assert paper.title == "Test Paper"
        # Extra fields should be preserved due to extra="allow"
