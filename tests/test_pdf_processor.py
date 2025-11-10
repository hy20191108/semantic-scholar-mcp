import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest

from core.config import ApplicationConfig, PDFProcessingConfig
from core.exceptions import NotFoundError, ValidationError
from semantic_scholar_mcp import pdf_processor
from semantic_scholar_mcp.api_client import SemanticScholarClient
from semantic_scholar_mcp.models import Paper
from semantic_scholar_mcp.pdf_processor import cleanup_pdf_cache, get_paper_fulltext


@pytest.fixture
def sample_paper() -> Paper:
    """Return a minimal open-access paper fixture."""
    return Paper.model_validate(
        {
            "paperId": "test-paper-id",
            "title": "Sample Paper",
            "isOpenAccess": True,
            "openAccessPdf": {"url": "https://example.org/sample.pdf"},
            "authors": [{"authorId": "1", "name": "Author One"}],
        }
    )


def build_config(tmp_path: Path) -> PDFProcessingConfig:
    """Construct a PDF processing config rooted in a temp directory."""
    base_dir = tmp_path / "artifacts"
    base_dir.mkdir(parents=True, exist_ok=True)
    return PDFProcessingConfig(
        pdf_dir=base_dir / "pdfs",
        markdown_dir=base_dir / "markdown",
        cache_index_file=base_dir / "cache" / "index.json",
        memory_dir=base_dir / "memories",
        store_markdown_artifacts=True,
        store_chunk_artifacts=True,
        enable_memory_capture=False,
    )


def build_app_config(config: PDFProcessingConfig) -> ApplicationConfig:
    """Return a lightweight ApplicationConfig substitute for testing."""
    return cast(ApplicationConfig, SimpleNamespace(pdf_processing=config))


def build_client(paper: Paper) -> SemanticScholarClient:
    """Return a SemanticScholarClient substitute backed by AsyncMock."""
    return cast(
        SemanticScholarClient,
        SimpleNamespace(get_paper=AsyncMock(return_value=paper)),
    )


@pytest.mark.anyio
async def test_get_paper_fulltext_reuses_cached_artifacts(
    sample_paper,
    tmp_path,
    monkeypatch,
):
    """Ensure cached artifacts prevent redundant conversions."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    convert_calls = {"count": 0}

    def fake_convert_pdf(path, conversion_kwargs):
        convert_calls["count"] += 1
        return [
            {"page": 1, "text": "First page"},
            {"page": 2, "text": "Second page"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    first = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="both",
    )

    assert convert_calls["count"] == 1
    assert first.metadata["cache_hit"] is False
    assert first.markdown is not None
    assert first.chunks is not None

    second = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="both",
    )

    assert convert_calls["count"] == 1
    assert second.metadata["cache_hit"] is True
    assert second.metadata["page_count"] == 2
    assert second.markdown == first.markdown
    assert second.pdf_path == first.pdf_path


@pytest.mark.anyio
async def test_include_images_uses_image_path_keyword(
    sample_paper,
    tmp_path,
    monkeypatch,
):
    """`include_images=True` forwards the correct library keyword."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    captured_kwargs: dict[str, str] = {}

    def fake_convert_pdf(path, conversion_kwargs):
        captured_kwargs.update(conversion_kwargs)
        return [{"page": 1, "text": "Page with image"}]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="chunks",
        include_images=True,
    )

    assert captured_kwargs["write_images"] is True
    assert "image_path" in captured_kwargs
    assert "image_dir" not in captured_kwargs
    assert result.images_dir is not None
    assert result.images_dir.exists()


