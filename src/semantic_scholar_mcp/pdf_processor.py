"""Utilities for downloading Semantic Scholar PDFs and producing Markdown artifacts."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import fitz
import httpx
import pymupdf4llm
from httpx import HTTPStatusError

from core.config import ApplicationConfig, PDFProcessingConfig
from core.exceptions import NotFoundError, ValidationError
from core.logging import get_logger

from .api_client import SemanticScholarClient
from .models import Paper

logger = get_logger(__name__)

UTF8 = "utf-8"

OutputMode = Literal["markdown", "chunks", "both"]


@dataclass(slots=True)
class PdfProcessingResult:
    """Container for processed PDF artifacts."""

    paper: Paper
    markdown: str | None
    chunks: list[dict[str, Any]] | None
    pdf_path: Path
    markdown_path: Path | None
    chunks_path: Path | None
    images_dir: Path | None
    memory_path: Path | None
    metadata: dict[str, Any]


@dataclass(slots=True)
class _CachedArtifacts:
    """Pre-computed artifacts loaded from disk."""

    markdown: str | None
    chunks: list[dict[str, Any]] | None
    markdown_path: Path | None
    chunks_path: Path | None
    images_dir: Path | None


async def get_paper_fulltext(
    paper_id: str,
    *,
    client: SemanticScholarClient,
    app_config: ApplicationConfig,
    output_mode: OutputMode = "chunks",
    include_images: bool = False,
    max_pages: int | None = None,
    force_refresh: bool = False,
    start_line: int | None = None,
    end_line: int | None = None,
    search_pattern: str | None = None,
    context_lines_before: int = 0,
    context_lines_after: int = 0,
) -> PdfProcessingResult:
    """Download an open-access PDF and convert it to Markdown artifacts."""
    pdf_config = app_config.pdf_processing
    if not pdf_config.enabled:
        raise ValidationError(
            "PDF processing is disabled by configuration",
            field="pdf_processing.enabled",
        )

    actual_max_pages = max_pages or pdf_config.max_pages
    if actual_max_pages is not None and actual_max_pages <= 0:
        raise ValidationError(
            "max_pages must be greater than zero",
            field="max_pages",
            value=actual_max_pages,
        )

    paper, pdf_url = await _resolve_open_access_pdf_url(
        client=client,
        paper_id=paper_id,
    )

    hashed_id = hashlib.sha1(paper.paper_id.encode("utf-8")).hexdigest()
    prefix = hashed_id[:2]

    pdf_path = await _fetch_pdf_to_disk(
        pdf_url=pdf_url,
        hashed_id=hashed_id,
        prefix=prefix,
        pdf_config=pdf_config,
        force_refresh=force_refresh,
    )

    result = await _generate_markdown_artifacts(
        pdf_path=pdf_path,
        hashed_id=hashed_id,
        prefix=prefix,
        paper=paper,
        pdf_config=pdf_config,
        output_mode=output_mode,
        include_images=include_images,
        max_pages=actual_max_pages,
        force_refresh=force_refresh,
    )

    if result.markdown is not None:
        if search_pattern:
            if start_line is not None or end_line is not None:
                raise ValidationError(
                    "Cannot specify both search_pattern and line filtering "
                    "(start_line/end_line). Please use one or the other.",
                    field="search_pattern",
                )
            lines = result.markdown.split("\n")
            total_lines = len(lines)
            found_matches = []
            matched_lines_indices = set()

            # Validate and compile regex pattern
            try:
                compiled_pattern = re.compile(search_pattern, re.DOTALL)
            except re.error as e:
                raise ValidationError(
                    f"Invalid regex pattern: {e}",
                    field="search_pattern",
                    value=search_pattern,
                )

            # Build line index for efficient line number lookup
            # Performance characteristics:
            # - Index construction: O(n) where n = markdown length
            # - For large PDFs (100+ pages, 50k+ chars): ~10-50ms overhead
            # - Binary search lookup per match: O(log m) where m = number of lines
            # - Overall: Much faster than O(n*m) naive approach for multiple matches
            line_starts = [0]
            for i, char in enumerate(result.markdown):
                if char == "\n":
                    line_starts.append(i + 1)

            def char_pos_to_line_num(char_pos: int) -> int:
                """
                Binary search to find line number from character position.

                Edge case handling:
                - If char_pos == line_starts[i], returns line i (exact match)
                - If line_starts[i] < char_pos < line_starts[i+1], returns line i
                - This ensures character positions at line boundaries map correctly

                Time complexity: O(log n) where n is the number of lines
                """
                left, right = 0, len(line_starts) - 1
                while left < right:
                    mid = (left + right + 1) // 2
                    if line_starts[mid] <= char_pos:
                        left = mid
                    else:
                        right = mid - 1
                return left

            # Collect matches with context
            for match in compiled_pattern.finditer(result.markdown):
                start_char, end_char = match.span()
                start_line_num = char_pos_to_line_num(start_char)
                end_line_num = char_pos_to_line_num(end_char)

                context_start = max(0, start_line_num - context_lines_before)
                context_end = min(total_lines, end_line_num + 1 + context_lines_after)

                for i in range(context_start, context_end):
                    if i not in matched_lines_indices:
                        # Format as markdown list item for valid markdown syntax
                        found_matches.append(f"- **Line {i + 1}:** {lines[i]}")
                        matched_lines_indices.add(i)

            # Format search results as valid markdown
            if found_matches:
                header = f"## Search Results (pattern: `{search_pattern}`)\n"
                result.markdown = header + "\n".join(found_matches)
            else:
                result.markdown = (
                    f"## Search Results (pattern: `{search_pattern}`)\n\n"
                    "No matches found."
                )

        elif start_line is not None or end_line is not None:
            lines = result.markdown.split("\n")
            total_lines = len(lines)

            # Validate line numbers
            actual_start = start_line if start_line is not None else 0
            actual_end = end_line if end_line is not None else total_lines - 1

            # Check that start <= end only when both are specified by user
            if (
                start_line is not None
                and end_line is not None
                and start_line > end_line
            ):
                raise ValidationError(
                    "start_line must be less than or equal to end_line",
                    field="start_line/end_line",
                    value=f"start={start_line}, end={end_line}",
                )

            # If start is beyond file length, return empty content
            if actual_start >= total_lines:
                result.markdown = ""
            else:
                # Ensure end doesn't exceed file bounds
                actual_end = min(actual_end, total_lines - 1)

                # Slice the lines (end_line is inclusive)
                filtered_lines = lines[actual_start : actual_end + 1]
                result.markdown = "\n".join(filtered_lines)

    return result


async def _resolve_open_access_pdf_url(
    *, client: SemanticScholarClient, paper_id: str
) -> tuple[Paper, str]:
    """Resolve the open-access PDF URL for a paper."""
    paper = await client.get_paper(
        paper_id=paper_id,
        fields=[
            "paperId",
            "title",
            "isOpenAccess",
            "openAccessPdf",
            "externalIds",
            "year",
            "authors",
            "venue",
            "tldr",
        ],
    )

    if not paper.is_open_access:
        raise NotFoundError(
            "Open access PDF is not available for this paper",
            details={"paper_id": paper.paper_id},
        )

    pdf_info = paper.open_access_pdf
    if not pdf_info or not pdf_info.url:
        raise NotFoundError(
            "Semantic Scholar did not provide a PDF URL for this paper",
            details={"paper_id": paper.paper_id},
        )

    return paper, pdf_info.url


async def _fetch_pdf_to_disk(
    *,
    pdf_url: str,
    hashed_id: str,
    prefix: str,
    pdf_config: PDFProcessingConfig,
    force_refresh: bool,
) -> Path:
    """Download the PDF to the configured artifacts directory."""
    target_dir = pdf_config.pdf_dir / prefix
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = target_dir / f"{hashed_id}.pdf"

    if pdf_path.exists() and not force_refresh:
        # Sanity check on file size
        max_bytes = pdf_config.max_pdf_size_mb * 1024 * 1024
        if pdf_path.stat().st_size > max_bytes:
            logger.warning(
                "Existing PDF exceeds size limit; forcing re-download",
                pdf_path=str(pdf_path),
                size=pdf_path.stat().st_size,
            )
            pdf_path.unlink(missing_ok=True)
        else:
            return pdf_path

    timeout = httpx.Timeout(pdf_config.request_timeout_seconds)
    max_bytes = pdf_config.max_pdf_size_mb * 1024 * 1024

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            async with client.stream("GET", pdf_url) as response:
                response.raise_for_status()

                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_bytes:
                    raise ValidationError(
                        "Remote PDF exceeds configured size limit",
                        field="Content-Length",
                        value=content_length,
                    )

                size = 0
                with pdf_path.open("wb") as file_handle:
                    async for chunk in response.aiter_bytes(
                        pdf_config.download_chunk_size
                    ):
                        size += len(chunk)
                        if size > max_bytes:
                            file_handle.close()
                            pdf_path.unlink(missing_ok=True)
                            raise ValidationError(
                                "Downloaded PDF exceeded configured size limit",
                                field="pdf_size",
                                value=size,
                            )
                        file_handle.write(chunk)
        except HTTPStatusError as error:
            pdf_path.unlink(missing_ok=True)
            raise NotFoundError(
                "Failed to download PDF from Semantic Scholar",
                details={
                    "url": pdf_url,
                    "status_code": error.response.status_code,
                },
            ) from error
        except Exception:
            pdf_path.unlink(missing_ok=True)
            raise

    return pdf_path


def _make_serializable(obj: Any) -> Any:
    """Recursively make an object JSON serializable."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    # Type-safe check for pymupdf Rect objects
    if isinstance(obj, fitz.Rect | fitz.IRect):
        return [obj.x0, obj.y0, obj.x1, obj.y1]
    return obj


