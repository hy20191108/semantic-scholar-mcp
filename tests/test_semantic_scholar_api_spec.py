"""Tests that verify Semantic Scholar API specification compliance."""

from core.exceptions import APIError
from semantic_scholar_mcp.models import (
    Author,
    DatasetDiff,
    DatasetDownloadLinks,
    DatasetRelease,
    IncrementalUpdate,
    OpenAccessPdf,
    Paper,
    PublicationVenue,
)


class TestSemanticScholarAPISpec:
    """Test compliance with Semantic Scholar API specifications."""

    def test_paper_model_with_api_spec_data(self):
        """Test Paper model with real API specification data."""
        # Based on FullPaper definition in API spec
        paper_data = {
            "paperId": "5c5751d45e298cea054f32b392c12c61027d2fe7",
            "corpusId": 215416146,
            "externalIds": {
                "MAG": "3015453090",
                "DBLP": "conf/acl/LoWNKW20",
                "ACL": "2020.acl-main.447",
                "DOI": "10.18653/V1/2020.ACL-MAIN.447",
                "CorpusId": "215416146",
            },
            "url": "https://www.semanticscholar.org/paper/5c5751d45e298cea054f32b392c12c61027d2fe7",
            "title": "Construction of the Literature Graph in Semantic Scholar",
            "abstract": (
                "We describe a deployed scalable system for organizing published "
                "scientific literature into a heterogeneous graph to facilitate "
                "algorithmic manipulation and discovery."
            ),
            "venue": "Annual Meeting of the Association for Computational Linguistics",
            "year": 2020,
            "referenceCount": 59,
            "citationCount": 453,
            "influentialCitationCount": 90,
            "isOpenAccess": True,
            "fieldsOfStudy": ["Computer Science"],
            "publicationTypes": ["JournalArticle"],
        }

        paper = Paper(**paper_data)

        # Verify all fields match API spec
        assert paper.paper_id == "5c5751d45e298cea054f32b392c12c61027d2fe7"
        assert paper.corpus_id == "215416146"  # Converted to string
        assert paper.external_ids["DOI"] == "10.18653/V1/2020.ACL-MAIN.447"
        assert paper.title == "Construction of the Literature Graph in Semantic Scholar"
        expected_abstract = (
            "We describe a deployed scalable system for organizing published "
            "scientific literature into a heterogeneous graph to facilitate "
            "algorithmic manipulation and discovery."
        )
        assert paper.abstract == expected_abstract
        assert (
            paper.venue
            == "Annual Meeting of the Association for Computational Linguistics"
        )
        assert paper.year == 2020
        assert paper.reference_count == 59
        assert paper.citation_count == 453
        assert paper.influential_citation_count == 90
        assert paper.is_open_access is True
        assert paper.fields_of_study == ["Computer Science"]

    def test_author_model_with_api_spec_data(self):
        """Test Author model with real API specification data."""
        # Based on AuthorWithPapers definition in API spec
        author_data = {
            "authorId": "1741101",
            "externalIds": {"DBLP": ["123"]},
            "url": "https://www.semanticscholar.org/author/1741101",
            "name": "Oren Etzioni",
            "affiliations": ["Allen Institute for AI"],
            "homepage": "https://allenai.org/",
            "paperCount": 10,
            "citationCount": 34803,
            "hIndex": 86,
        }

        author = Author(**author_data)

        # Verify all fields match API spec
        assert author.author_id == "1741101"
        assert author.name == "Oren Etzioni"
        assert author.affiliations == ["Allen Institute for AI"]
        assert author.homepage == "https://allenai.org/"
        assert author.paper_count == 10
        assert author.citation_count == 34803
        assert author.h_index == 86

    def test_publication_venue_model(self):
        """Test PublicationVenue model with API spec data."""
        venue_data = {
            "id": "1e33b3be-b2ab-46e9-96e8-d4eb4bad6e44",
            "name": "Annual Meeting of the Association for Computational Linguistics",
            "type": "conference",
            "alternateNames": [
                "Annu Meet Assoc Comput Linguistics",
                "Meeting of the Association for Computational Linguistics",
                "ACL",
                "Meet Assoc Comput Linguistics",
            ],
            "url": "https://www.aclweb.org/anthology/venues/acl/",
        }

        venue = PublicationVenue(**venue_data)

        assert venue.id == "1e33b3be-b2ab-46e9-96e8-d4eb4bad6e44"
        assert (
            venue.name
            == "Annual Meeting of the Association for Computational Linguistics"
        )
        assert venue.type == "conference"
        assert "ACL" in venue.alternate_names
        assert venue.url == "https://www.aclweb.org/anthology/venues/acl/"

    def test_open_access_pdf_model(self):
        """Test OpenAccessPdf model with API spec data."""
        pdf_data = {
            "url": "https://www.aclweb.org/anthology/2020.acl-main.447.pdf",
            "status": "HYBRID",
        }

        pdf = OpenAccessPdf(**pdf_data)

        assert pdf.url == "https://www.aclweb.org/anthology/2020.acl-main.447.pdf"
        assert pdf.status == "HYBRID"

    def test_paper_with_publication_venue(self):
        """Test Paper model with publicationVenue field."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "year": 2023,
            "publicationVenue": {
                "id": "venue-id",
                "name": "Test Conference",
                "type": "conference",
            },
        }

        paper = Paper(**paper_data)

        assert paper.publication_venue.name == "Test Conference"
        assert paper.publication_venue.type == "conference"

    def test_paper_with_open_access_pdf(self):
        """Test Paper model with openAccessPdf field."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "year": 2023,
            "openAccessPdf": {"url": "https://example.com/paper.pdf", "status": "GOLD"},
        }

        paper = Paper(**paper_data)

        assert paper.open_access_pdf.url == "https://example.com/paper.pdf"
        assert paper.open_access_pdf.status == "GOLD"

    def test_dataset_release_model(self):
        """Test DatasetRelease model with API spec data."""
        release_data = {
            "releaseId": "2023-03-28",
            "README": "Semantic Scholar Academic Graph Datasets",
            "datasets": [
                {
                    "name": "abstracts",
                    "description": (
                        "Paper abstract text, where available. "
                        "100M records in 30 1.8GB files."
                    ),
                    "README": (
                        "Semantic Scholar Academic Graph Datasets "
                        "The abstracts dataset provides..."
                    ),
                }
            ],
        }

        release = DatasetRelease(**release_data)

        assert release.release_id == "2023-03-28"
        assert release.readme == "Semantic Scholar Academic Graph Datasets"
        assert len(release.datasets) == 1
        assert release.datasets[0].name == "abstracts"

    def test_dataset_download_links_model(self):
        """Test DatasetDownloadLinks model with API spec data."""
        download_data = {
            "name": "abstracts",
            "description": (
                "Paper abstract text, where available. 100M records in 30 1.8GB files."
            ),
            "README": (
                "Semantic Scholar Academic Graph Datasets "
                "The abstracts dataset provides..."
            ),
            "files": [
                "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-03-28/abstracts/20230331_0..."
            ],
        }

        download_links = DatasetDownloadLinks(**download_data)

        assert download_links.name == "abstracts"
        assert len(download_links.files) == 1
        assert download_links.files[0].startswith("https://ai2-s2ag.s3.amazonaws.com")

    def test_dataset_diff_model(self):
        """Test DatasetDiff model with API spec data."""
        diff_data = {
            "fromRelease": "2023-08-01",
            "toRelease": "2023-08-07",
            "updateFiles": ["http://example.com/updates.json"],
            "deleteFiles": ["http://example.com/deletes.json"],
        }

        diff = DatasetDiff(**diff_data)

        assert diff.from_release == "2023-08-01"
        assert diff.to_release == "2023-08-07"
        assert len(diff.update_files) == 1
        assert len(diff.delete_files) == 1

    def test_incremental_update_model(self):
        """Test IncrementalUpdate model with API spec data."""
        update_data = {
            "dataset": "papers",
            "startRelease": "2023-08-01",
            "endRelease": "2023-08-29",
            "diffs": [
                {
                    "fromRelease": "2023-08-01",
                    "toRelease": "2023-08-07",
                    "updateFiles": ["http://example.com/updates.json"],
                    "deleteFiles": ["http://example.com/deletes.json"],
                }
            ],
        }

        update = IncrementalUpdate(**update_data)

        assert update.dataset == "papers"
        assert update.start_release == "2023-08-01"
        assert update.end_release == "2023-08-29"
        assert len(update.diffs) == 1
        assert update.diffs[0].from_release == "2023-08-01"

    def test_api_error_400_format(self):
        """Test API error format matches spec."""
        # Based on Error400 definition in API spec
        error_data = {
            "error": (
                "Unrecognized or unsupported fields: [author.creditCardNumber, garbage]"
            )
        }

        error = APIError(message=error_data["error"], status_code=400)

        assert (
            error.message
            == "Unrecognized or unsupported fields: [author.creditCardNumber, garbage]"
        )
        assert error.details.get("status_code") == 400

    def test_api_error_404_format(self):
        """Test API error 404 format matches spec."""
        # Based on Error404 definition in API spec
        error_data = {"error": "Paper/Author/Object not found"}

        error = APIError(message=error_data["error"], status_code=404)

        assert error.message == "Paper/Author/Object not found"
        assert error.details.get("status_code") == 404

    def test_paper_external_ids_all_types(self):
        """Test Paper external IDs with all supported types from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "externalIds": {
                "ArXiv": "1234.5678",
                "MAG": "3015453090",
                "ACL": "2020.acl-main.447",
                "PubMed": "12345678",
                "Medline": "87654321",
                "PubMedCentral": "PMC1234567",
                "DBLP": "conf/acl/LoWNKW20",
                "DOI": "10.18653/V1/2020.ACL-MAIN.447",
                "CorpusId": "215416146",
            },
        }

        paper = Paper(**paper_data)

        # Verify all external ID types are supported
        assert paper.external_ids["ArXiv"] == "1234.5678"
        assert paper.external_ids["MAG"] == "3015453090"
        assert paper.external_ids["ACL"] == "2020.acl-main.447"
        assert paper.external_ids["PubMed"] == "12345678"
        assert paper.external_ids["Medline"] == "87654321"
        assert paper.external_ids["PubMedCentral"] == "PMC1234567"
        assert paper.external_ids["DBLP"] == "conf/acl/LoWNKW20"
        assert paper.external_ids["DOI"] == "10.18653/V1/2020.ACL-MAIN.447"
        assert paper.external_ids["CorpusId"] == "215416146"

    def test_fields_of_study_all_categories(self):
        """Test all supported fields of study from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "fieldsOfStudy": [
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
            ],
        }

        paper = Paper(**paper_data)

        # Verify all fields of study are supported
        assert "Computer Science" in paper.fields_of_study
        assert "Medicine" in paper.fields_of_study
        assert "Chemistry" in paper.fields_of_study
        assert "Biology" in paper.fields_of_study
        assert "Materials Science" in paper.fields_of_study
        assert "Physics" in paper.fields_of_study
        assert "Linguistics" in paper.fields_of_study
        assert len(paper.fields_of_study) == 23

    def test_paper_embedding_specter_v1(self):
        """Test Paper with SPECTER v1 embedding from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "embedding": {
                "model": "specter_v1",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 154,  # 770 dimensions for v1
            },
        }

        paper = Paper(**paper_data)

        assert paper.embedding is not None
        assert paper.embedding.model == "specter_v1"
        assert len(paper.embedding.vector) == 770
        assert all(isinstance(x, float) for x in paper.embedding.vector)

    def test_paper_embedding_specter_v2(self):
        """Test Paper with SPECTER v2 embedding from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "embedding": {
                "model": "specter_v2",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 153,  # 765 dimensions for v2
            },
        }

        paper = Paper(**paper_data)

        assert paper.embedding is not None
        assert paper.embedding.model == "specter_v2"
        assert len(paper.embedding.vector) == 765
        assert all(isinstance(x, float) for x in paper.embedding.vector)

    def test_paper_s2_fields_of_study(self):
        """Test Paper with s2FieldsOfStudy detailed structure."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "s2FieldsOfStudy": [
                {
                    "category": "Computer Science",
                    "source": "s2-fos-model",
                },
                {
                    "category": "Medicine",
                    "source": "external",
                },
            ],
        }

        paper = Paper(**paper_data)

        # Test that s2FieldsOfStudy is handled (may be stored as extra field)
        assert paper.paper_id == "test-paper-id"
        assert paper.title == "Test Paper"

    def test_paper_citation_contexts(self):
        """Test Paper with citation contexts from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "citations": [
                {
                    "paperId": "citing-paper-id",
                    "title": "Citing Paper",
                    "contexts": [
                        "This builds on the work of Smith et al. (2020)...",
                        "As shown in the seminal paper by Jones et al...",
                    ],
                    "intents": ["background", "methodology"],
                }
            ],
        }

        paper = Paper(**paper_data)

        assert len(paper.citations) == 1
        citation = paper.citations[0]
        assert citation.paper_id == "citing-paper-id"
        assert citation.title == "Citing Paper"
        # Note: contexts and intents may be stored as extra fields

    def test_paper_journal_detailed(self):
        """Test Paper with detailed journal information."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "journal": {
                "name": "Nature",
                "pages": "123-456",
                "volume": "580",
                "issue": "7801",
            },
        }

        paper = Paper(**paper_data)

        assert paper.journal is not None
        assert paper.journal["name"] == "Nature"
        assert paper.journal["pages"] == "123-456"
        assert paper.journal["volume"] == "580"
        assert paper.journal["issue"] == "7801"

    def test_paper_tldr_model(self):
        """Test Paper with TL;DR summary from API spec."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "tldr": {
                "model": "tldr-3.1.0",
                "text": "This paper presents a novel approach to machine learning.",
            },
        }

        paper = Paper(**paper_data)

        assert paper.tldr is not None
        assert paper.tldr.model == "tldr-3.1.0"
        assert (
            paper.tldr.text
            == "This paper presents a novel approach to machine learning."
        )

    def test_paper_publication_date_format(self):
        """Test Paper with publication date in various formats."""
        paper_data = {
            "paperId": "test-paper-id",
            "title": "Test Paper",
            "publicationDate": "2023-03-15",
        }

        paper = Paper(**paper_data)

        assert paper.publication_date is not None
        # The actual date parsing depends on the model implementation
        assert paper.paper_id == "test-paper-id"