@pytest.mark.anyio
async def test_max_pages_limits_returned_chunks(
    sample_paper,
    tmp_path,
    monkeypatch,
):
    """Ensure `max_pages` limits returned chunks while stored data remains intact."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "First"},
            {"page": 2, "text": "Second"},
            {"page": 3, "text": "Third"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="chunks",
        max_pages=1,
    )

    assert result.metadata["page_count"] == 1
    assert result.chunks is not None
    assert len(result.chunks) == 1
    assert result.chunks[0]["text"] == "First"

    assert result.chunks_path is not None
    stored_chunks = json.loads(result.chunks_path.read_text(encoding="utf-8"))
    assert len(stored_chunks) == 3


@pytest.mark.anyio
async def test_cache_ttl_removes_expired_artifacts(
    sample_paper,
    tmp_path,
    monkeypatch,
):
    """Artifacts exceeding the configured TTL are purged from disk and index."""
    config = build_config(tmp_path)
    config.artifact_ttl_hours = 1
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "First"},
            {"page": 2, "text": "Second"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
    )

    index_data = json.loads(config.cache_index_file.read_text(encoding="utf-8"))
    hashed_id = next(iter(index_data))
    index_data[hashed_id]["updated_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).isoformat()
    config.cache_index_file.write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    purged = cleanup_pdf_cache(app_config=app_config, now=datetime.now(timezone.utc))

    updated_index = json.loads(config.cache_index_file.read_text(encoding="utf-8"))
    assert hashed_id not in updated_index
    assert purged == 1
    assert not result.pdf_path.exists()
    assert result.markdown_path is None or not result.markdown_path.exists()
    assert result.chunks_path is None or not result.chunks_path.exists()


@pytest.mark.anyio
async def test_get_paper_fulltext_requires_open_access(tmp_path, sample_paper):
    """Closed-access papers surface a not found error before downloading."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    closed_paper = sample_paper.model_copy(update={"isOpenAccess": False})
    client = build_client(closed_paper)

    with pytest.raises(NotFoundError):
        await get_paper_fulltext(
            paper_id=closed_paper.paper_id,
            client=client,
            app_config=app_config,
        )


@pytest.mark.anyio
async def test_fetch_pdf_to_disk_rejects_oversized_download(
    tmp_path,
    sample_paper,
    monkeypatch,
):
    """PDF downloads exceeding the configured size limit raise a validation error."""
    config = build_config(tmp_path)
    config.max_pdf_size_mb = 1

    hashed_id = hashlib.sha1(sample_paper.paper_id.encode("utf-8")).hexdigest()
    prefix = hashed_id[:2]
    max_bytes = config.max_pdf_size_mb * 1024 * 1024

    class DummyResponse:
        def __init__(self) -> None:
            self.headers = {"Content-Length": str(max_bytes + 1)}

        def raise_for_status(self) -> None:  # pragma: no cover - simple stub
            return None

        async def aiter_bytes(self, chunk_size: int):  # pragma: no cover - not used
            yield b""

    class DummyStream:
        async def __aenter__(self) -> DummyResponse:
            return DummyResponse()

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - init stub
            pass

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        def stream(self, method: str, url: str) -> DummyStream:
            return DummyStream()

    monkeypatch.setattr(pdf_processor.httpx, "AsyncClient", DummyAsyncClient)

    with pytest.raises(ValidationError):
        await pdf_processor._fetch_pdf_to_disk(
            pdf_url="https://example.org/too-large.pdf",
            hashed_id=hashed_id,
            prefix=prefix,
            pdf_config=config,
            force_refresh=False,
        )

    pdf_path = config.pdf_dir / prefix / f"{hashed_id}.pdf"
    assert not pdf_path.exists()


@pytest.mark.anyio
async def test_conversion_error_propagates_without_artifacts(
    sample_paper,
    tmp_path,
    monkeypatch,
):
    """Conversion errors bubble up and avoid writing partial artifacts."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    with pytest.raises(RuntimeError):
        await get_paper_fulltext(
            paper_id=sample_paper.paper_id,
            client=client,
            app_config=app_config,
        )

    hashed_id = hashlib.sha1(sample_paper.paper_id.encode("utf-8")).hexdigest()
    prefix = hashed_id[:2]
    chunks_path = config.markdown_dir / prefix / f"{hashed_id}.chunks.json"
    assert not chunks_path.exists()
    assert not config.cache_index_file.exists()


@pytest.mark.anyio
async def test_line_filtering_basic(sample_paper, tmp_path, monkeypatch):
    """Test basic start_line/end_line filtering."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "Line 0\nLine 1\nLine 2\nLine 3\nLine 4"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    # Test start_line only
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        start_line=2,
    )
    assert result.markdown is not None
    lines = result.markdown.split("\n")
    assert lines == ["Line 2", "Line 3", "Line 4"]

    # Test end_line only
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        end_line=2,
        force_refresh=True,
    )
    assert result.markdown is not None
    lines = result.markdown.split("\n")
    assert lines == ["Line 0", "Line 1", "Line 2"]

    # Test both start_line and end_line
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        start_line=1,
        end_line=3,
        force_refresh=True,
    )
    assert result.markdown is not None
    lines = result.markdown.split("\n")
    assert lines == ["Line 1", "Line 2", "Line 3"]