async def _generate_markdown_artifacts(
    *,
    pdf_path: Path,
    hashed_id: str,
    prefix: str,
    paper: Paper,
    pdf_config: PDFProcessingConfig,
    output_mode: OutputMode,
    include_images: bool,
    max_pages: int | None,
    force_refresh: bool,
) -> PdfProcessingResult:
    """Convert a PDF into Markdown artifacts and optional memory entries."""
    markdown_dir = pdf_config.markdown_dir / prefix
    markdown_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = markdown_dir / f"{hashed_id}.md"
    chunks_path = markdown_dir / f"{hashed_id}.chunks.json"
    images_dir_candidate = markdown_dir / f"{hashed_id}_{pdf_config.image_dir_name}"

    cached = _load_cached_artifacts(
        force_refresh=force_refresh,
        output_mode=output_mode,
        include_images=include_images,
        markdown_path=markdown_path,
        chunks_path=chunks_path,
        images_dir=images_dir_candidate,
    )

    cache_hit = cached is not None
    raw_chunks: list[dict[str, Any]]
    stored_markdown: str | None = None
    markdown_path_on_disk: Path | None = (
        markdown_path if markdown_path.exists() else None
    )
    chunks_path_on_disk: Path | None = chunks_path if chunks_path.exists() else None
    images_dir_path: Path | None = (
        cached.images_dir if cached is not None and cached.images_dir else None
    )

    if cache_hit:
        assert cached is not None  # narrow type for type-checkers
        raw_chunks = list(cached.chunks or [])
        stored_markdown = cached.markdown
        markdown_path_on_disk = cached.markdown_path or markdown_path_on_disk
        chunks_path_on_disk = cached.chunks_path or chunks_path_on_disk
    else:
        conversion_kwargs: dict[str, Any] = {"page_chunks": True}

        if include_images:
            images_dir_candidate.mkdir(parents=True, exist_ok=True)
            images_dir_path = images_dir_candidate
            conversion_kwargs["write_images"] = True
            conversion_kwargs["image_path"] = str(images_dir_candidate)
            conversion_kwargs["image_format"] = pdf_config.image_format
        elif images_dir_candidate.exists() and not force_refresh:
            images_dir_path = images_dir_candidate

        raw_chunks = await asyncio.to_thread(
            _convert_pdf_to_chunks,
            pdf_path,
            conversion_kwargs,
        )

        if not isinstance(raw_chunks, list):
            raise ValidationError(
                "PDF conversion produced unexpected output",
                field="chunks",
            )

        stored_markdown = _chunks_to_markdown(raw_chunks)

        if pdf_config.store_markdown_artifacts:
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            markdown_path.write_text(stored_markdown, encoding=UTF8)
            markdown_path_on_disk = markdown_path
        elif markdown_path.exists():
            markdown_path_on_disk = markdown_path

        if pdf_config.store_chunk_artifacts:
            chunks_path.parent.mkdir(parents=True, exist_ok=True)
            serializable_chunks = _make_serializable(raw_chunks)
            chunks_path.write_text(
                json.dumps(serializable_chunks, ensure_ascii=False, indent=2),
                encoding=UTF8,
            )
            chunks_path_on_disk = chunks_path
        elif chunks_path.exists():
            chunks_path_on_disk = chunks_path

    if images_dir_path is None and images_dir_candidate.exists():
        images_dir_path = images_dir_candidate

    if stored_markdown is None:
        stored_markdown = _chunks_to_markdown(raw_chunks)

    selected_chunks = list(raw_chunks)
    if max_pages is not None:
        selected_chunks = selected_chunks[:max_pages]

    markdown_text = _chunks_to_markdown(selected_chunks)

    memory_path: Path | None = None
    if pdf_config.enable_memory_capture and not cache_hit:
        memory_path = _persist_processed_paper(
            paper=paper,
            markdown_text=stored_markdown,
            chunks=raw_chunks,
            hashed_id=hashed_id,
            pdf_path=pdf_path,
            markdown_path=markdown_path_on_disk or markdown_path,
            chunks_path=chunks_path_on_disk or chunks_path,
            pdf_config=pdf_config,
        )

    _update_artifact_cache_index(
        pdf_config=pdf_config,
        hashed_id=hashed_id,
        prefix=prefix,
        paper=paper,
        pdf_path=pdf_path,
        markdown_path=markdown_path_on_disk,
        chunks_path=chunks_path_on_disk,
        images_dir=images_dir_path,
        include_images=include_images,
        chunk_count=len(raw_chunks),
        cache_hit=cache_hit,
    )

    purged_entries = _enforce_cache_ttl(pdf_config=pdf_config)
    if purged_entries:
        logger.debug("Purged expired PDF artifacts", count=purged_entries)

    data_payload: dict[str, Any] = {}
    if output_mode in ("markdown", "both"):
        data_payload["markdown"] = markdown_text
    if output_mode in ("chunks", "both"):
        preview_length = pdf_config.chunk_preview_length
        enriched_chunks: list[dict[str, Any]] = []
        for chunk in selected_chunks:
            text = chunk.get("text", "")
            enriched_chunks.append(
                {
                    "page": chunk.get("page"),
                    "preview": text[:preview_length],
                    "text": text,
                }
            )
        data_payload["chunks"] = enriched_chunks

    metadata = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "page_count": len(selected_chunks),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output_mode": output_mode,
        "include_images": include_images,
        "cache_hit": cache_hit,
        "stored_chunk_count": len(raw_chunks),
    }

    return PdfProcessingResult(
        paper=paper,
        markdown=data_payload.get("markdown"),
        chunks=data_payload.get("chunks"),
        pdf_path=pdf_path,
        markdown_path=markdown_path_on_disk,
        chunks_path=chunks_path_on_disk,
        images_dir=(
            images_dir_path if images_dir_path and images_dir_path.exists() else None
        ),
        memory_path=memory_path,
        metadata=metadata,
    )


