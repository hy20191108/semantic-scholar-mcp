"""Dashboard statistics collection and management."""

import threading
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DashboardStats:
    """
    Statistics collector for Dashboard analytics.

    Tracks tool usage, API calls, cache performance, and search analytics
    for real-time monitoring and historical analysis.
    """

    # Tool usage metrics
    tool_calls: Counter[str] = field(default_factory=Counter)
    tool_times: dict[str, list[float]] = field(default_factory=dict)
    tool_errors: Counter[str] = field(default_factory=Counter)

    # Cache performance
    cache_hits: int = 0
    cache_misses: int = 0

    # Search analytics (semantic-scholar specific)
    search_queries: Counter[str] = field(default_factory=Counter)
    accessed_papers: Counter[str] = field(default_factory=Counter)
    fields_of_study: Counter[str] = field(default_factory=Counter)

    # API call timeline (last 1000 calls)
    api_calls_timeline: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=1000)
    )

    # PDF processing metrics
    pdf_conversions: int = 0
    pdf_cache_hits: int = 0

    # API health metrics
    rate_limit_warnings: int = 0
    circuit_breaker_trips: int = 0

    # Server metrics
    start_time: float = field(default_factory=time.time)

    # Thread safety
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_tool_call(
        self, tool_name: str, duration: float, success: bool = True
    ) -> None:
        """Record a tool invocation with timing and result."""
        with self._lock:
            self.tool_calls[tool_name] += 1
            if tool_name not in self.tool_times:
                self.tool_times[tool_name] = []
            self.tool_times[tool_name].append(duration)

            if not success:
                self.tool_errors[tool_name] += 1

            # Record in timeline
            self.api_calls_timeline.append(
                {
                    "timestamp": time.time(),
                    "tool": tool_name,
                    "duration": duration,
                    "success": success,
                }
            )

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        with self._lock:
            self.cache_misses += 1

    def record_search_query(self, query: str) -> None:
        """Record a search query for analytics."""
        with self._lock:
            self.search_queries[query] += 1

    def record_paper_access(self, paper_id: str) -> None:
        """Record paper access for trending analysis."""
        with self._lock:
            self.accessed_papers[paper_id] += 1

    def record_field_of_study(self, field: str) -> None:
        """Record field of study for distribution analysis."""
        with self._lock:
            self.fields_of_study[field] += 1

    def record_pdf_conversion(self, from_cache: bool = False) -> None:
        """Record PDF to markdown conversion."""
        with self._lock:
            self.pdf_conversions += 1
            if from_cache:
                self.pdf_cache_hits += 1

    def record_rate_limit_warning(self) -> None:
        """Record rate limit warning event."""
        with self._lock:
            self.rate_limit_warnings += 1

    def record_circuit_breaker_trip(self) -> None:
        """Record circuit breaker trip event."""
        with self._lock:
            self.circuit_breaker_trips += 1

    def get_uptime(self) -> float:
        """Get server uptime in seconds."""
        return time.time() - self.start_time

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        with self._lock:
            total = self.cache_hits + self.cache_misses
            if total == 0:
                return 0.0
            return (self.cache_hits / total) * 100

    def get_pdf_cache_hit_rate(self) -> float:
        """Calculate PDF cache hit rate percentage."""
        with self._lock:
            if self.pdf_conversions == 0:
                return 0.0
            return (self.pdf_cache_hits / self.pdf_conversions) * 100

    def get_tool_stats(self) -> dict[str, Any]:
        """Get comprehensive tool usage statistics."""
        with self._lock:
            stats = {}
            for tool_name in self.tool_calls:
                call_count = self.tool_calls[tool_name]
                error_count = self.tool_errors.get(tool_name, 0)
                times = self.tool_times.get(tool_name, [])

                stats[tool_name] = {
                    "calls": call_count,
                    "errors": error_count,
                    "success_rate": (
                        ((call_count - error_count) / call_count * 100)
                        if call_count > 0
                        else 0.0
                    ),
                    "avg_time": sum(times) / len(times) if times else 0.0,
                    "min_time": min(times) if times else 0.0,
                    "max_time": max(times) if times else 0.0,
                }
            return stats

    def get_top_queries(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most popular search queries."""
        with self._lock:
            return self.search_queries.most_common(limit)

    def get_top_papers(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most accessed papers."""
        with self._lock:
            return self.accessed_papers.most_common(limit)

    def get_field_distribution(self) -> dict[str, int]:
        """Get field of study distribution."""
        with self._lock:
            return dict(self.fields_of_study)

    def get_timeline_data(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent API call timeline."""
        with self._lock:
            # Return last N items from deque
            timeline = list(self.api_calls_timeline)
            return timeline[-limit:] if len(timeline) > limit else timeline

    def clear_stats(self) -> None:
        """Clear all statistics (for testing or reset)."""
        with self._lock:
            self.tool_calls.clear()
            self.tool_times.clear()
            self.tool_errors.clear()
            self.cache_hits = 0
            self.cache_misses = 0
            self.search_queries.clear()
            self.accessed_papers.clear()
            self.fields_of_study.clear()
            self.api_calls_timeline.clear()
            self.pdf_conversions = 0
            self.pdf_cache_hits = 0
            self.rate_limit_warnings = 0
            self.circuit_breaker_trips = 0
            # Don't reset start_time to preserve uptime

    def get_summary(self) -> dict[str, Any]:
        """Get complete statistics summary."""
        with self._lock:
            return {
                "uptime_seconds": self.get_uptime(),
                "total_tool_calls": sum(self.tool_calls.values()),
                "total_errors": sum(self.tool_errors.values()),
                "cache_hit_rate": self.get_cache_hit_rate(),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "pdf_conversions": self.pdf_conversions,
                "pdf_cache_hit_rate": self.get_pdf_cache_hit_rate(),
                "rate_limit_warnings": self.rate_limit_warnings,
                "circuit_breaker_trips": self.circuit_breaker_trips,
                "unique_tools_used": len(self.tool_calls),
                "unique_queries": len(self.search_queries),
                "unique_papers": len(self.accessed_papers),
                "fields_tracked": len(self.fields_of_study),
            }