@pytest.mark.anyio
async def test_line_filtering_start_greater_than_end(
    sample_paper, tmp_path, monkeypatch
):
    """Test that start_line > end_line raises a validation error."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "Line 0\nLine 1\nLine 2"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    with pytest.raises(ValidationError) as exc_info:
        await get_paper_fulltext(
            paper_id=sample_paper.paper_id,
            client=client,
            app_config=app_config,
            output_mode="markdown",
            start_line=5,
            end_line=2,
        )

    assert "start_line must be less than or equal to end_line" in str(exc_info.value)


@pytest.mark.anyio
async def test_search_pattern_with_context(sample_paper, tmp_path, monkeypatch):
    """Test search_pattern with context lines."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {
                "page": 1,
                "text": "Line 0\nLine 1 MATCH\nLine 2\nLine 3\nLine 4 MATCH\nLine 5",
            },
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    # Test search_pattern without context
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        search_pattern=r"MATCH",
    )
    assert result.markdown is not None
    assert "Line 1 MATCH" in result.markdown
    assert "Line 4 MATCH" in result.markdown

    # Test search_pattern with context_lines_before
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        search_pattern=r"MATCH",
        context_lines_before=1,
        force_refresh=True,
    )
    assert result.markdown is not None
    assert "Line 0" in result.markdown
    assert "Line 1 MATCH" in result.markdown
    assert "Line 3" in result.markdown
    assert "Line 4 MATCH" in result.markdown

    # Test search_pattern with context_lines_after
    result = await get_paper_fulltext(
        paper_id=sample_paper.paper_id,
        client=client,
        app_config=app_config,
        output_mode="markdown",
        search_pattern=r"MATCH",
        context_lines_after=1,
        force_refresh=True,
    )
    assert result.markdown is not None
    assert "Line 1 MATCH" in result.markdown
    assert "Line 2" in result.markdown
    assert "Line 4 MATCH" in result.markdown
    assert "Line 5" in result.markdown


@pytest.mark.anyio
async def test_search_pattern_mutually_exclusive_with_line_filter(
    sample_paper, tmp_path, monkeypatch
):
    """Test that search_pattern and line filtering cannot be used together."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "Line 0\nLine 1\nLine 2"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    # Test with both search_pattern and start_line
    with pytest.raises(ValidationError) as exc_info:
        await get_paper_fulltext(
            paper_id=sample_paper.paper_id,
            client=client,
            app_config=app_config,
            output_mode="markdown",
            search_pattern=r"Line",
            start_line=1,
        )

    assert "Cannot specify both search_pattern and line filtering" in str(
        exc_info.value
    )

    # Test with both search_pattern and end_line
    with pytest.raises(ValidationError) as exc_info:
        await get_paper_fulltext(
            paper_id=sample_paper.paper_id,
            client=client,
            app_config=app_config,
            output_mode="markdown",
            search_pattern=r"Line",
            end_line=2,
        )

    assert "Cannot specify both search_pattern and line filtering" in str(
        exc_info.value
    )


@pytest.mark.anyio
async def test_search_pattern_invalid_regex(sample_paper, tmp_path, monkeypatch):
    """Test that invalid regex patterns raise a validation error."""
    config = build_config(tmp_path)
    app_config = build_app_config(config)
    client = build_client(sample_paper)

    async def fake_fetch_pdf(**kwargs):
        pdf_file = config.pdf_dir / kwargs["prefix"] / f"{kwargs['hashed_id']}.pdf"
        pdf_file.parent.mkdir(parents=True, exist_ok=True)
        pdf_file.write_bytes(b"%PDF-1.4\n%%EOF")
        return pdf_file

    def fake_convert_pdf(path, conversion_kwargs):
        return [
            {"page": 1, "text": "Line 0\nLine 1\nLine 2"},
        ]

    monkeypatch.setattr(pdf_processor, "_fetch_pdf_to_disk", fake_fetch_pdf)
    monkeypatch.setattr(pdf_processor, "_convert_pdf_to_chunks", fake_convert_pdf)

    with pytest.raises(ValidationError) as exc_info:
        await get_paper_fulltext(
            paper_id=sample_paper.paper_id,
            client=client,
            app_config=app_config,
            output_mode="markdown",
            search_pattern=r"[invalid(regex",
        )

    assert "Invalid regex pattern" in str(exc_info.value)