def _load_cached_artifacts(
    *,
    force_refresh: bool,
    output_mode: OutputMode,
    include_images: bool,
    markdown_path: Path,
    chunks_path: Path,
    images_dir: Path,
) -> _CachedArtifacts | None:
    """Load available artifacts from disk when cache reuse is possible."""
    if force_refresh:
        return None

    chunks_path_on_disk = chunks_path if chunks_path.exists() else None
    if chunks_path_on_disk is None:
        return None

    try:
        chunk_payload = json.loads(chunks_path_on_disk.read_text(encoding=UTF8))
    except (json.JSONDecodeError, OSError):
        return None

    if not isinstance(chunk_payload, list):
        return None

    if output_mode in ("chunks", "both") and not chunk_payload:
        return None

    markdown_path_on_disk = markdown_path if markdown_path.exists() else None
    markdown_text: str | None = None
    if markdown_path_on_disk is not None:
        try:
            markdown_text = markdown_path_on_disk.read_text(encoding=UTF8)
        except OSError:
            markdown_text = None

    images_dir_path = images_dir if images_dir.exists() else None
    if include_images and images_dir_path is None:
        return None

    return _CachedArtifacts(
        markdown=markdown_text,
        chunks=chunk_payload,
        markdown_path=markdown_path_on_disk,
        chunks_path=chunks_path_on_disk,
        images_dir=images_dir_path,
    )


