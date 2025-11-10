"""MCP server implementation for Semantic Scholar API."""

import asyncio
import json
import logging
import multiprocessing
import os
import sys
import threading
import webbrowser
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    MutableMapping,
    Sequence,
)
from contextlib import asynccontextmanager, suppress
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any, ParamSpec, TypeVar, cast

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from core.config import ApplicationConfig, get_config
from core.core import InMemoryCache
from core.error_handler import MCPErrorHandler, mcp_error_handler
from core.exceptions import ValidationError
from core.logging import (
    TextFormatter,
    get_logger,
    initialize_logging,
)
from core.metrics_collector import MetricsCollector

from .api_client import SemanticScholarClient
from .dashboard import DashboardAPI, DashboardStats
from .instruction_loader import inject_yaml_instructions, load_all_instructions
from .models import (
    SearchFilters,
    SearchQuery,
)
from .pdf_processor import OutputMode
from .utils import (
    apply_field_selection,
    create_search_filters,
    extract_field_value,
    validate_batch_size,
)

# Type definitions for Serena compliance
TResult = TypeVar("TResult")
ToolResult = str  # Type alias for tool results (Serena-style string responses)
logger = get_logger(__name__)

# Initial MCP instructions (visible to MCP clients that honor server instructions)
INITIAL_MCP_INSTRUCTIONS = (
    "You are connected to the Semantic Scholar MCP Server.\n"
    "Guidelines:\n"
    "- Prefer compact JSON. Use data/total/offset/limit/has_more when applicable.\n"
    "- Respect API limits (~1 rps anonymous). Prefer pagination over large limits.\n"
    "- Use 'fields' to reduce payload size.\n"
    "- Suggest next steps (refine query, open refs/citations, summarize).\n"
    "- For details, use get_paper; cite requested fields in summaries.\n"
)

# Initialize MCP server with initial instructions (Serena-style)
mcp = FastMCP(name="semantic-scholar-mcp", instructions=INITIAL_MCP_INSTRUCTIONS)

# Global instances (initialized in initialize_server)
config: ApplicationConfig | None = None
api_client: SemanticScholarClient | None = None
error_handler: MCPErrorHandler | None = None
metrics_collector: MetricsCollector | None = None
dashboard_stats: DashboardStats | None = None
dashboard_api: DashboardAPI | None = None
dashboard_thread = None
dashboard_port = None
dashboard_log_messages: list[str] = []
dashboard_log_handler: logging.Handler | None = None


async def execute_api_with_error_handling(operation_name: str, operation_func):
    """Execute API operation with standardized error handling."""
    try:
        if api_client is None:
            raise RuntimeError("API client is not initialized")
        async with api_client:
            return await operation_func()
    except Exception as e:
        logger.error(f"Error in {operation_name}: {e!s}")
        return {"success": False, "error": {"type": "error", "message": str(e)}}


def extract_pagination_params(limit=None, offset=None, default_limit=10):
    """Extract pagination parameters from Field objects."""
    actual_limit = extract_field_value(limit) if limit is not None else default_limit
    actual_offset = extract_field_value(offset) if offset is not None else 0
    return actual_limit, actual_offset


def _require_config() -> ApplicationConfig:
    """Return the loaded application config or raise an error."""

    if config is None:
        raise RuntimeError(
            "Server configuration has not been initialized. "
            "Call initialize_server() first."
        )
    return config


def _require_api_client() -> SemanticScholarClient:
    """Return the initialized API client or raise an error."""

    if api_client is None:
        raise RuntimeError(
            "API client is not initialized. "
            "Call initialize_server() before invoking tools."
        )
    return api_client


@asynccontextmanager
async def _use_api_client() -> AsyncIterator[SemanticScholarClient]:
    """Async context manager that yields the configured API client."""

    client = _require_api_client()
    async with client:
        yield client


async def _with_api_client(
    runner: Callable[[SemanticScholarClient], Awaitable[TResult]],
) -> TResult:
    """Execute an API client coroutine while guaranteeing initialization."""

    async with _use_api_client() as client:
        return await runner(client)


