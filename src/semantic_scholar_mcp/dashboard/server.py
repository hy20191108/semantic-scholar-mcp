"""Dashboard Flask server with API endpoints."""

import logging as stdlib_logging
import socket
import threading
from pathlib import Path
from typing import Any

from flask import Flask, Response, request, send_from_directory
from pydantic import BaseModel

from semantic_scholar_mcp.dashboard.stats import DashboardStats

# Disable Flask/Werkzeug logging to avoid cluttering MCP output
stdlib_logging.getLogger("werkzeug").setLevel(stdlib_logging.WARNING)
logger = stdlib_logging.getLogger(__name__)

# Dashboard static files directory
DASHBOARD_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"


# Pydantic models for API requests/responses
class RequestLog(BaseModel):
    """Request model for log pagination."""

    start_idx: int = 0


class ResponseLog(BaseModel):
    """Response model for log messages."""

    messages: list[str]
    max_idx: int


class ResponseStats(BaseModel):
    """Response model for statistics summary."""

    summary: dict[str, Any]
    tool_stats: dict[str, Any]


class ResponseSearchAnalytics(BaseModel):
    """Response model for search analytics."""

    top_queries: list[tuple[str, int]]
    top_papers: list[tuple[str, int]]
    field_distribution: dict[str, int]


class ResponsePerformance(BaseModel):
    """Response model for performance metrics."""

    cache_hit_rate: float
    pdf_cache_hit_rate: float
    timeline: list[dict[str, Any]]


class DashboardAPI:
    """
    Flask-based Dashboard API server.

    Provides REST endpoints for monitoring MCP server health,
    tool usage, search analytics, and performance metrics.
    """

    def __init__(
        self,
        stats: DashboardStats,
        log_messages: list[str] | None = None,
    ) -> None:
        """
        Initialize Dashboard API.

        Args:
            stats: DashboardStats instance for data collection
            log_messages: Optional list of log messages for display
        """
        self.stats = stats
        self.log_messages = log_messages or []
        self._app = Flask(
            __name__,
            static_folder=str(DASHBOARD_DIR),
            template_folder=str(TEMPLATES_DIR),
        )
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Configure Flask routes."""

        # Serve static files
        @self._app.route("/dashboard/<path:filename>")
        def serve_static(filename: str) -> Response:
            return send_from_directory(DASHBOARD_DIR, filename)

        # Serve main HTML
        @self._app.route("/dashboard/")
        def serve_index() -> Response:
            return send_from_directory(TEMPLATES_DIR, "index.html")

        # API: Get log messages
        @self._app.route("/api/logs", methods=["POST"])
        def get_logs() -> dict[str, Any]:
            request_data = request.get_json()
            req = (
                RequestLog.model_validate(request_data)
                if request_data
                else RequestLog()
            )
            result = self._get_log_messages(req)
            return result.model_dump()

        # API: Get statistics summary
        @self._app.route("/api/stats", methods=["GET"])
        def get_stats() -> dict[str, Any]:
            result = self._get_stats()
            return result.model_dump()

        # API: Get search analytics
        @self._app.route("/api/analytics", methods=["GET"])
        def get_analytics() -> dict[str, Any]:
            result = self._get_search_analytics()
            return result.model_dump()

        # API: Get performance metrics
        @self._app.route("/api/performance", methods=["GET"])
        def get_performance() -> dict[str, Any]:
            result = self._get_performance()
            return result.model_dump()

        # API: Clear statistics
        @self._app.route("/api/stats/clear", methods=["POST"])
        def clear_stats() -> dict[str, str]:
            self.stats.clear_stats()
            return {"status": "cleared"}

        # API: Health check
        @self._app.route("/api/health", methods=["GET"])
        def health_check() -> dict[str, Any]:
            return {
                "status": "healthy",
                "uptime": self.stats.get_uptime(),
                "total_calls": sum(self.stats.tool_calls.values()),
            }

    def _get_log_messages(self, req: RequestLog) -> ResponseLog:
        """Get paginated log messages."""
        all_messages = self.log_messages
        requested_messages = (
            all_messages[req.start_idx :] if req.start_idx <= len(all_messages) else []
        )
        max_idx = len(all_messages) - 1 if all_messages else 0
        return ResponseLog(messages=requested_messages, max_idx=max_idx)

    def _get_stats(self) -> ResponseStats:
        """Get comprehensive statistics."""
        summary = self.stats.get_summary()
        tool_stats = self.stats.get_tool_stats()
        return ResponseStats(summary=summary, tool_stats=tool_stats)

    def _get_search_analytics(self) -> ResponseSearchAnalytics:
        """Get search analytics data."""
        top_queries = self.stats.get_top_queries(limit=10)
        top_papers = self.stats.get_top_papers(limit=10)
        field_dist = self.stats.get_field_distribution()
        return ResponseSearchAnalytics(
            top_queries=top_queries,
            top_papers=top_papers,
            field_distribution=field_dist,
        )

    def _get_performance(self) -> ResponsePerformance:
        """Get performance metrics."""
        cache_rate = self.stats.get_cache_hit_rate()
        pdf_cache_rate = self.stats.get_pdf_cache_hit_rate()
        timeline = self.stats.get_timeline_data(limit=100)
        return ResponsePerformance(
            cache_hit_rate=cache_rate,
            pdf_cache_hit_rate=pdf_cache_rate,
            timeline=timeline,
        )

    @staticmethod
    def _find_first_free_port(start_port: int) -> int:
        """Find first available port starting from start_port (Serena-style)."""
        port = start_port
        while port <= 65535:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(("127.0.0.1", port))
                    return port
            except OSError:
                port += 1

        raise RuntimeError(f"No free ports found starting from {start_port}")

    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 0x5EDA,
    ) -> int:
        """
        Run Flask dashboard server.

        Args:
            host: Host to bind to (default: 127.0.0.1)
            port: Port to bind to (default: 0x5EDA = 24282)

        Returns:
            Port number the server is running on
        """
        # Suppress Flask's startup banner
        from flask import cli

        cli.show_server_banner = lambda *args, **kwargs: None  # noqa: ARG005

        self._app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
        )
        return port

    def run_in_thread(
        self,
        host: str = "127.0.0.1",
        port: int | None = None,
    ) -> tuple[threading.Thread, int]:
        """
        Run Dashboard in background thread.

        Args:
            host: Preferred bind address for the dashboard.
            port: Preferred port (ignored, for compatibility only).

        Returns:
            Tuple of (thread, port_number)

        Note:
            Following Serena's simple and reliable approach:
            Always finds first free port starting from default (0x5EDA = 24282).
            Configuration port is ignored to ensure dashboard always starts
            successfully.
        """
        # Always find free port, Serena-style (simple and reliable)
        chosen_port = self._find_first_free_port(0x5EDA)
        thread = threading.Thread(
            target=lambda: self.run(host=host, port=chosen_port),
            daemon=True,
        )
        thread.start()
        return thread, chosen_port