def _chunks_to_markdown(chunks: list[dict[str, Any]]) -> str:
    """Join chunk text segments into a markdown string."""
    if not chunks:
        return ""

    text_segments = [chunk.get("text", "") for chunk in chunks]
    return "\n\n".join(text_segments).strip()


def _convert_pdf_to_chunks(
    pdf_path: Path,
    conversion_kwargs: dict[str, Any],
) -> list[dict[str, Any]]:
    """Wrapper to execute PyMuPDF4LLM conversion."""
    return pymupdf4llm.to_markdown(str(pdf_path), **conversion_kwargs)  # type: ignore[return-value]


def _persist_processed_paper(
    *,
    paper: Paper,
    markdown_text: str,
    chunks: list[dict[str, Any]],
    hashed_id: str,
    pdf_path: Path,
    markdown_path: Path,
    chunks_path: Path,
    pdf_config: PDFProcessingConfig,
) -> Path:
    """Persist a Serena-style memory entry for the processed paper."""
    memory_dir = pdf_config.memory_dir
    memory_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    memory_path = memory_dir / f"{timestamp}_{hashed_id}.md"

    header_lines = [
        f"# Paper Markdown Snapshot: {paper.title}",
        "",
        f"- Paper ID: `{paper.paper_id}`",
        f"- Generated At: {datetime.now(timezone.utc).isoformat()}",
        f"- PDF Path: `{pdf_path}`",
        f"- Markdown Path: `{markdown_path}`",
        f"- Chunks Path: `{chunks_path}`",
        f"- Authors: {', '.join(author.name for author in paper.authors)}",
        f"- Venue: {paper.venue or 'Unknown'} ({paper.year or 'N/A'})",
        "",
        "## TL;DR",
        paper.tldr.text if paper.tldr else "Not available.",
        "",
        "## Markdown Preview",
        markdown_text[: pdf_config.chunk_preview_length],
        "",
        "## Chunk Overview",
    ]

    for chunk in chunks[:10]:
        preview = chunk.get("text", "")[: pdf_config.chunk_preview_length]
        header_lines.append(f"- Page {chunk.get('page')}: {preview}")

    memory_path.write_text("\n".join(header_lines), encoding="utf-8")
    return memory_path


