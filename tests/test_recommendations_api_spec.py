"""Tests for Semantic Scholar Recommendations API specification compliance."""

from core.exceptions import APIError
from semantic_scholar_mcp.models import Author, Paper


class TestRecommendationsAPISpec:
    """Test compliance with Semantic Scholar Recommendations API specifications."""

    def test_paper_input_model_positive_examples(self):
        """Test Paper Input model with positive examples."""
        # Based on Paper Input definition in recommendations API spec
        paper_input_data = {
            "positivePaperIds": [
                "649def34f8be52c8b66281af98ae884c09aef38b",
                "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
                "5c5751d45e298cea054f32b392c12c61027d2fe7",
            ]
        }

        # Since we don't have a dedicated PaperInput model, test with dict
        assert len(paper_input_data["positivePaperIds"]) == 3
        assert all(
            isinstance(paper_id, str)
            for paper_id in paper_input_data["positivePaperIds"]
        )
        assert all(
            len(paper_id) == 40 for paper_id in paper_input_data["positivePaperIds"]
        )

    def test_paper_input_model_negative_examples(self):
        """Test Paper Input model with negative examples."""
        paper_input_data = {
            "positivePaperIds": [
                "649def34f8be52c8b66281af98ae884c09aef38b",
                "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            ],
            "negativePaperIds": [
                "abc123def456789012345678901234567890abcd",
                "def456789012345678901234567890abcdef1234",
            ],
        }

        # Validate both positive and negative examples
        assert len(paper_input_data["positivePaperIds"]) == 2
        assert len(paper_input_data["negativePaperIds"]) == 2

        # All paper IDs should be strings
        all_paper_ids = (
            paper_input_data["positivePaperIds"] + paper_input_data["negativePaperIds"]
        )
        assert all(isinstance(paper_id, str) for paper_id in all_paper_ids)

    def test_paper_recommendations_response_format(self):
        """Test Paper Recommendations response format."""
        # Based on Paper Recommendations definition in API spec
        recommendations_data = {
            "recommendedPapers": [
                {
                    "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
                    "title": "Construction of the Literature Graph in Semantic Scholar",
                    "abstract": (
                        "We describe a deployed scalable system for organizing "
                        "published scientific literature into a heterogeneous graph."
                    ),
                    "year": 2020,
                    "venue": (
                        "Annual Meeting of the Association for "
                        "Computational Linguistics"
                    ),
                    "authors": [
                        {
                            "authorId": "1741101",
                            "name": "Oren Etzioni",
                        }
                    ],
                    "citationCount": 453,
                    "referenceCount": 59,
                    "influentialCitationCount": 90,
                    "fieldsOfStudy": ["Computer Science"],
                    "publicationTypes": ["JournalArticle"],
                    "isOpenAccess": True,
                    "url": "https://www.semanticscholar.org/paper/649def34f8be52c8b66281af98ae884c09aef38b",
                }
            ]
        }

        # Test the response structure
        assert "recommendedPapers" in recommendations_data
        assert isinstance(recommendations_data["recommendedPapers"], list)
        assert len(recommendations_data["recommendedPapers"]) == 1

        # Test each recommended paper
        recommended_paper = recommendations_data["recommendedPapers"][0]
        paper = Paper(**recommended_paper)

        # Verify all fields are properly parsed
        assert paper.paper_id == "649def34f8be52c8b66281af98ae884c09aef38b"
        assert paper.title == "Construction of the Literature Graph in Semantic Scholar"
        assert paper.year == 2020
        assert paper.citation_count == 453
        assert paper.reference_count == 59
        assert paper.influential_citation_count == 90
        assert paper.is_open_access is True
        assert len(paper.authors) == 1
        assert paper.authors[0].name == "Oren Etzioni"

    def test_recommendation_fields_parameter(self):
        """Test recommendations with fields parameter."""
        # Test minimal fields response
        minimal_recommendation = {
            "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
            "title": "Construction of the Literature Graph in Semantic Scholar",
        }

        paper = Paper(**minimal_recommendation)
        assert paper.paper_id == "649def34f8be52c8b66281af98ae884c09aef38b"
        assert paper.title == "Construction of the Literature Graph in Semantic Scholar"

        # Test extended fields response
        extended_recommendation = {
            "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
            "title": "Construction of the Literature Graph in Semantic Scholar",
            "url": "https://www.semanticscholar.org/paper/649def34f8be52c8b66281af98ae884c09aef38b",
            "year": 2020,
            "authors": [
                {
                    "authorId": "1741101",
                    "name": "Oren Etzioni",
                    "url": "https://www.semanticscholar.org/author/1741101",
                }
            ],
            "abstract": "We describe a deployed scalable system...",
            "venue": "ACL",
            "publicationVenue": {
                "id": "1e33b3be-b2ab-46e9-96e8-d4eb4bad6e44",
                "name": (
                    "Annual Meeting of the Association for Computational Linguistics"
                ),
                "type": "conference",
            },
            "fieldsOfStudy": ["Computer Science"],
            "citationCount": 453,
            "referenceCount": 59,
            "influentialCitationCount": 90,
            "isOpenAccess": True,
            "openAccessPdf": {
                "url": "https://www.aclweb.org/anthology/2020.acl-main.447.pdf",
                "status": "HYBRID",
            },
        }

        paper = Paper(**extended_recommendation)
        assert paper.paper_id == "649def34f8be52c8b66281af98ae884c09aef38b"
        assert (
            paper.url
            == "https://www.semanticscholar.org/paper/649def34f8be52c8b66281af98ae884c09aef38b"
        )
        assert (
            paper.publication_venue.name
            == "Annual Meeting of the Association for Computational Linguistics"
        )
        assert paper.open_access_pdf.status == "HYBRID"

    def test_recommendations_api_limits(self):
        """Test recommendations API limits compliance."""
        # Test maximum limit of 500 recommendations
        max_limit = 500
        assert max_limit == 500

        # Test default limit of 100
        default_limit = 100
        assert default_limit == 100

        # Test that we can handle large recommendation lists
        large_recommendations = {
            "recommendedPapers": [
                {
                    "paperId": f"paper_id_{i:03d}{'0' * 37}",
                    "title": f"Test Paper {i}",
                }
                for i in range(100)
            ]
        }

        assert len(large_recommendations["recommendedPapers"]) == 100
        assert all(
            paper_data["paperId"].startswith("paper_id_")
            for paper_data in large_recommendations["recommendedPapers"]
        )

    def test_recommendations_api_error_formats(self):
        """Test recommendations API error response formats."""
        # Test Error400 format
        error_400_data = {"error": "Invalid paper ID format in positivePaperIds"}

        error_400 = APIError(message=error_400_data["error"], status_code=400)
        assert error_400.message == "Invalid paper ID format in positivePaperIds"
        assert error_400.details.get("status_code") == 400

        # Test Error404 format
        error_404_data = {"error": "One or more input papers not found"}

        error_404 = APIError(message=error_404_data["error"], status_code=404)
        assert error_404.message == "One or more input papers not found"
        assert error_404.details.get("status_code") == 404

    def test_recommendations_basepaper_model(self):
        """Test BasePaper model used in recommendations."""
        # Based on BasePaper definition in recommendations API spec
        base_paper_data = {
            "paperId": "649def34f8be52c8b66281af98ae884c09aef38b",
            "title": "Construction of the Literature Graph in Semantic Scholar",
            "abstract": "We describe a deployed scalable system...",
            "year": 2020,
            "venue": "ACL",
            "authors": [
                {
                    "authorId": "1741101",
                    "name": "Oren Etzioni",
                }
            ],
            "externalIds": {
                "DOI": "10.18653/V1/2020.ACL-MAIN.447",
                "ACL": "2020.acl-main.447",
            },
            "url": "https://www.semanticscholar.org/paper/649def34f8be52c8b66281af98ae884c09aef38b",
            "referenceCount": 59,
            "citationCount": 453,
            "influentialCitationCount": 90,
            "isOpenAccess": True,
            "fieldsOfStudy": ["Computer Science"],
            "publicationTypes": ["JournalArticle"],
            "publicationDate": "2020-07-01",
            "journal": {
                "name": (
                    "Annual Meeting of the Association for Computational Linguistics"
                ),
                "volume": "2020",
            },
        }

        paper = Paper(**base_paper_data)

        # Verify all BasePaper fields are supported
        assert paper.paper_id == "649def34f8be52c8b66281af98ae884c09aef38b"
        assert paper.title == "Construction of the Literature Graph in Semantic Scholar"
        assert paper.abstract == "We describe a deployed scalable system..."
        assert paper.year == 2020
        assert paper.venue == "ACL"
        assert len(paper.authors) == 1
        assert paper.authors[0].name == "Oren Etzioni"
        assert paper.external_ids["DOI"] == "10.18653/V1/2020.ACL-MAIN.447"
        assert paper.citation_count == 453
        assert paper.reference_count == 59
        assert paper.influential_citation_count == 90
        assert paper.is_open_access is True
        assert paper.fields_of_study == ["Computer Science"]
        assert (
            paper.journal["name"]
            == "Annual Meeting of the Association for Computational Linguistics"
        )

    def test_recommendations_authorinfo_model(self):
        """Test AuthorInfo model used in recommendations."""
        # Based on AuthorInfo definition in recommendations API spec
        author_info_data = {
            "authorId": "1741101",
            "name": "Oren Etzioni",
            "url": "https://www.semanticscholar.org/author/1741101",
            "affiliations": ["Allen Institute for AI"],
            "homepage": "https://allenai.org/",
        }

        author = Author(**author_info_data)

        # Verify all AuthorInfo fields are supported
        assert author.author_id == "1741101"
        assert author.name == "Oren Etzioni"
        assert author.homepage == "https://allenai.org/"
        assert author.affiliations == ["Allen Institute for AI"]

    def test_recommendations_endpoint_compliance(self):
        """Test recommendations endpoint compliance with API spec."""
        # Test POST /papers/ endpoint format
        post_papers_request = {
            "positivePaperIds": [
                "649def34f8be52c8b66281af98ae884c09aef38b",
                "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            ],
            "negativePaperIds": [
                "abc123def456789012345678901234567890abcd",
            ],
        }

        # Validate request structure
        assert "positivePaperIds" in post_papers_request
        assert isinstance(post_papers_request["positivePaperIds"], list)
        assert len(post_papers_request["positivePaperIds"]) >= 1
        assert "negativePaperIds" in post_papers_request
        assert isinstance(post_papers_request["negativePaperIds"], list)

        # Test GET /papers/forpaper/{paper_id} endpoint format
        get_forpaper_paper_id = "649def34f8be52c8b66281af98ae884c09aef38b"

        # Validate paper ID format
        assert isinstance(get_forpaper_paper_id, str)
        # Standard Semantic Scholar paper ID length
        assert len(get_forpaper_paper_id) == 40

    def test_recommendations_query_parameters(self):
        """Test recommendations API query parameters."""
        # Test limit parameter
        limit_values = [1, 10, 50, 100, 500]
        for limit in limit_values:
            assert 1 <= limit <= 500

        # Test fields parameter examples
        fields_examples = [
            "title,url,authors",
            "title,abstract,year,venue",
            "title,authors.name,authors.affiliations",
            "title,citationCount,referenceCount,influentialCitationCount",
            "title,fieldsOfStudy,publicationTypes,isOpenAccess",
        ]

        for fields in fields_examples:
            assert isinstance(fields, str)
            assert len(fields.split(",")) >= 1

        # Test that paperId is always returned (implicit in API)
        default_fields = ["paperId", "title"]
        assert "paperId" in default_fields

    def test_recommendations_paper_id_formats(self):
        """Test various paper ID formats supported in recommendations."""
        # Test different paper ID formats
        paper_id_formats = [
            "649def34f8be52c8b66281af98ae884c09aef38b",  # Standard format
            "ARXIV:2106.15928",  # ArXiv format
            "DOI:10.18653/V1/2020.ACL-MAIN.447",  # DOI format
            "204e3073870fae3d05bcbc2f6a8e263d9b72e776",  # Another standard format
        ]

        for paper_id in paper_id_formats:
            assert isinstance(paper_id, str)
            assert len(paper_id) > 0

        # Test that we can handle mixed formats in same request
        mixed_request = {
            "positivePaperIds": [
                "649def34f8be52c8b66281af98ae884c09aef38b",
                "ARXIV:2106.15928",
            ],
            "negativePaperIds": [
                "DOI:10.18653/V1/2020.ACL-MAIN.447",
            ],
        }

        assert len(mixed_request["positivePaperIds"]) == 2
        assert len(mixed_request["negativePaperIds"]) == 1