async def _call_client_method(
    method_name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Invoke a method on the Semantic Scholar API client in a safe context."""

    async def _runner(client: SemanticScholarClient) -> Any:
        method = getattr(client, method_name)
        return await method(*args, **kwargs)

    return await _with_api_client(_runner)


def _model_to_dict(payload: Any) -> dict[str, Any]:
    """Convert Pydantic models or mappings to plain dictionaries."""

    if hasattr(payload, "model_dump"):
        # Try different combinations for compatibility with various
        # Pydantic versions and mocks
        try:
            return cast(
                dict[str, Any],
                payload.model_dump(mode="json", exclude_none=True),
            )
        except TypeError:
            try:
                return cast(dict[str, Any], payload.model_dump(exclude_none=True))
            except TypeError:
                # Fallback for basic mock objects that only have
                # model_dump() without parameters
                return cast(dict[str, Any], payload.model_dump())
    if isinstance(payload, MutableMapping):
        return dict(payload)
    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


def _success_payload(data: Any, **extra: Any) -> str:
    """Create a standard success response for MCP tools."""
    import json

    payload = {"success": True, "data": data}
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _validation_error_payload(exc: ValidationError) -> str:
    """Format validation errors consistently across tools."""
    import json

    payload = {
        "success": False,
        "error": {
            "type": "validation_error",
            "message": str(exc),
            "details": getattr(exc, "details", None),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _serialize_items(
    items: Sequence[Any],
    fields: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Convert iterable payloads to dictionaries with optional field filtering."""

    serialized: list[dict[str, Any]] = []
    for item in items:
        try:
            item_dict = _model_to_dict(item)
        except TypeError:
            logger.warning("Skipping unserializable payload", payload_type=type(item))
            continue

        if fields:
            item_dict = apply_field_selection(item_dict, fields)

        serialized.append(item_dict)

    return serialized


class DashboardLogHandler(logging.Handler):
    """In-memory log handler feeding dashboard UI."""

    def __init__(self, buffer: list[str], max_messages: int) -> None:
        super().__init__(level=logging.INFO)
        self._buffer = buffer
        self._max_messages = max_messages
        self._lock = threading.Lock()
        self.setFormatter(TextFormatter(include_context=False))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()

        with self._lock:
            self._buffer.append(message)
            overflow = len(self._buffer) - self._max_messages
            if overflow > 0:
                del self._buffer[:overflow]


def _launch_dashboard_browser(url: str) -> None:
    """Open dashboard URL in a separate process, Serena-style."""

    def _open() -> None:
        try:
            null_fd = os.open(os.devnull, os.O_WRONLY)
            try:
                os.dup2(null_fd, sys.stdout.fileno())
                os.dup2(null_fd, sys.stderr.fileno())
            finally:
                os.close(null_fd)
        except OSError:
            # Fall back silently if redirecting fails
            pass

        # Swallow exceptions to avoid noisy stderr in subprocess; parent logs success
        with suppress(Exception):
            webbrowser.open(url, new=2, autoraise=True)

    process = multiprocessing.Process(target=_open, daemon=True)
    process.start()
    process.join(timeout=1)


async def initialize_server():
    """Initialize server components."""
    global config, api_client, error_handler, metrics_collector
    global dashboard_stats, dashboard_api

    # Load .env file with robust path discovery
    import os
    from pathlib import Path

    from dotenv import load_dotenv

    def find_env_file():
        """Find .env file using multiple strategies for robustness."""
        # Strategy 1: Check current working directory first (most common case)
        cwd_env = Path.cwd() / ".env"
        if cwd_env.exists():
            logger.debug(f"Found .env file in current working directory: {cwd_env}")
            return cwd_env

        # Strategy 2: Check for explicit environment variable
        env_path_var = os.getenv("DOTENV_PATH")
        if env_path_var:
            env_path = Path(env_path_var)
            if env_path.exists():
                logger.debug(f"Found .env file via DOTENV_PATH: {env_path}")
                return env_path

        # Strategy 3: Search parent directories from current file location
        current_file = Path(__file__).resolve()
        for parent in [current_file.parent, *list(current_file.parents)]:
            env_path = parent / ".env"
            if env_path.exists():
                logger.debug(f"Found .env file in parent directory: {env_path}")
                return env_path

        logger.debug("No .env file found in any searched locations")
        return None

    # Find and load .env file
    env_path = find_env_file()
    if env_path:
        load_dotenv(env_path)
        logger.info(f"Successfully loaded .env file from {env_path}")
        # Debug: Check if API key is now available
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        api_key_status = "***SET***" if api_key else "NOT SET"
        logger.debug(f"API key after loading .env: {api_key_status}")
    else:
        logger.info("No .env file loaded - using system environment variables only")

    # Load configuration
    config = get_config()

    # Initialize logging with MCP-safe settings
    import os

    # Handle MCP mode logging configuration
    if os.getenv("MCP_MODE", "false").lower() == "true":
        # Standard MCP compatibility mode
        if not config.logging.debug_mcp_mode:
            config.logging.level = "ERROR"

    # Override log level for debug mode
    if config.logging.debug_mcp_mode and config.logging.debug_level_override:
        config.logging.level = config.logging.debug_level_override
    elif config.logging.debug_mcp_mode:
        # Enable debug logging when MCP debug mode is active
        config.logging.level = "DEBUG"

    initialize_logging(config.logging)

    # Create cache
    cache = (
        InMemoryCache(
            max_size=config.cache.max_size, default_ttl=config.cache.ttl_seconds
        )
        if config.cache.enabled
        else None
    )

    # Create API client
    api_client = SemanticScholarClient(
        config=config,
        rate_limit_config=config.rate_limit,
        retry_config=config.retry,
        logger=logger,
        cache=cache,
    )

    # Initialize error handler and metrics collector
    metrics_collector = MetricsCollector(max_history=1000)
    error_handler = MCPErrorHandler()

    # Set global instances for decorators
    from core.error_handler import set_global_error_handler
    from core.metrics_collector import set_global_metrics_collector

    set_global_metrics_collector(metrics_collector)
    set_global_error_handler(error_handler)

    # Initialize Dashboard if enabled
    global dashboard_stats, dashboard_api, dashboard_log_messages, dashboard_log_handler
    if config.dashboard.enabled:
        dashboard_stats = DashboardStats()
        dashboard_log_messages = []
        dashboard_api = DashboardAPI(
            stats=dashboard_stats,
            log_messages=dashboard_log_messages,
        )

        if config.dashboard.enable_log_collection:
            root_logger = logging.getLogger()
            if dashboard_log_handler:
                root_logger.removeHandler(dashboard_log_handler)
            dashboard_log_handler = DashboardLogHandler(
                dashboard_log_messages,
                max_messages=config.dashboard.max_log_messages,
            )
            root_logger.addHandler(dashboard_log_handler)

        logger.info(
            "Dashboard initialized",
            host=config.dashboard.host,
            port=config.dashboard.port,
        )

    # Log server initialization details
    logger.info(
        "Semantic Scholar MCP server initialized",
        version=config.server.version,
        environment=config.environment.value,
        debug_mcp_mode=config.logging.debug_mcp_mode,
        log_level=config.logging.level.value
        if hasattr(config.logging.level, "value")
        else str(config.logging.level),
        performance_metrics_enabled=config.logging.log_performance_metrics,
    )

    # Log MCP tools and resources if debug mode is enabled
    if config.logging.debug_mcp_mode:
        logger.debug_mcp(
            "MCP server configuration details",
            mcp_tools=[
                "search_papers",
                "get_paper",
                "get_paper_citations",
                "get_paper_references",
                "get_paper_authors",
                "get_author",
                "get_author_papers",
                "search_authors",
                "get_recommendations_for_paper",
                "batch_get_papers",
                "bulk_search_papers",
                "search_papers_match",
                "autocomplete_query",
                "search_snippets",
                "batch_get_authors",
                "get_recommendations_batch",
                "get_dataset_releases",
                "get_dataset_info",
                "get_dataset_download_links",
                "get_paper_fulltext",
                "get_paper_with_embeddings",
                "search_papers_with_embeddings",
                "get_incremental_dataset_updates",
                "check_api_key_status",
            ],
            mcp_resources=["papers/{paper_id}", "authors/{author_id}"],
            mcp_prompts=[
                "literature_review",
                "citation_analysis",
                "research_trend_analysis",
            ],
            cache_enabled=config.cache.enabled,
            rate_limit_enabled=config.rate_limit.enabled,
            circuit_breaker_enabled=config.circuit_breaker.enabled,
        )


# Tool implementations


P = ParamSpec("P")
ToolCoroutine = Callable[P, Awaitable[MutableMapping[str, Any]]]


# Load tool instructions from external template files (YAML/Markdown)
# This is done at module level to benefit from caching
TOOL_INSTRUCTIONS = load_all_instructions()
TOOL_INSTRUCTION_KEYS = set(TOOL_INSTRUCTIONS.keys())


REGISTERED_TOOL_NAMES: set[str] = set()


def _inject_instructions(result: Any, instruction_text: str) -> Any:
    """Attach instructions to successful tool responses."""

    # If the tool returned a JSON string, try to inject into the parsed object
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except Exception:
            return result
        if isinstance(parsed, MutableMapping):
            # Normalize to ensure `data` top-level exists
            if "data" not in parsed:
                parsed = {"data": parsed}
            parsed.setdefault("instructions", instruction_text)
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        return result

    # Only inject into mapping-like results
    if not isinstance(result, MutableMapping):
        return result

    # Normalize mapping return to ensure `data` exists
    if "data" not in result:
        result = {"data": result}

    if not instruction_text:
        logger.debug("No instruction_text provided, skipping injection")
        return result

    success_value = result.get("success")
    if success_value is False:
        logger.debug("Result marked as failure, skipping instruction injection")
        return result

    logger.debug(
        "Injecting instructions into result",
        instruction_length=len(instruction_text),
        has_instructions_key="instructions" in result,
    )
    result.setdefault("instructions", instruction_text)
    logger.debug(
        "Instructions injected successfully",
        instructions_present="instructions" in result,
    )
    return result


def with_tool_instructions(tool_name: str) -> Callable[[ToolCoroutine], ToolCoroutine]:
    """
    Decorator that injects follow-up instructions into tool descriptions.

    Implements Serena-style instruction injection by appending guidance
    to tool docstrings for better LLM interaction.
    """
    from .instruction_loader import get_instruction, get_next_steps_text

    # Support both YAML-based and Markdown-based instruction sources
    _raw = TOOL_INSTRUCTIONS.get(tool_name)
    if isinstance(_raw, dict):
        # YAML dict: format Next Steps text from YAML
        category = _raw.get("category", "")
        instruction_text = get_next_steps_text(tool_name, category)
    else:
        # Markdown string fallback
        instruction_text = _raw or get_instruction(tool_name)

    def decorator(func: ToolCoroutine) -> ToolCoroutine:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError(
                "with_tool_instructions decorator expects an async function"
            )

        REGISTERED_TOOL_NAMES.add(tool_name)

        # Serena-style: Append instructions to docstring
        if instruction_text and func.__doc__:
            # Append instructions to the existing docstring
            original_doc = func.__doc__.strip()

            # Format instructions section
            instructions_section = f"\n\n{instruction_text}"

            # Create new docstring
            func.__doc__ = original_doc + instructions_section

            logger.debug(
                "Appended instructions to tool docstring",
                tool_name=tool_name,
                original_doc_length=len(original_doc),
                instructions_length=len(instruction_text),
            )

        # Update FastMCP tool description after registration
        # This runs after @mcp.tool() has registered the tool
        def update_tool_description():
            try:
                tool = mcp._tool_manager._tools.get(tool_name)
                if tool and instruction_text:
                    # Update the tool's description with instructions
                    original_description = tool.description
                    if (
                        original_description
                        and instruction_text not in original_description
                    ):
                        tool.description = (
                            f"{original_description}\n\n{instruction_text}"
                        )
                        logger.debug(
                            "Updated MCP tool description with instructions",
                            tool_name=tool_name,
                            instructions_length=len(instruction_text),
                        )
            except Exception as exc:
                logger.warning(
                    "Failed to update tool description",
                    tool_name=tool_name,
                    error=str(exc),
                )

        # Update tool description immediately after decorator execution
        # Note: This runs synchronously at import time, which is safe because
        # we're only modifying the tool's description string (no async operations)
        update_tool_description()

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            start = perf_counter()
            result: Any
            success_flag = False

            try:
                result = await func(*args, **kwargs)
                success_flag = (
                    bool(result.get("success", True))
                    if isinstance(result, MutableMapping)
                    else True
                )
            except Exception:
                if dashboard_stats:
                    dashboard_stats.record_tool_call(
                        tool_name,
                        perf_counter() - start,
                        success=False,
                    )
                raise
            else:
                if dashboard_stats:
                    dashboard_stats.record_tool_call(
                        tool_name,
                        perf_counter() - start,
                        success=success_flag,
                    )

            # Keep JSON-based injection for backward compatibility
            return _inject_instructions(result, instruction_text)

        return async_wrapper

    return decorator


@inject_yaml_instructions("search_papers", "paper")
@with_tool_instructions("search_papers")
@mcp.tool()
@mcp_error_handler(tool_name="search_papers")
async def search_papers(
    query: str,
    limit: int = Field(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
    year: int | None = Field(default=None, description="Filter by publication year"),
    fields_of_study: list[str] | None = Field(
        default=None, description="Filter by fields of study"
    ),
    sort: str | None = Field(
        default=None, description="Sort order (relevance, citationCount, year)"
    ),
    fields: list[str] | None = Field(
        default=None,
        description="Fields to include in response (supports dot notation)",
    ),
) -> str:
    """
    Search Semantic Scholar papers with optional filters.

    This tool searches the Semantic Scholar database and returns matching papers
    with metadata like title, authors, citations, publication venue, and more.

    Args:
        query: Search query string
        limit: Number of results to return (1-100, default: 10)
        offset: Pagination offset (default: 0)
        year: Filter by publication year (optional)
        fields_of_study: Filter by academic fields (optional)
        sort: Sort order - "relevance", "citationCount", or "year" (optional)
        fields: Specific fields to include in response, supports dot notation (optional)

    Returns:
        JSON object with:
        - data: list[Paper] search results
        - total: int total hits (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Review the returned papers list and identify items worth reading
        - Request summaries or full details of papers that stand out
        - Refine your search query or add filters if results are too broad
        - Use pagination (offset/limit) to explore more results if needed
    """
    logger.debug_mcp(
        "Search papers requested",
        query=query,
        limit=limit,
        offset=offset,
        year=year,
        fields_of_study=fields_of_study,
        sort=sort,
    )

    actual_limit, actual_offset = extract_pagination_params(limit, offset, 10)
    actual_sort = extract_field_value(sort)
    actual_year = extract_field_value(year)
    actual_fields_of_study = extract_field_value(fields_of_study)
    actual_fields = extract_field_value(fields)

    logger.debug_mcp(
        "Extracted parameters",
        actual_limit=actual_limit,
        actual_offset=actual_offset,
        actual_sort=actual_sort,
        actual_year=actual_year,
        actual_fields_of_study=actual_fields_of_study,
        requested_fields=actual_fields,
    )

    search_query = SearchQuery(
        query=query,
        limit=actual_limit,
        offset=actual_offset,
        sort=actual_sort,
        fields=actual_fields,
    )

    filters_kwargs: dict[str, Any] = {}
    if actual_year is not None:
        filters_kwargs["year"] = str(actual_year)
    if actual_fields_of_study:
        filters_kwargs["fields_of_study"] = actual_fields_of_study

    if filters_kwargs:
        search_query.filters = SearchFilters(**filters_kwargs)
        logger.debug_mcp(
            "Applied search filters",
            filters=search_query.filters.model_dump() if search_query.filters else None,
        )

    result = await _with_api_client(lambda client: client.search_papers(search_query))
    papers_data = _serialize_items(result.data, actual_fields)
    payload = {
        "data": papers_data,
        "total": result.total,
        "offset": result.offset,
        "limit": result.limit,
        "has_more": result.has_more,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper", "paper")
@with_tool_instructions("get_paper")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper")
async def get_paper(
    paper_id: str,
    fields: list[str] | None = Field(
        default=None,
        description="Fields to include in response (supports dot notation)",
    ),
    include_citations: bool = Field(
        default=False, description="Include citation details"
    ),
    include_references: bool = Field(
        default=False, description="Include reference details"
    ),
) -> str:
    """
    Retrieve detailed information about a specific paper.

    Fetches comprehensive metadata for a single paper from Semantic Scholar,
    including title, authors, abstract, citations, references, and publication details.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID
        fields: Specific fields to include in response, supports dot notation (optional)
        include_citations: Whether to include citation details (default: False)
        include_references: Whether to include reference details (default: False)

    Returns:
        JSON object with:
        - data: Paper (filtered by fields if specified)

    Next Steps:
        - Examine the abstract, authors, and venue to confirm relevance
        - Request a summary of specific sections or findings
        - Consider checking citations or references for deeper context
    """
    actual_fields = extract_field_value(fields)

    paper = await _call_client_method(
        "get_paper",
        paper_id=paper_id,
        fields=actual_fields,
        include_citations=include_citations,
        include_references=include_references,
    )
    paper_dict = _model_to_dict(paper)
    if actual_fields:
        paper_dict = apply_field_selection(paper_dict, actual_fields)
    return json.dumps({"data": paper_dict}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper_citations", "paper")
@with_tool_instructions("get_paper_citations")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper_citations")
async def get_paper_citations(
    paper_id: str,
    limit: int = Field(
        default=100,
        ge=1,
        le=9999,
        description="Number of citations to return (max 9999)",
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Get citations for a specific paper.

    Retrieves the list of papers that cite this paper, helping you understand
    its impact and follow-up research.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID
        limit: Maximum number of citations to return (1-9999, default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[Citation]
        - count: int number of items returned in this page
        - offset: int request offset
        - limit: int page size

    Next Steps:
        - Review citing papers to understand follow-up research
        - Ask for a comparison between key citing works
        - Use get_paper on notable citations to inspect details
    """
    actual_limit, actual_offset = extract_pagination_params(limit, offset, 100)

    citations = await _call_client_method(
        "get_paper_citations",
        paper_id=paper_id,
        limit=actual_limit,
        offset=actual_offset,
    )
    citations_data = _serialize_items(citations.data)
    payload = {
        "data": citations_data,
        "total": citations.total,
        "count": len(citations_data),
        "offset": citations.offset,
        "limit": citations.limit,
        "has_more": citations.has_more,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper_references", "paper")
@with_tool_instructions("get_paper_references")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper_references")
async def get_paper_references(
    paper_id: str,
    limit: int = Field(
        default=100, ge=1, le=1000, description="Number of references to return"
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Get references for a specific paper.

    Retrieves the list of papers referenced by this paper, helping you map
    the foundational work and research context.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID
        limit: Maximum number of references to return (1-1000, default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[Reference]
        - count: int number of items returned in this page
        - offset: int request offset
        - limit: int page size

    Next Steps:
        - Scan referenced papers to map the foundational work
        - Ask for brief summaries of the most influential references
        - Retrieve full details for any reference with get_paper
    """
    actual_limit, actual_offset = extract_pagination_params(limit, offset, 100)

    references = await _call_client_method(
        "get_paper_references",
        paper_id=paper_id,
        limit=actual_limit,
        offset=actual_offset,
    )
    # Handle None or empty data gracefully
    references_data = _serialize_items(references.data or [])
    payload = {
        "data": references_data,
        "total": references.total,
        "count": len(references_data),
        "offset": references.offset,
        "limit": references.limit,
        "has_more": references.has_more,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper_authors", "paper")
@with_tool_instructions("get_paper_authors")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper_authors")
async def get_paper_authors(
    paper_id: str,
    limit: int = Field(
        default=100, ge=1, le=1000, description="Number of authors to return"
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Get detailed author information for a specific paper.

    Retrieves comprehensive author profiles for all authors of a paper,
    including affiliations, h-index, and publication metrics.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID
        limit: Maximum number of authors to return (1-1000, default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[Author]
        - total: int total authors (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Identify recurring collaborators or leading authors
        - Ask for author profiles to evaluate expertise
        - Follow up with get_author_papers for a selected researcher
    """
    actual_limit, actual_offset = extract_pagination_params(limit, offset, 100)

    result = await _call_client_method(
        "get_paper_authors",
        paper_id=paper_id,
        limit=actual_limit,
        offset=actual_offset,
    )
    authors_data = _serialize_items(result.data)
    return json.dumps(
        {
            "data": authors_data,
            "total": result.total,
            "offset": result.offset,
            "limit": result.limit,
            "has_more": result.has_more,
        },
        ensure_ascii=False,
        indent=2,
    )


@inject_yaml_instructions("get_author", "author")
@with_tool_instructions("get_author")
@mcp.tool()
@mcp_error_handler(tool_name="get_author")
async def get_author(author_id: str) -> str:
    """
    Get detailed information about an author.

    Retrieves comprehensive profile information for a researcher,
    including publications, citations, h-index, and affiliations.

    Args:
        author_id: Semantic Scholar author ID

    Returns:
        JSON object with:
        - data: Author

    Next Steps:
        - Review the author metrics and affiliations provided
        - Ask for trends or notable publications in their portfolio
        - Use get_author_papers for recent work or specific years
    """
    author = await _call_client_method("get_author", author_id=author_id)
    return json.dumps({"data": _model_to_dict(author)}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_author_papers", "author")
@with_tool_instructions("get_author_papers")
@mcp.tool()
@mcp_error_handler(tool_name="get_author_papers")
async def get_author_papers(
    author_id: str,
    limit: int = Field(
        default=100, ge=1, le=1000, description="Number of papers to return"
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Get papers by a specific author.

    Retrieves the publication list for a researcher, including paper titles,
    venues, citations, and publication dates.

    Args:
        author_id: Semantic Scholar author ID
        limit: Maximum number of papers to return (1-1000, default: 100)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[Paper]
        - total: int total papers (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Scan the publication list for themes or collaborations
        - Request summaries of standout papers for a quick brief
        - Compare with other authors to spot overlapping research
    """
    result = await _call_client_method(
        "get_author_papers",
        author_id=author_id,
        limit=limit,
        offset=offset,
    )
    papers_data = _serialize_items(result.data)
    return json.dumps(
        {
            "data": papers_data,
            "total": result.total,
            "offset": result.offset,
            "limit": result.limit,
            "has_more": result.has_more,
        },
        ensure_ascii=False,
        indent=2,
    )


@inject_yaml_instructions("search_authors", "author")
@with_tool_instructions("search_authors")
@mcp.tool()
@mcp_error_handler(tool_name="search_authors")
async def search_authors(
    query: str,
    limit: int = Field(
        default=10, ge=1, le=100, description="Number of results to return"
    ),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Search for authors by name.

    Searches the Semantic Scholar database for researchers matching the query,
    returning author profiles with basic metrics.

    Args:
        query: Author name search query
        limit: Maximum number of results to return (1-100, default: 10)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[Author]
        - total: int total hits (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Inspect the candidate list and shortlist promising researchers
        - Request get_author for profiles you want to explore
        - Note emerging topics or institutions tied to each author
    """
    # Extract actual values from Field objects if needed
    actual_offset = extract_field_value(offset)

    result = await _call_client_method(
        "search_authors",
        query=query,
        limit=limit,
        offset=actual_offset,
    )
    authors_data = _serialize_items(result.data)
    return json.dumps(
        {
            "data": authors_data,
            "total": result.total,
            "offset": result.offset,
            "limit": result.limit,
            "has_more": result.has_more,
        },
        ensure_ascii=False,
        indent=2,
    )


@inject_yaml_instructions("get_recommendations_for_paper", "prompts")
@with_tool_instructions("get_recommendations_for_paper")
@mcp.tool()
@mcp_error_handler(tool_name="get_recommendations_for_paper")
async def get_recommendations_for_paper(
    paper_id: str,
    limit: int = Field(
        default=10, ge=1, le=100, description="Number of recommendations"
    ),
    fields: list[str] | None = Field(
        default=None, description="Fields to include in response"
    ),
) -> str:
    """
    Get paper recommendations based on a given paper.

    Uses Semantic Scholar's recommendation algorithm to find related papers
    based on content similarity and citation patterns.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID to base recommendations on
        limit: Maximum number of recommendations to return (1-100, default: 10)
        fields: Fields to include in response (optional)

    Returns:
        JSON object with:
        - data: list[Paper]
        - count: int number of recommendations returned

    Next Steps:
        - Review recommended papers and note recurring concepts
        - Ask for summaries or contrasts with the source paper
        - Queue follow-up searches for promising recommendations
    """
    papers = await _call_client_method(
        "get_recommendations_for_paper",
        paper_id=paper_id,
        limit=limit,
        fields=fields,
    )
    papers_data = _serialize_items(papers, extract_field_value(fields))
    payload = {"data": papers_data, "count": len(papers_data)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("batch_get_papers", "paper")
@with_tool_instructions("batch_get_papers")
@mcp.tool()
@mcp_error_handler(tool_name="batch_get_papers")
async def batch_get_papers(
    paper_ids: list[str],
    fields: list[str] | None = Field(
        default=None,
        description="Fields to include in response (supports dot notation)",
    ),
) -> str:
    """
    Get multiple papers in a single request.

    Efficiently retrieves details for multiple papers in a single API call,
    useful for batch processing and reducing API overhead.

    Args:
        paper_ids: List of paper IDs - Semantic Scholar IDs, DOIs, or
            ArXiv IDs (max 500)
        fields: Optional list of fields to include, supports dot notation

    Returns:
        JSON object with:
        - data: list[Paper]
        - count: int number of papers returned

    Next Steps:
        - Check that each requested paper is present and complete
        - Ask for a synthesis across the batch to spot shared themes
        - Plan deeper dives using get_paper where more detail is needed
    """
    validate_batch_size(paper_ids, 500)
    actual_fields = extract_field_value(fields)

    papers = await _call_client_method(
        "batch_get_papers",
        paper_ids=paper_ids,
        fields=actual_fields,
    )
    papers_data = _serialize_items(papers, actual_fields)
    payload = {"data": papers_data, "count": len(papers_data)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("bulk_search_papers", "paper")
@with_tool_instructions("bulk_search_papers")
@mcp.tool()
@mcp_error_handler(tool_name="bulk_search_papers")
async def bulk_search_papers(
    query: str,
    fields: list[str] | None = Field(
        default=None,
        description="Fields to include in response (supports dot notation)",
    ),
    publication_types: list[str] | None = Field(
        default=None, description="Publication types to filter by"
    ),
    fields_of_study: list[str] | None = Field(
        default=None, description="Fields of study to filter by"
    ),
    year_range: str | None = Field(
        default=None, description="Year range (e.g., '2020-2023', '2020-', '-2023')"
    ),
    venue: str | None = Field(default=None, description="Venue to filter by"),
    min_citation_count: int | None = Field(
        default=None, description="Minimum citation count"
    ),
    open_access_pdf: bool | None = Field(
        default=None, description="Filter by open access PDF availability"
    ),
    sort: str | None = Field(
        default=None,
        description="Sort order (relevance, citationCount, publicationDate)",
    ),
) -> str:
    """
    Bulk search papers with advanced filtering (unlimited results).

    Performs comprehensive search across Semantic Scholar with multiple filter criteria,
    suitable for large-scale research analysis and dataset creation.

    Args:
        query: Search query string
        fields: Optional list of fields to include, supports dot notation
        publication_types: Types of publications to include
            (e.g., 'JournalArticle', 'Conference')
        fields_of_study: Academic fields to filter by
            (e.g., 'Computer Science', 'Medicine')
        year_range: Publication year range (e.g., '2020-2023', '2020-', '-2023')
        venue: Publication venue to filter by
        min_citation_count: Minimum citation threshold
        open_access_pdf: Filter by open access PDF availability
        sort: Sort order - "relevance", "citationCount", or "publicationDate"

    Returns:
        JSON object with:
        - data: list[Paper]
        - count: int number of papers returned

    Next Steps:
        - Inspect aggregated hits and decide which query succeeded
        - Ask for focused summaries of the best-performing results
        - Iterate on the weaker queries with refined keywords
    """
    # Extract actual field value
    actual_fields = extract_field_value(fields)

    papers = await _call_client_method(
        "search_papers_bulk",
        query=query,
        fields=actual_fields,
        publication_types=publication_types,
        fields_of_study=fields_of_study,
        year_range=year_range,
        venue=venue,
        min_citation_count=min_citation_count,
        open_access_pdf=open_access_pdf,
        sort=sort,
    )
    papers_data = _serialize_items(papers, actual_fields)
    payload = {"data": papers_data, "count": len(papers_data)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("search_papers_match", "paper")
@with_tool_instructions("search_papers_match")
@mcp.tool()
@mcp_error_handler(tool_name="search_papers_match")
async def search_papers_match(
    title: str,
    fields: list[str] | None = Field(
        default=None,
        description="Fields to include in response (supports dot notation)",
    ),
) -> str:
    """
    Search papers by title matching.

    Finds papers with titles that closely match the provided string,
    useful for finding specific papers when you know the title.

    Args:
        title: Paper title to search for (exact or partial match)
        fields: Optional list of fields to include, supports dot notation

    Returns:
        JSON object with:
        - data: list[Paper]
        - count: int number of papers returned

    Next Steps:
        - Verify the matching titles to confirm precision
        - Request details on the closest matches for validation
        - Adjust the exact title or add identifiers if results are sparse
    """
    # Extract actual field value
    actual_fields = extract_field_value(fields)

    papers = await _call_client_method(
        "search_papers_match",
        title=title,
        fields=actual_fields,
    )
    papers_data = _serialize_items(papers.data, actual_fields)
    payload = {
        "data": papers_data,
        "total": papers.total,
        "count": len(papers_data),
        "offset": papers.offset,
        "limit": papers.limit,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("autocomplete_query", "prompts")
@with_tool_instructions("autocomplete_query")
@mcp.tool()
@mcp_error_handler(tool_name="autocomplete_query")
async def autocomplete_query(
    query: str,
    limit: int = Field(default=10, ge=1, le=50, description="Number of suggestions"),
) -> str:
    """
    Get query autocompletion suggestions.

    Provides search query completions to help refine and improve your search terms.

    Args:
        query: Partial query string to complete
        limit: Maximum number of suggestions to return (1-50, default: 10)

    Returns:
        JSON object with:
        - data: list[str]
        - count: int number of suggestions

    Next Steps:
        - Use the suggestions to craft a clearer search prompt
        - Ask for the pros and cons of the top suggested phrases
        - Run search_papers with the selected completion
    """
    suggestions = await _call_client_method(
        "autocomplete_query",
        query=query,
        limit=limit,
    )
    payload = {"data": suggestions, "count": len(suggestions)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("search_snippets", "prompts")
@with_tool_instructions("search_snippets")
@mcp.tool()
@mcp_error_handler(tool_name="search_snippets")
async def search_snippets(
    query: str,
    limit: int = Field(default=10, ge=1, le=100, description="Number of snippets"),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
) -> str:
    """
    Search text snippets in papers.

    Searches for specific text passages within papers, returning contextual snippets
    around matches to help assess relevance quickly.

    Args:
        query: Search query string
        limit: Maximum number of snippets to return (1-100, default: 10)
        offset: Pagination offset (default: 0)

    Returns:
        JSON object with:
        - data: list[dict] snippets
        - total: int total hits (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Read snippet contexts to judge relevance quickly
        - Ask for full paper details on the most compelling snippets
        - Consider refining keywords if noise remains high
    """
    result = await _call_client_method(
        "search_snippets",
        query=query,
        limit=limit,
        offset=offset,
    )
    return json.dumps(
        {
            "data": result.data,
            "total": result.total,
            "offset": result.offset,
            "limit": result.limit,
            "has_more": result.has_more,
        },
        ensure_ascii=False,
        indent=2,
    )


@inject_yaml_instructions("batch_get_authors", "author")
@with_tool_instructions("batch_get_authors")
@mcp.tool()
@mcp_error_handler(tool_name="batch_get_authors")
async def batch_get_authors(
    author_ids: list[str],
) -> str:
    """
    Get multiple authors in a single request.

    Efficiently retrieves profiles for multiple researchers in a single API call,
    useful for batch processing and comparative analysis.

    Args:
        author_ids: List of Semantic Scholar author IDs (max 1000)

    Returns:
        JSON object with:
        - data: list[Author]
        - count: int number of authors returned

    Next Steps:
        - Confirm that each requested author profile is included
        - Ask for a comparative overview across these researchers
        - Plan next queries such as get_author_papers per person
    """
    validate_batch_size(author_ids, 1000)
    authors = await _call_client_method(
        "batch_get_authors",
        author_ids=author_ids,
    )
    authors_data = _serialize_items(authors)
    payload = {"data": authors_data, "count": len(authors_data)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_recommendations_batch", "prompts")
@with_tool_instructions("get_recommendations_batch")
@mcp.tool()
@mcp_error_handler(tool_name="get_recommendations_batch")
async def get_recommendations_batch(
    positive_paper_ids: list[str],
    negative_paper_ids: list[str] | None = None,
    limit: int = 10,
) -> str:
    """
    Get advanced recommendations based on positive and negative examples.

    Uses machine learning to recommend papers similar to positive examples
    while avoiding papers similar to negative examples.

    Args:
        positive_paper_ids: Paper IDs to use as positive examples (what you want)
        negative_paper_ids: Paper IDs to use as negative examples
            (what to avoid, optional)
        limit: Maximum number of recommendations to return (default: 10)

    Returns:
        JSON object with:
        - data: list[Paper]
        - count: int number of recommendations returned

    Next Steps:
        - Scan recommended sets for consensus picks
        - Ask for clusters or themes spanning the recommendations
        - Prioritize papers for closer reading or follow-up calls
    """
    papers = await _call_client_method(
        "get_recommendations_batch",
        positive_paper_ids=positive_paper_ids,
        negative_paper_ids=negative_paper_ids,
        limit=limit,
    )
    recs = _serialize_items(papers)
    payload = {"data": recs, "count": len(recs)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_dataset_releases", "dataset")
@with_tool_instructions("get_dataset_releases")
@mcp.tool()
@mcp_error_handler(tool_name="get_dataset_releases")
async def get_dataset_releases() -> str:
    """
    Get available dataset releases.

    Lists all available Semantic Scholar dataset releases with version information
    and release dates.

    Returns:
        JSON object with:
        - data: list[dict] dataset releases
        - count: int number of releases returned

    Next Steps:
        - Identify the release that matches your research needs
        - Ask for differences between adjacent releases if unsure
        - Fetch detailed metadata via get_dataset_info
    """
    releases = await _call_client_method("get_dataset_releases")
    # releases is a list of strings (release IDs), not objects
    payload = {"data": releases, "count": len(releases)}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_dataset_info", "dataset")
@with_tool_instructions("get_dataset_info")
@mcp.tool()
@mcp_error_handler(tool_name="get_dataset_info")
async def get_dataset_info(release_id: str) -> str:
    """
    Get dataset release information.

    Retrieves detailed metadata for a specific dataset release, including
    file counts, sizes, and content descriptions.

    Args:
    release_id: Dataset release ID (from get_dataset_releases)

    Returns:
        JSON object with:
        - data: dict dataset metadata

    Next Steps:
        - Review dataset size, modality, and coverage carefully
        - Ask for implications or usage tips for this dataset
        - Proceed to get_dataset_download_links when ready
    """
    info = await _call_client_method(
        "get_dataset_info",
        release_id=release_id,
    )
    return json.dumps({"data": _model_to_dict(info)}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_dataset_download_links", "dataset")
@with_tool_instructions("get_dataset_download_links")
@mcp.tool()
@mcp_error_handler(tool_name="get_dataset_download_links")
async def get_dataset_download_links(release_id: str, dataset_name: str) -> str:
    """
    Get download links for a specific dataset.

    Retrieves S3 URLs and download information for a specific dataset within a release.

    Args:
        release_id: Dataset release ID (from get_dataset_releases)
        dataset_name: Name of the dataset to download

    Returns:
        JSON object with:
        - data: dict download information

    Next Steps:
        - Record the download URLs and any authentication notes
        - Ask for guidance on verifying file integrity
        - Plan storage or processing steps before downloading
    """
    links = await _call_client_method(
        "get_dataset_download_links",
        release_id=release_id,
        dataset_name=dataset_name,
    )
    # links is likely a mapping; convert if needed
    try:
        links_dict = _model_to_dict(links)  # if Pydantic model
    except TypeError:
        links_dict = links  # already a plain mapping
    return json.dumps({"data": links_dict}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper_fulltext", "pdf")
@with_tool_instructions("get_paper_fulltext")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper_fulltext")
async def get_paper_fulltext(
    paper_id: str = Field(..., description="Semantic Scholar paper ID or DOI"),
    output_mode: str | None = Field(
        default=None,
        description=(
            "Choose 'markdown', 'chunks', or 'both'. Defaults to the server "
            "configuration."
        ),
    ),
    include_images: bool = Field(
        default=False,
        description="Extract images while converting the PDF.",
    ),
    max_pages: int | None = Field(
        default=None,
        ge=1,
        description="Limit the number of pages to convert. Defaults to configuration.",
    ),
    force_refresh: bool = Field(
        default=False,
        description="Force re-download and regeneration of artifacts.",
    ),
    start_line: int | None = Field(
        default=None,
        ge=0,
        description=(
            "The 0-based index of the first line to be retrieved. "
            "If None, start from the beginning."
        ),
    ),
    end_line: int | None = Field(
        default=None,
        ge=0,
        description=(
            "The 0-based index of the last line to be retrieved (inclusive). "
            "If None, read until the end."
        ),
    ),
    search_pattern: str | None = Field(
        default=None,
        description=(
            "Optional regex pattern to search for in the markdown content. "
            "When specified, only lines containing matches and their "
            "context will be returned."
        ),
    ),
    context_lines_before: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of lines to include before each match when using search_pattern."
        ),
    ),
    context_lines_after: int = Field(
        default=0,
        ge=0,
        description=(
            "Number of lines to include after each match when using search_pattern."
        ),
    ),
) -> str:
    """
    Download an open-access PDF and expose Markdown content to MCP clients.

    Converts academic PDFs to Markdown format with optional chunking and
    image extraction,
    enabling text analysis and content summarization. Results are cached for efficiency.

    Args:
        paper_id: Semantic Scholar paper ID or DOI
        output_mode: Output format - 'markdown', 'chunks', or 'both'
            (default: server config)
        include_images: Whether to extract images from the PDF (default: False)
        max_pages: Limit pages to convert, defaults to server configuration
        force_refresh: Force re-download and regeneration of artifacts (default: False)
        start_line: The 0-based index of the first line to be retrieved (default: None)
        end_line: The 0-based index of the last line to be retrieved,
            inclusive (default: None)
        search_pattern: Optional regex pattern to search for in the markdown content.
        context_lines_before: Number of lines to include before each match.
        context_lines_after: Number of lines to include after each match.

    Returns:
        JSON object with:
        - data: {
            paper: Basic paper metadata,
            artifacts: paths for cached PDF/Markdown/chunks/images,
            content: optional markdown/chunks,
            metadata: conversion stats
          }

    Next Steps:
        - Read the Markdown file: When available, use the Read tool with
          the path from artifacts.markdown_path to view the converted content;
          this path is only returned if Markdown artifacts are enabled
        - Access chunks: Request output_mode="chunks" or "both" to populate
          content.chunks with structured text segments for analysis
        - Analyze findings: Ask for summaries, key concepts, or specific
          sections from the paper
        - Check artifacts: PDF, Markdown, and chunks are saved in
          .semantic_scholar_mcp/artifacts/ with SHA-1 partitioned paths
        - View images: If include_images=true, extracted images are in
          artifacts.images_dir
        - Leverage caching: Subsequent requests use cached artifacts unless
          force_refresh=true is specified
    """
    app_config = _require_config()
    pdf_config = app_config.pdf_processing
    if not pdf_config.enabled:
        raise ValidationError(
            "PDF processing is disabled in configuration",
            field="pdf_processing.enabled",
        )

    actual_output_mode = extract_field_value(output_mode)
    selected_mode = (actual_output_mode or pdf_config.default_output_mode).lower()
    valid_modes: set[str] = {"markdown", "chunks", "both"}
    if selected_mode not in valid_modes:
        raise ValidationError(
            "output_mode must be one of 'markdown', 'chunks', or 'both'",
            field="output_mode",
            value=selected_mode,
        )

    typed_mode: OutputMode = cast(OutputMode, selected_mode)

    async def _runner(client: SemanticScholarClient):
        from .pdf_processor import get_paper_fulltext as pdf_get_paper_fulltext

        return await pdf_get_paper_fulltext(
            paper_id=paper_id,
            client=client,
            app_config=app_config,
            output_mode=typed_mode,
            include_images=extract_field_value(include_images),
            max_pages=extract_field_value(max_pages),
            force_refresh=extract_field_value(force_refresh),
            start_line=extract_field_value(start_line),
            end_line=extract_field_value(end_line),
            search_pattern=extract_field_value(search_pattern),
            context_lines_before=extract_field_value(context_lines_before),
            context_lines_after=extract_field_value(context_lines_after),
        )

    result = await _with_api_client(_runner)

    content: dict[str, Any] = {}
    if result.markdown is not None:
        content["markdown"] = result.markdown
    if result.chunks is not None:
        content["chunks"] = result.chunks

    payload = {
        "paper": {
            "paper_id": result.paper.paper_id,
            "title": result.paper.title,
            "year": result.paper.year,
            "venue": result.paper.venue,
            "authors": [author.name for author in result.paper.authors],
        },
        "artifacts": {
            "pdf_path": str(result.pdf_path),
            "markdown_path": (
                str(result.markdown_path) if result.markdown_path else None
            ),
            "chunks_path": str(result.chunks_path) if result.chunks_path else None,
            "images_dir": str(result.images_dir) if result.images_dir else None,
            "memory_path": str(result.memory_path) if result.memory_path else None,
        },
        "content": content,
        "metadata": result.metadata,
    }
    return json.dumps({"data": payload}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_paper_with_embeddings", "paper")
@with_tool_instructions("get_paper_with_embeddings")
@mcp.tool()
@mcp_error_handler(tool_name="get_paper_with_embeddings")
async def get_paper_with_embeddings(
    paper_id: str,
    embedding_type: str = Field(
        default="specter_v2",
        description="Embedding model type (specter_v1 or specter_v2)",
    ),
) -> str:
    """
    Get paper with embedding vectors for semantic analysis.

    Retrieves paper metadata along with SPECTER embedding vectors for
    semantic similarity analysis and clustering.

    Args:
        paper_id: Semantic Scholar paper ID, DOI, or ArXiv ID
        embedding_type: Embedding model - "specter_v1" or "specter_v2"
            (default: "specter_v2")

    Returns:
        Dictionary containing:
        - success: Whether the request succeeded
        - data: Paper details with embedding vector
        - error: Error details if request failed

    Next Steps:
        - Use the embedding vector for similarity searches or clustering
        - Ask for interpretation of key metadata linked to the vector
        - Combine with search_papers_with_embeddings to expand the set
    """
    paper = await _call_client_method(
        "get_paper_with_embeddings",
        paper_id=paper_id,
        embedding_type=embedding_type,
    )
    return json.dumps({"data": _model_to_dict(paper)}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("search_papers_with_embeddings", "paper")
@with_tool_instructions("search_papers_with_embeddings")
@mcp.tool()
@mcp_error_handler(tool_name="search_papers_with_embeddings")
async def search_papers_with_embeddings(
    query: str,
    embedding_type: str = Field(
        default="specter_v2", description="Embedding model type"
    ),
    limit: int = Field(default=10, ge=1, le=100, description="Number of results"),
    offset: int = Field(default=0, ge=0, description="Offset for pagination"),
    publication_types: list[str] | None = Field(
        default=None, description="Filter by publication types"
    ),
    fields_of_study: list[str] | None = Field(
        default=None, description="Filter by fields of study"
    ),
    year_range: str | None = Field(
        default=None, description="Year range filter (e.g., '2020-2023')"
    ),
    min_citation_count: int | None = Field(
        default=None, description="Minimum citation count"
    ),
) -> str:
    """
    Search papers with embeddings for semantic analysis.

    Searches papers and returns results with SPECTER embedding vectors,
    enabling semantic similarity analysis and clustering.

    Args:
        query: Search query string
        embedding_type: Embedding model - "specter_v1" or "specter_v2"
            (default: "specter_v2")
        limit: Number of results to return (1-100, default: 10)
        offset: Pagination offset (default: 0)
        publication_types: Publication type filters
            (e.g., 'JournalArticle', 'Conference')
        fields_of_study: Field of study filters (e.g., 'Computer Science', 'Medicine')
        year_range: Year range filter (e.g., '2020-2023')
        min_citation_count: Minimum citation count threshold

    Returns:
        JSON object with:
        - data: list[Paper] results (with embeddings)
        - total: int total hits (from API)
        - offset: int request offset
        - limit: int page size
        - has_more: bool whether more results are available

    Next Steps:
        - Check each match score to gauge semantic proximity
        - Ask for a narrative summary of the closest matches
        - Feed chosen IDs into get_paper for full context
    """
    filters = create_search_filters(
        publication_types=publication_types,
        fields_of_study=fields_of_study,
        year_range=year_range,
        min_citation_count=min_citation_count,
    )

    search_query = SearchQuery(
        query=query,
        limit=extract_field_value(limit),
        offset=extract_field_value(offset),
        filters=filters,
    )

    result = await _call_client_method(
        "search_papers_with_embeddings",
        query=search_query,
        embedding_type=embedding_type,
    )
    payload = {
        "data": _serialize_items(result.data),
        "total": result.total,
        "offset": result.offset,
        "limit": result.limit,
        "has_more": result.has_more,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@inject_yaml_instructions("get_incremental_dataset_updates", "dataset")
@with_tool_instructions("get_incremental_dataset_updates")
@mcp.tool()
@mcp_error_handler(tool_name="get_incremental_dataset_updates")
async def get_incremental_dataset_updates(
    start_release_id: str,
    end_release_id: str,
    dataset_name: str,
) -> str:
    """
    Get incremental dataset updates between releases.

    Retrieves the differences between two dataset releases, useful for
    efficiently updating your local dataset copy.

    Args:
        start_release_id: Starting release ID (older version)
        end_release_id: Ending release ID (newer version)
        dataset_name: Name of the dataset

    Returns:
        JSON object with:
        - data: dict incremental update information

    Next Steps:
        - Examine update windows to schedule data refreshes
        - Ask for change summaries between the releases
        - Decide whether a full or incremental download is needed
    """
    updates = await _call_client_method(
        "get_incremental_dataset_updates",
        start_release_id=start_release_id,
        end_release_id=end_release_id,
        dataset_name=dataset_name,
    )
    try:
        updates_dict = _model_to_dict(updates)
    except TypeError:
        updates_dict = updates
    return json.dumps({"data": updates_dict}, ensure_ascii=False, indent=2)


@inject_yaml_instructions("check_api_key_status", "prompts")
@with_tool_instructions("check_api_key_status")
@mcp.tool()
@mcp_error_handler(tool_name="check_api_key_status")
async def check_api_key_status() -> str:
    """
    Check the API key configuration status and usage.

    Verifies whether an API key is configured and provides guidance on
    rate limits and best practices for API usage.

    Returns:
        JSON object with:
        - data: API key status, configuration guidance, and rate limit info

    Next Steps:
        - Review the API key status and rate limit guidance provided
        - Set or rotate SEMANTIC_SCHOLAR_API_KEY if configuration is missing
        - Ask for usage recommendations or next steps after updating credentials
    """
    import json
    import os

    from core.config import get_config

    # Check environment variable
    api_key_env = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

    # Get configuration
    config = get_config()
    api_key_configured = bool(config.semantic_scholar.api_key)

    # Get API client configuration
    # Note: Free tier API keys have 1 req/s limit (same as anonymous)
    # Premium API keys would have higher limits (e.g., 100 req/s)
    rate_limit_info = {
        "requests_per_second": 1,  # Free tier and anonymous both have 1 req/s
        "daily_limit": (
            "Unlimited (1 req/s)" if api_key_configured else "5,000 requests"
        ),
        "mode": ("authenticated (free tier)" if api_key_configured else "anonymous"),
    }

    # Check actual API key value (masked)
    api_key_preview = None
    if api_key_configured and config.semantic_scholar.api_key:
        # Show first 4 and last 4 characters only
        # Get the actual string value from SecretStr
        key_value = config.semantic_scholar.api_key.get_secret_value()
        if len(key_value) > 10:
            api_key_preview = f"{key_value[:4]}...{key_value[-4:]}"
        else:
            api_key_preview = "***SET***"

    payload = {
        "api_key_configured": api_key_configured,
        "api_key_source": "environment_variable" if api_key_env else "not_set",
        "api_key_preview": api_key_preview,
        "rate_limits": rate_limit_info,
        "benefits_with_key": [
            "No daily request limit (unlimited requests at 1 req/s)",
            "More stable service (authenticated requests)",
            "Access to all endpoints",
            "Required for production applications",
        ],
        "current_status": (
            "API key is configured ✓"
            if api_key_configured
            else "No API key configured (using anonymous mode)"
        ),
        "recommendation": (
            None
            if api_key_configured
            else "Consider adding SEMANTIC_SCHOLAR_API_KEY for better performance"
        ),
    }

    return json.dumps({"success": True, "data": payload}, ensure_ascii=False, indent=2)


_UNUSED_INSTRUCTION_KEYS = TOOL_INSTRUCTION_KEYS - REGISTERED_TOOL_NAMES
if _UNUSED_INSTRUCTION_KEYS:
    raise ValueError(
        "TOOL_INSTRUCTIONS contains keys that do not correspond to registered tools: "
        + ", ".join(sorted(_UNUSED_INSTRUCTION_KEYS))
    )

_MISSING_INSTRUCTION_KEYS = REGISTERED_TOOL_NAMES - TOOL_INSTRUCTION_KEYS
if _MISSING_INSTRUCTION_KEYS:
    logger.warning(
        "Missing explicit tool instructions; default instructions will be used",
        tools=sorted(_MISSING_INSTRUCTION_KEYS),
    )


# Resource implementations


@mcp.resource("papers/{paper_id}")
async def get_paper_resource(paper_id: str) -> str:
    """
    Get paper information as a resource.

    Args:
        paper_id: Paper ID

    Returns:
        Formatted paper information
    """
    paper = await _call_client_method("get_paper", paper_id=paper_id)

    # Format paper as markdown
    lines = [
        f"# {paper.title}",
        "",
        f"**Authors**: {', '.join([a.name for a in paper.authors])}",
        f"**Year**: {paper.year}",
        f"**Venue**: {paper.venue or 'N/A'}",
        f"**Citations**: {paper.citation_count}",
        "",
        "## Abstract",
        paper.abstract or "No abstract available.",
        "",
    ]

    if paper.url:
        lines.append(f"**URL**: {paper.url}")

    return "\n".join(lines)


@mcp.resource("authors/{author_id}")
async def get_author_resource(author_id: str) -> str:
    """
    Get author information as a resource.

    Args:
        author_id: Author ID

    Returns:
        Formatted author information
    """
    author = await _call_client_method("get_author", author_id=author_id)

    # Format author as markdown
    lines = [
        f"# {author.name}",
        "",
        f"**H-Index**: {author.h_index or 'N/A'}",
        f"**Citation Count**: {author.citation_count or 0}",
        f"**Paper Count**: {author.paper_count or 0}",
        "",
    ]

    if author.affiliations:
        lines.append(f"**Affiliations**: {', '.join(author.affiliations)}")

    if author.homepage:
        lines.append(f"**Homepage**: {author.homepage}")

    return "\n".join(lines)


# Prompt implementations


@mcp.prompt()
def literature_review(
    topic: str,
    max_papers: int = Field(default=20, ge=5, le=50),
    start_year: int | None = Field(default=None),
) -> str:
    """
    Generate a literature review prompt for a given topic.

    Args:
        topic: Research topic
        max_papers: Maximum number of papers to include
        start_year: Starting year for paper search

    Returns:
        Prompt text for literature review
    """
    year_filter = f" published after {start_year}" if start_year else ""

    return f"""Please help me create a comprehensive literature review on the topic: \
"{topic}"

Instructions:
1. Search for the most relevant and highly-cited papers on this topic{year_filter}
2. Retrieve up to {max_papers} papers
3. For each paper, analyze:
   - Main contributions and findings
   - Methodology used
   - Limitations and future work
4. Identify common themes and research gaps
5. Organize the review by subtopics or chronologically
6. Include proper citations for all papers

Please structure the review with:
- Introduction to the topic
- Methodology (how papers were selected)
- Main body organized by themes
- Summary of findings
- Research gaps and future directions
- References list"""


@mcp.prompt()
def citation_analysis(paper_id: str, depth: int = Field(default=1, ge=1, le=3)) -> str:
    """
    Generate a citation analysis prompt for a paper.

    Args:
        paper_id: Paper ID to analyze
        depth: Depth of citation analysis (1-3)

    Returns:
        Prompt text for citation analysis
    """
    return f"""Please perform a comprehensive citation analysis for paper ID: {paper_id}

Analysis depth: {depth} levels

Instructions:
1. Retrieve the main paper and its metadata
2. Analyze citations at depth {depth}:
   - Level 1: Direct citations (papers citing the main paper)
   - Level 2: Citations of citations (if depth >= 2)
   - Level 3: Third-level citations (if depth = 3)

For each level, analyze:
- Most influential citing papers (by citation count)
- Common themes in citing papers
- How the original paper is used/referenced
- Evolution of the research area
- Identify key research groups or authors

Please provide:
- Citation statistics and trends
- Network visualization description
- Key insights about the paper's impact
- Recommendations for related work"""


@mcp.prompt()
def research_trend_analysis(
    field: str, years: int = Field(default=5, ge=1, le=20)
) -> str:
    """
    Generate a research trend analysis prompt.

    Args:
        field: Research field to analyze
        years: Number of years to analyze

    Returns:
        Prompt text for trend analysis
    """
    return f"""Please analyze research trends in the field of "{field}" over the \
past {years} years.

Instructions:
1. Search for papers in this field from the last {years} years
2. Group papers by year and identify:
   - Publication volume trends
   - Most cited papers per year
   - Emerging topics and keywords
   - Declining research areas

3. Analyze:
   - Top contributing authors and institutions
   - International collaboration patterns
   - Funding sources (if available)
   - Industry vs academic contributions

4. Identify:
   - Breakthrough papers and why they're significant
   - Methodology shifts
   - Technology adoption
   - Interdisciplinary connections

Please provide:
- Executive summary of trends
- Detailed year-by-year analysis
- Future research predictions
- Recommendations for researchers entering the field"""


# Server lifecycle


async def on_startup():
    """Initialize server on startup."""
    logger.debug_mcp("MCP server startup initiated")
    await initialize_server()
    logger.debug_mcp("MCP server startup completed")


async def on_shutdown():
    """Cleanup on shutdown."""
    logger.debug_mcp("MCP server shutdown initiated")
    logger.info("Semantic Scholar MCP server shutting down")
    logger.debug_mcp("MCP server shutdown completed")


# Main entry point
def main():
    """Main entry point for the server."""

    # Initialize server first
    logger.debug_mcp("Initializing MCP server")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_server())

    # Log environment information if debug mode is enabled
    if os.getenv("DEBUG_MCP_MODE", "false").lower() == "true":
        temp_logger = get_logger("mcp.main")
        temp_logger.debug_mcp(
            "MCP server main() called",
            environment_vars={
                "DEBUG_MCP_MODE": os.getenv("DEBUG_MCP_MODE"),
                "LOG_MCP_MESSAGES": os.getenv("LOG_MCP_MESSAGES"),
                "LOG_API_PAYLOADS": os.getenv("LOG_API_PAYLOADS"),
                "LOG_PERFORMANCE_METRICS": os.getenv("LOG_PERFORMANCE_METRICS"),
                "MCP_MODE": os.getenv("MCP_MODE"),
                "SEMANTIC_SCHOLAR_API_KEY": "***SET***"
                if os.getenv("SEMANTIC_SCHOLAR_API_KEY")
                else "***NOT_SET***",
            },
            python_version=sys.version,
            working_directory=str(Path.cwd()),
        )

    # Start Dashboard if enabled
    global dashboard_thread, dashboard_port
    try:
        if dashboard_api and config and config.dashboard.enabled:
            dashboard_thread, dashboard_port = dashboard_api.run_in_thread(
                host=config.dashboard.host,
                port=config.dashboard.port,
            )
            logger.info(
                f"Dashboard started at http://{config.dashboard.host}:{dashboard_port}/dashboard/"
            )
            if config.dashboard.open_on_launch:
                browser_host = config.dashboard.host
                if browser_host in {"0.0.0.0", "::"}:  # noqa: S104
                    browser_host = "127.0.0.1"
                dashboard_url = f"http://{browser_host}:{dashboard_port}/dashboard/"
                _launch_dashboard_browser(dashboard_url)
                logger.info("Opening dashboard in default browser", url=dashboard_url)
    except Exception as e:
        logger.error(f"Failed to start Dashboard: {e}")

    # Run the server
    try:
        logger.debug_mcp("Starting FastMCP server with stdio transport")
        # FastMCP handles the async event loop internally
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.debug_mcp("MCP server interrupted by user")
        logger.info("Semantic Scholar MCP server shutting down")
    except Exception as e:
        logger.log_with_stack_trace(
            logging.ERROR,
            "Fatal error running MCP server",
            exception=e,
            transport="stdio",
        )
        raise
    finally:
        logger.debug_mcp("MCP server shutdown completed")


# Export app for testing
app = mcp


# Export app for testing
app = mcp


if __name__ == "__main__":
    main()