def _update_artifact_cache_index(
    *,
    pdf_config: PDFProcessingConfig,
    hashed_id: str,
    prefix: str,
    paper: Paper,
    pdf_path: Path,
    markdown_path: Path | None,
    chunks_path: Path | None,
    images_dir: Path | None,
    include_images: bool,
    chunk_count: int,
    cache_hit: bool,
) -> None:
    """Update the artifact index for quick lookups and cleanup."""
    index_path = pdf_config.cache_index_file
    index_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        existing = {}
    except json.JSONDecodeError:
        existing = {}

    existing[hashed_id] = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "prefix": prefix,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pdf_path": str(pdf_path),
        "markdown_path": str(markdown_path) if markdown_path else None,
        "chunks_path": str(chunks_path) if chunks_path else None,
        "images_dir": str(images_dir) if images_dir else None,
        "include_images": include_images,
        "chunk_count": chunk_count,
        "cache_hit": cache_hit,
    }

    index_path.write_text(
        json.dumps(existing, ensure_ascii=False, indent=2),
        encoding=UTF8,
    )


def _enforce_cache_ttl(
    *, pdf_config: PDFProcessingConfig, now: datetime | None = None
) -> int:
    """Remove expired artifacts based on the configured TTL.

    Returns the number of cache entries deleted during enforcement.
    """
    ttl_hours = getattr(pdf_config, "artifact_ttl_hours", None)
    if ttl_hours is None or ttl_hours <= 0:
        return 0

    index_path = pdf_config.cache_index_file
    if not index_path.exists():
        return 0

    try:
        index_payload = json.loads(index_path.read_text(encoding=UTF8))
    except (json.JSONDecodeError, OSError):
        return 0

    if not isinstance(index_payload, dict) or not index_payload:
        return 0

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=ttl_hours)

    removals = 0
    for hashed_id, entry in list(index_payload.items()):
        updated_at_raw = entry.get("updated_at")
        try:
            updated_at = datetime.fromisoformat(updated_at_raw)
        except (TypeError, ValueError):
            updated_at = None

        if updated_at is None or updated_at >= cutoff:
            continue

        removals += 1
        _purge_artifact_entry(
            hashed_id=hashed_id,
            entry=entry,
            pdf_config=pdf_config,
        )
        index_payload.pop(hashed_id, None)

    if removals:
        index_path.write_text(
            json.dumps(index_payload, ensure_ascii=False, indent=2),
            encoding=UTF8,
        )

    return removals


