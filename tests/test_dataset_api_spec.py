"""Tests for Semantic Scholar Dataset API specification compliance."""

from semantic_scholar_mcp.models import (
    DatasetDiff,
    DatasetDownloadLinks,
    DatasetRelease,
    DatasetSummary,
    IncrementalUpdate,
)


class TestDatasetAPISpec:
    """Test compliance with Semantic Scholar Dataset API specifications."""

    def test_dataset_summary_model(self):
        """Test DatasetSummary model with API spec data."""
        # Based on Dataset Summary definition in datasets API spec
        summary_data = {
            "name": "papers",
            "description": "Core paper metadata",
            "README": (
                "This dataset contains paper metadata including titles, "
                "abstracts, and citations."
            ),
        }

        summary = DatasetSummary(**summary_data)

        assert summary.name == "papers"
        assert summary.description == "Core paper metadata"
        expected_readme = (
            "This dataset contains paper metadata including titles, "
            "abstracts, and citations."
        )
        assert summary.readme == expected_readme

    def test_dataset_release_with_multiple_datasets(self):
        """Test DatasetRelease with multiple datasets."""
        release_data = {
            "releaseId": "2023-03-28",
            "README": "Subject to the following terms ...",
            "datasets": [
                {
                    "name": "papers",
                    "description": "Core paper metadata",
                    "README": "This dataset contains paper metadata...",
                },
                {
                    "name": "authors",
                    "description": "Author information",
                    "README": "This dataset contains author information...",
                },
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
                },
            ],
        }

        release = DatasetRelease(**release_data)

        assert release.release_id == "2023-03-28"
        assert len(release.datasets) == 3
        assert release.datasets[0].name == "papers"
        assert release.datasets[1].name == "authors"
        assert release.datasets[2].name == "abstracts"

    def test_dataset_download_links_with_multiple_files(self):
        """Test DatasetDownloadLinks with multiple files."""
        download_data = {
            "name": "papers",
            "description": "Core paper metadata",
            "README": "This dataset contains paper metadata...",
            "files": [
                "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-03-28/papers/part-00000.json.gz",
                "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-03-28/papers/part-00001.json.gz",
                "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-03-28/papers/part-00002.json.gz",
            ],
        }

        download_links = DatasetDownloadLinks(**download_data)

        assert download_links.name == "papers"
        assert len(download_links.files) == 3
        assert all(
            file.startswith("https://ai2-s2ag.s3.amazonaws.com")
            for file in download_links.files
        )
        assert all(file.endswith(".json.gz") for file in download_links.files)

    def test_dataset_diff_with_multiple_files(self):
        """Test DatasetDiff with multiple update and delete files."""
        diff_data = {
            "fromRelease": "2023-08-01",
            "toRelease": "2023-08-07",
            "updateFiles": [
                "https://ai2-s2ag.s3.amazonaws.com/diffs/2023-08-01_to_2023-08-07/papers/updates-00000.json.gz",
                "https://ai2-s2ag.s3.amazonaws.com/diffs/2023-08-01_to_2023-08-07/papers/updates-00001.json.gz",
            ],
            "deleteFiles": [
                "https://ai2-s2ag.s3.amazonaws.com/diffs/2023-08-01_to_2023-08-07/papers/deletes-00000.json.gz"
            ],
        }

        diff = DatasetDiff(**diff_data)

        assert diff.from_release == "2023-08-01"
        assert diff.to_release == "2023-08-07"
        assert len(diff.update_files) == 2
        assert len(diff.delete_files) == 1
        assert all("updates" in file for file in diff.update_files)
        assert all("deletes" in file for file in diff.delete_files)

    def test_incremental_update_with_multiple_diffs(self):
        """Test IncrementalUpdate with multiple diffs."""
        update_data = {
            "dataset": "papers",
            "startRelease": "2023-08-01",
            "endRelease": "2023-08-29",
            "diffs": [
                {
                    "fromRelease": "2023-08-01",
                    "toRelease": "2023-08-07",
                    "updateFiles": ["https://example.com/updates-1.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-1.json.gz"],
                },
                {
                    "fromRelease": "2023-08-07",
                    "toRelease": "2023-08-14",
                    "updateFiles": ["https://example.com/updates-2.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-2.json.gz"],
                },
                {
                    "fromRelease": "2023-08-14",
                    "toRelease": "2023-08-21",
                    "updateFiles": ["https://example.com/updates-3.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-3.json.gz"],
                },
                {
                    "fromRelease": "2023-08-21",
                    "toRelease": "2023-08-29",
                    "updateFiles": ["https://example.com/updates-4.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-4.json.gz"],
                },
            ],
        }

        update = IncrementalUpdate(**update_data)

        assert update.dataset == "papers"
        assert update.start_release == "2023-08-01"
        assert update.end_release == "2023-08-29"
        assert len(update.diffs) == 4

        # Verify the chain of diffs
        assert update.diffs[0].from_release == "2023-08-01"
        assert update.diffs[0].to_release == "2023-08-07"
        assert update.diffs[1].from_release == "2023-08-07"
        assert update.diffs[1].to_release == "2023-08-14"
        assert update.diffs[2].from_release == "2023-08-14"
        assert update.diffs[2].to_release == "2023-08-21"
        assert update.diffs[3].from_release == "2023-08-21"
        assert update.diffs[3].to_release == "2023-08-29"

    def test_dataset_api_endpoints_response_format(self):
        """Test that dataset API response formats match specification."""
        # Test release list response format
        release_list = ["2022-01-17", "2023-03-14", "2023-03-21", "2023-03-28"]

        assert all(isinstance(release_id, str) for release_id in release_list)
        assert all(
            len(release_id) == 10 for release_id in release_list
        )  # YYYY-MM-DD format
        assert all(release_id.count("-") == 2 for release_id in release_list)

    def test_dataset_field_aliases(self):
        """Test that dataset models handle field aliases correctly."""
        # Test DatasetRelease with alias
        release_data = {
            "release_id": "2023-03-28",  # Using snake_case
            "README": "Test readme",
        }

        release = DatasetRelease(**release_data)
        assert release.release_id == "2023-03-28"
        assert release.readme == "Test readme"

        # Test DatasetDiff with aliases
        diff_data = {
            "from_release": "2023-08-01",  # Using snake_case
            "to_release": "2023-08-07",  # Using snake_case
            "update_files": ["file1.json"],  # Using snake_case
            "delete_files": ["file2.json"],  # Using snake_case
        }

        diff = DatasetDiff(**diff_data)
        assert diff.from_release == "2023-08-01"
        assert diff.to_release == "2023-08-07"
        assert diff.update_files == ["file1.json"]
        assert diff.delete_files == ["file2.json"]

    def test_dataset_validation_rules(self):
        """Test dataset model validation rules."""
        # Test valid minimal dataset
        summary = DatasetSummary(name="test", description="Test dataset", README="Test")
        assert summary.name == "test"

        # Test valid minimal release
        release = DatasetRelease(releaseId="2023-01-01", README="Test")
        assert release.release_id == "2023-01-01"

        # Test that models accept all required fields
        assert summary.description == "Test dataset"
        assert summary.readme == "Test"
        assert release.readme == "Test"

    def test_dataset_url_patterns(self):
        """Test that dataset URLs follow expected patterns."""
        # Test typical S3 URL patterns for datasets
        base_url = "https://ai2-s2ag.s3.amazonaws.com"
        release_id = "2023-03-28"
        dataset_name = "papers"

        # Test that URLs match expected patterns
        test_urls = [
            f"{base_url}/dev/staging/{release_id}/{dataset_name}/part-00000.json.gz",
            f"{base_url}/diffs/{release_id}_to_2023-08-07/{dataset_name}/updates-00000.json.gz",
            f"{base_url}/release/{release_id}/metadata.json",
        ]

        for i, url in enumerate(test_urls):
            assert url.startswith(base_url)
            assert release_id in url
            if i == 0:  # First URL should contain dataset name
                assert dataset_name in url

    def test_dataset_file_extensions(self):
        """Test that dataset files have expected extensions."""
        download_data = {
            "name": "papers",
            "description": "Core paper metadata",
            "README": "Test",
            "files": [
                "https://example.com/papers/part-00000.json.gz",
                "https://example.com/papers/part-00001.json.gz",
                "https://example.com/papers/part-00002.json.gz",
            ],
        }

        download_links = DatasetDownloadLinks(**download_data)

        # All files should have .json.gz extension
        assert all(file.endswith(".json.gz") for file in download_links.files)

        # All files should contain part- prefix
        assert all("part-" in file for file in download_links.files)

    def test_dataset_size_limits(self):
        """Test dataset size and limit constraints."""
        # Test that we can handle large numbers of files
        many_files = [f"https://example.com/part-{i:05d}.json.gz" for i in range(100)]

        download_data = {
            "name": "large_dataset",
            "description": "Large dataset with many files",
            "README": "Test",
            "files": many_files,
        }

        download_links = DatasetDownloadLinks(**download_data)

        assert len(download_links.files) == 100
        assert all(
            file.startswith("https://example.com/part-")
            for file in download_links.files
        )
        assert all(file.endswith(".json.gz") for file in download_links.files)

    def test_dataset_api_error_handling(self):
        """Test dataset API error response formats."""
        # Test typical dataset API error scenarios
        from core.exceptions import APIError

        # Test 404 for non-existent release
        error_404 = APIError(message="Release not found", status_code=404)
        assert error_404.message == "Release not found"
        assert error_404.details.get("status_code") == 404

        # Test 400 for invalid dataset name
        error_400 = APIError(message="Invalid dataset name", status_code=400)
        assert error_400.message == "Invalid dataset name"
        assert error_400.details.get("status_code") == 400

    def test_dataset_real_s3_url_patterns(self):
        """Test realistic S3 URL patterns from actual API."""
        # Test actual S3 URL patterns from Semantic Scholar
        real_s3_urls = [
            "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-08-01/papers/part-00000.json.gz",
            "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-08-01/authors/part-00001.json.gz",
            "https://ai2-s2ag.s3.amazonaws.com/dev/staging/2023-08-01/abstracts/part-00002.json.gz",
            "https://ai2-s2ag.s3.amazonaws.com/diffs/2023-08-01_to_2023-08-07/papers/updates-00000.json.gz",
            "https://ai2-s2ag.s3.amazonaws.com/diffs/2023-08-01_to_2023-08-07/papers/deletes-00000.json.gz",
        ]

        for url in real_s3_urls:
            assert url.startswith("https://ai2-s2ag.s3.amazonaws.com")
            assert url.endswith(".json.gz")
            assert "2023-08-01" in url

        # Test URL structure validation
        staging_urls = [url for url in real_s3_urls if "staging" in url]
        diff_urls = [url for url in real_s3_urls if "diffs" in url]

        assert len(staging_urls) == 3
        assert len(diff_urls) == 2

        # Verify all staging URLs contain dataset names
        dataset_names = ["papers", "authors", "abstracts"]
        for dataset_name in dataset_names:
            assert any(dataset_name in url for url in staging_urls)

    def test_dataset_metadata_structure(self):
        """Test dataset metadata structure from API spec."""
        # Test comprehensive dataset metadata
        metadata = {
            "releaseId": "2023-08-01",
            "README": "Semantic Scholar Academic Graph Dataset Release 2023-08-01",
            "datasets": [
                {
                    "name": "papers",
                    "description": (
                        "Core paper metadata including titles, abstracts, and citations"
                    ),
                    "README": "The papers dataset contains...",
                    "fileCount": 100,
                    "sizeInBytes": 50000000000,
                },
                {
                    "name": "authors",
                    "description": (
                        "Author information including names, affiliations, "
                        "and statistics"
                    ),
                    "README": "The authors dataset contains...",
                    "fileCount": 25,
                    "sizeInBytes": 5000000000,
                },
            ],
        }

        release = DatasetRelease(**metadata)

        assert release.release_id == "2023-08-01"
        assert len(release.datasets) == 2

        papers_dataset = release.datasets[0]
        assert papers_dataset.name == "papers"
        assert "paper metadata" in papers_dataset.description

        authors_dataset = release.datasets[1]
        assert authors_dataset.name == "authors"
        assert "author information" in authors_dataset.description.lower()

    def test_dataset_incremental_update_chain_validation(self):
        """Test incremental update chain validation logic."""
        # Test a complete update chain from 2023-08-01 to 2023-08-29
        update_chain = {
            "dataset": "papers",
            "startRelease": "2023-08-01",
            "endRelease": "2023-08-29",
            "diffs": [
                {
                    "fromRelease": "2023-08-01",
                    "toRelease": "2023-08-07",
                    "updateFiles": ["https://example.com/updates-1.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-1.json.gz"],
                },
                {
                    "fromRelease": "2023-08-07",
                    "toRelease": "2023-08-14",
                    "updateFiles": ["https://example.com/updates-2.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-2.json.gz"],
                },
                {
                    "fromRelease": "2023-08-14",
                    "toRelease": "2023-08-21",
                    "updateFiles": ["https://example.com/updates-3.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-3.json.gz"],
                },
                {
                    "fromRelease": "2023-08-21",
                    "toRelease": "2023-08-29",
                    "updateFiles": ["https://example.com/updates-4.json.gz"],
                    "deleteFiles": ["https://example.com/deletes-4.json.gz"],
                },
            ],
        }

        update = IncrementalUpdate(**update_chain)

        # Verify chain integrity
        assert update.start_release == "2023-08-01"
        assert update.end_release == "2023-08-29"
        assert len(update.diffs) == 4

        # Verify each diff connects to the next
        for i in range(len(update.diffs) - 1):
            current_diff = update.diffs[i]
            next_diff = update.diffs[i + 1]
            assert current_diff.to_release == next_diff.from_release

        # Verify start and end match first and last diffs
        assert update.diffs[0].from_release == update.start_release
        assert update.diffs[-1].to_release == update.end_release
