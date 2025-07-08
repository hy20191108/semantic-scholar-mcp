"""Metrics collection and monitoring infrastructure.

This module provides comprehensive metrics collection with support for
multiple backends including Prometheus, StatsD, and DataDog.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any

from .abstractions import IMetricsCollector
from .config import MetricsConfig
from .types import MetricName


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Represents a metric value with metadata."""

    name: str
    value: float
    metric_type: MetricType
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit,
            "description": self.description
        }


class MetricBackend(ABC):
    """Abstract base class for metric backends."""

    @abstractmethod
    def record_counter(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record counter metric."""

    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record gauge metric."""

    @abstractmethod
    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record histogram metric."""

    @abstractmethod
    def flush(self) -> None:
        """Flush any buffered metrics."""


class InMemoryBackend(MetricBackend):
    """In-memory metric backend for testing and development."""

    def __init__(self) -> None:
        """Initialize in-memory backend."""
        self._metrics: dict[str, list[MetricValue]] = defaultdict(list)
        self._lock = Lock()

    def record_counter(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record counter metric."""
        with self._lock:
            self._metrics[name].append(
                MetricValue(name, value, MetricType.COUNTER, tags or {})
            )

    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record gauge metric."""
        with self._lock:
            self._metrics[name].append(
                MetricValue(name, value, MetricType.GAUGE, tags or {})
            )

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record histogram metric."""
        with self._lock:
            self._metrics[name].append(
                MetricValue(name, value, MetricType.HISTOGRAM, tags or {})
            )

    def flush(self) -> None:
        """No-op for in-memory backend."""

    def get_metrics(self) -> dict[str, list[MetricValue]]:
        """Get all recorded metrics."""
        with self._lock:
            return dict(self._metrics)

    def clear(self) -> None:
        """Clear all metrics."""
        with self._lock:
            self._metrics.clear()


class PrometheusBackend(MetricBackend):
    """Prometheus metric backend."""

    def __init__(self, config: MetricsConfig) -> None:
        """Initialize Prometheus backend."""
        self.config = config
        self._counters: dict[str, Any] = {}
        self._gauges: dict[str, Any] = {}
        self._histograms: dict[str, Any] = {}
        self._lock = Lock()

        # Import prometheus_client dynamically
        try:
            import prometheus_client
            self.prometheus = prometheus_client
            self._initialize_metrics()
        except ImportError:
            raise ImportError("prometheus_client is required for Prometheus backend")

    def record_counter(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record counter metric."""
        with self._lock:
            counter = self._get_or_create_counter(name, tags)
            counter.inc(value)

    def record_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record gauge metric."""
        with self._lock:
            gauge = self._get_or_create_gauge(name, tags)
            gauge.set(value)

    def record_histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record histogram metric."""
        with self._lock:
            histogram = self._get_or_create_histogram(name, tags)
            histogram.observe(value)

    def flush(self) -> None:
        """No-op for Prometheus (pull-based)."""

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # Start HTTP server for metrics endpoint
        if self.config.export_endpoint:
            port = int(self.config.export_endpoint.split(":")[-1])
            self.prometheus.start_http_server(port)

    def _get_or_create_counter(self, name: str, tags: dict[str, str] | None) -> Any:
        """Get or create counter metric."""
        if name not in self._counters:
            label_names = list(tags.keys()) if tags else []
            self._counters[name] = self.prometheus.Counter(
                name.replace(".", "_"),
                f"Counter for {name}",
                label_names
            )

        counter = self._counters[name]
        if tags:
            return counter.labels(**tags)
        return counter

    def _get_or_create_gauge(self, name: str, tags: dict[str, str] | None) -> Any:
        """Get or create gauge metric."""
        if name not in self._gauges:
            label_names = list(tags.keys()) if tags else []
            self._gauges[name] = self.prometheus.Gauge(
                name.replace(".", "_"),
                f"Gauge for {name}",
                label_names
            )

        gauge = self._gauges[name]
        if tags:
            return gauge.labels(**tags)
        return gauge

    def _get_or_create_histogram(self, name: str, tags: dict[str, str] | None) -> Any:
        """Get or create histogram metric."""
        if name not in self._histograms:
            label_names = list(tags.keys()) if tags else []
            self._histograms[name] = self.prometheus.Histogram(
                name.replace(".", "_"),
                f"Histogram for {name}",
                label_names,
                buckets=self.config.histogram_buckets
            )

        histogram = self._histograms[name]
        if tags:
            return histogram.labels(**tags)
        return histogram


class MetricsCollector(IMetricsCollector):
    """Main metrics collector implementation."""

    def __init__(self, config: MetricsConfig) -> None:
        """Initialize metrics collector."""
        self.config = config
        self._backend = self._create_backend()
        self._global_tags: dict[str, str] = {}
        self._lock = Lock()

        # Metric registry for tracking
        self._metric_registry: dict[str, MetricValue] = {}

        # Performance tracking
        self._timers: dict[str, float] = {}

    def increment(self, metric: MetricName, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        if not self.config.enabled:
            return

        merged_tags = self._merge_tags(tags)
        self._backend.record_counter(metric, float(value), merged_tags)

        # Track in registry
        self._update_registry(metric, float(value), MetricType.COUNTER, merged_tags)

    def gauge(self, metric: MetricName, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge metric."""
        if not self.config.enabled:
            return

        merged_tags = self._merge_tags(tags)
        self._backend.record_gauge(metric, value, merged_tags)

        # Track in registry
        self._update_registry(metric, value, MetricType.GAUGE, merged_tags)

    def histogram(self, metric: MetricName, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram metric."""
        if not self.config.enabled:
            return

        merged_tags = self._merge_tags(tags)
        self._backend.record_histogram(metric, value, merged_tags)

        # Track in registry
        self._update_registry(metric, value, MetricType.HISTOGRAM, merged_tags)

    @asynccontextmanager
    async def timer(self, metric: MetricName, tags: dict[str, str] | None = None):
        """Context manager for timing operations."""
        if not self.config.enabled:
            yield
            return

        start_time = time.time()
        timer_id = f"{metric}:{id(tags)}"

        try:
            with self._lock:
                self._timers[timer_id] = start_time
            yield
        finally:
            duration = time.time() - start_time
            with self._lock:
                self._timers.pop(timer_id, None)

            # Record duration as histogram
            self.histogram(f"{metric}.duration", duration, tags)

            # Also record as counter for rate calculation
            self.increment(f"{metric}.count", 1, tags)

    def set_global_tags(self, tags: dict[str, str]) -> None:
        """Set global tags for all metrics."""
        with self._lock:
            self._global_tags.update(tags)

    def flush(self) -> None:
        """Flush metrics to backend."""
        self._backend.flush()

    def get_registry(self) -> dict[str, MetricValue]:
        """Get current metric registry."""
        with self._lock:
            return dict(self._metric_registry)

    def _create_backend(self) -> MetricBackend:
        """Create metric backend based on configuration."""
        if self.config.backend == "prometheus":
            return PrometheusBackend(self.config)
        if self.config.backend == "none" or not self.config.enabled:
            return InMemoryBackend()
        # Default to in-memory for unsupported backends
        return InMemoryBackend()

    def _merge_tags(self, tags: dict[str, str] | None) -> dict[str, str]:
        """Merge tags with global tags."""
        merged = self._global_tags.copy()
        if tags:
            merged.update(tags)
        return merged if self.config.include_labels else {}

    def _update_registry(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: dict[str, str]
    ) -> None:
        """Update metric registry."""
        with self._lock:
            registry_key = f"{name}:{','.join(f'{k}={v}' for k, v in sorted(tags.items()))}"
            self._metric_registry[registry_key] = MetricValue(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags
            )


class MetricAggregator:
    """Aggregates metrics for analysis."""

    def __init__(self) -> None:
        """Initialize metric aggregator."""
        self._metrics: list[MetricValue] = []
        self._lock = Lock()

    def add_metric(self, metric: MetricValue) -> None:
        """Add metric to aggregator."""
        with self._lock:
            self._metrics.append(metric)

    def get_metrics(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        tags: dict[str, str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> list[MetricValue]:
        """Get filtered metrics."""
        with self._lock:
            metrics = self._metrics

            if name:
                metrics = [m for m in metrics if m.name == name]
            if metric_type:
                metrics = [m for m in metrics if m.metric_type == metric_type]
            if tags:
                metrics = [
                    m for m in metrics
                    if all(m.tags.get(k) == v for k, v in tags.items())
                ]
            if start_time:
                metrics = [m for m in metrics if m.timestamp >= start_time]
            if end_time:
                metrics = [m for m in metrics if m.timestamp <= end_time]

            return metrics

    def get_statistics(self, name: str) -> dict[str, Any]:
        """Get statistics for a metric."""
        metrics = self.get_metrics(name=name)
        if not metrics:
            return {}

        values = [m.value for m in metrics]

        return {
            "count": len(values),
            "sum": sum(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": metrics[-1].value,
            "first_seen": metrics[0].timestamp.isoformat(),
            "last_seen": metrics[-1].timestamp.isoformat()
        }


class HealthCheck:
    """Health check system with metrics."""

    def __init__(self, metrics: IMetricsCollector) -> None:
        """Initialize health check."""
        self.metrics = metrics
        self._checks: dict[str, Callable[[], dict[str, Any]]] = {}
        self._lock = Lock()

    def register_check(self, name: str, check: Callable[[], dict[str, Any]]) -> None:
        """Register a health check."""
        with self._lock:
            self._checks[name] = check

    async def check_health(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        overall_healthy = True

        for name, check in self._checks.items():
            try:
                start_time = time.time()
                result = await asyncio.create_task(asyncio.to_thread(check))
                duration = time.time() - start_time

                # Record metrics
                self.metrics.histogram(
                    "health_check.duration",
                    duration,
                    {"check": name}
                )

                if result.get("status") != "healthy":
                    overall_healthy = False
                    self.metrics.increment(
                        "health_check.failure",
                        tags={"check": name}
                    )
                else:
                    self.metrics.increment(
                        "health_check.success",
                        tags={"check": name}
                    )

                results["checks"][name] = result

            except Exception as e:
                overall_healthy = False
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                self.metrics.increment(
                    "health_check.error",
                    tags={"check": name, "error": type(e).__name__}
                )

        results["status"] = "healthy" if overall_healthy else "unhealthy"
        return results


class MetricsMiddleware:
    """Middleware for request metrics."""

    def __init__(self, metrics: IMetricsCollector) -> None:
        """Initialize metrics middleware."""
        self.metrics = metrics

    async def __call__(self, request: Any, call_next: Callable) -> Any:
        """Process request with metrics."""
        # Extract metadata
        method = getattr(request, "method", "UNKNOWN")
        path = getattr(request, "path", "UNKNOWN")

        # Start timer
        start_time = time.time()

        # Track active requests
        self.metrics.increment("http.requests.active", tags={"method": method})

        try:
            # Process request
            response = await call_next(request)

            # Record metrics
            duration = time.time() - start_time
            status = getattr(response, "status_code", 0)

            tags = {
                "method": method,
                "path": path,
                "status": str(status),
                "status_class": f"{status // 100}xx"
            }

            self.metrics.histogram("http.request.duration", duration, tags)
            self.metrics.increment("http.requests.total", tags=tags)

            # Track response size if available
            if hasattr(response, "headers") and "content-length" in response.headers:
                size = int(response.headers["content-length"])
                self.metrics.histogram("http.response.size", size, tags)

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time

            tags = {
                "method": method,
                "path": path,
                "error": type(e).__name__
            }

            self.metrics.histogram("http.request.duration", duration, tags)
            self.metrics.increment("http.requests.errors", tags=tags)

            raise

        finally:
            # Decrement active requests
            self.metrics.increment("http.requests.active", value=-1, tags={"method": method})


# Decorators for method-level metrics
def track_performance(metric_name: str | None = None):
    """Decorator to track method performance."""
    def decorator(func: Callable) -> Callable:
        name = metric_name or f"{func.__module__}.{func.__name__}"

        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get metrics collector from first argument if it has one
            metrics = None
            if args and hasattr(args[0], "metrics"):
                metrics = args[0].metrics

            if metrics:
                async with metrics.timer(name):
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)

        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get metrics collector from first argument if it has one
            metrics = None
            if args and hasattr(args[0], "metrics"):
                metrics = args[0].metrics

            if metrics:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    metrics.histogram(f"{name}.duration", duration)
                    metrics.increment(f"{name}.count")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    metrics.histogram(f"{name}.duration", duration, {"error": type(e).__name__})
                    metrics.increment(f"{name}.errors", tags={"error": type(e).__name__})
                    raise
            else:
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