def _purge_artifact_entry(
    *, hashed_id: str, entry: dict[str, Any], pdf_config: PDFProcessingConfig
) -> None:
    """Delete on-disk artifacts for an expired cache entry."""
    pdf_path_raw = entry.get("pdf_path")
    markdown_path_raw = entry.get("markdown_path")
    chunks_path_raw = entry.get("chunks_path")
    images_dir_raw = entry.get("images_dir")

    paths_to_delete: list[Path] = []

    for candidate in (pdf_path_raw, markdown_path_raw, chunks_path_raw):
        if isinstance(candidate, str) and candidate:
            paths_to_delete.append(Path(candidate))

    for path in paths_to_delete:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.debug(
                "Failed to delete expired artifact", hashed_id=hashed_id, path=str(path)
            )

    if isinstance(images_dir_raw, str) and images_dir_raw:
        images_dir = Path(images_dir_raw)
        if images_dir.exists():
            try:
                for child in images_dir.iterdir():
                    child.unlink(missing_ok=True)
                images_dir.rmdir()
            except OSError:
                logger.debug(
                    "Failed to delete expired image directory",
                    hashed_id=hashed_id,
                    path=str(images_dir),
                )

    _cleanup_parent_directories(paths_to_delete)


def _cleanup_parent_directories(paths: list[Path]) -> None:
    """Remove empty parent directories for deleted artifacts."""
    for path in paths:
        parent = path.parent
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            logger.debug("Failed to prune artifact directory", path=str(parent))


def cleanup_pdf_cache(
    app_config: ApplicationConfig | None = None,
    *,
    now: datetime | None = None,
) -> int:
    """Manually enforce the PDF artifact TTL using the given configuration."""

    config = app_config or ApplicationConfig()
    return _enforce_cache_ttl(
        pdf_config=config.pdf_processing,
        now=now,
    )
