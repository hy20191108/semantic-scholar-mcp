"""Comprehensive metrics collection and monitoring system."""

import asyncio
import time
from collections import defaultdict, deque
from typing import Any

from .interfaces import IMetricsCollector
from .logging import get_logger

logger = get_logger(__name__)


class MetricsCollector(IMetricsCollector):
    """Comprehensive metrics collector with real-time monitoring."""

    def __init__(self, max_history: int = 1000, enabled: bool = True):
        """Initialize metrics collector.

        Args:
            max_history: Maximum number of historical data points to keep
            enabled: Whether metrics collection is enabled
        """
        self.max_history = max_history
        self.enabled = enabled
        self._metrics: dict[str, Any] = {
            "counters": defaultdict(int),
            "gauges": defaultdict(float),
            "histograms": defaultdict(lambda: deque(maxlen=max_history)),
            "timers": defaultdict(lambda: deque(maxlen=max_history)),
            "rates": defaultdict(lambda: {"count": 0, "window_start": time.time()}),
            "errors": defaultdict(
                lambda: {
                    "count": 0,
                    "last_error": None,
                    "error_types": defaultdict(int),
                }
            ),
        }
        self._lock = asyncio.Lock()

    def increment(
        self, name: str, value: float = 1.0, tags: dict[str, str] | None = None
    ) -> None:
        """Increment counter metric."""
        if not self.enabled:
            return

        key = self._make_key(name, tags)
        self._metrics["counters"][key] += value

    def gauge(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Set gauge metric."""
        if not self.enabled:
            return

        key = self._make_key(name, tags)
        self._metrics["gauges"][key] = value

    def histogram(
        self, name: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record histogram metric."""
        if not self.enabled:
            return

        key = self._make_key(name, tags)
        self._metrics["histograms"][key].append(
            {
                "value": value,
                "timestamp": time.time(),
            }
        )

    async def increment_counter(
        self, name: str, value: int = 1, labels: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric."""
        self.increment(name, float(value), labels)

    async def set_gauge(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric."""
        self.gauge(name, value, labels)

    async def record_histogram(
        self, name: str, value: float, labels: dict[str, str] | None = None
    ) -> None:
        """Record a histogram value."""
        self.histogram(name, value, labels)

    async def record_timer(
        self, name: str, duration: float, labels: dict[str, str] | None = None
    ) -> None:
        """Record a timer value."""
        if not self.enabled:
            return

        async with self._lock:
            key = self._make_key(name, labels)
            self._metrics["timers"][key].append(
                {
                    "duration": duration,
                    "timestamp": time.time(),
                }
            )

    async def record_rate(
        self, name: str, labels: dict[str, str] | None = None
    ) -> None:
        """Record a rate metric."""
        if not self.enabled:
            return

        async with self._lock:
            key = self._make_key(name, labels)
            current_time = time.time()
            rate_data = self._metrics["rates"][key]

            # Reset window if more than 60 seconds have passed
            if current_time - rate_data["window_start"] > 60:
                rate_data["count"] = 0
                rate_data["window_start"] = current_time

            rate_data["count"] += 1

    async def record_error(
        self, name: str, error: Exception, labels: dict[str, str] | None = None
    ) -> None:
        """Record an error metric."""
        if not self.enabled:
            return

        async with self._lock:
            key = self._make_key(name, labels)
            error_data = self._metrics["errors"][key]

            error_data["count"] += 1
            error_data["last_error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "timestamp": time.time(),
            }
            error_data["error_types"][type(error).__name__] += 1

    def _make_key(self, name: str, labels: dict[str, str] | None = None) -> str:
        """Create a key for the metric."""
        if not labels:
            return name

        label_parts = [f"{k}={v}" for k, v in sorted(labels.items())]
        return f"{name}({','.join(label_parts)})"

    async def get_metrics(self) -> dict[str, Any]:
        """Get all metrics."""
        async with self._lock:
            return {
                "counters": dict(self._metrics["counters"]),
                "gauges": dict(self._metrics["gauges"]),
                "histograms": {
                    k: list(v) for k, v in self._metrics["histograms"].items()
                },
                "timers": {k: list(v) for k, v in self._metrics["timers"].items()},
                "rates": {k: dict(v) for k, v in self._metrics["rates"].items()},
                "errors": {k: dict(v) for k, v in self._metrics["errors"].items()},
            }

    async def get_summary(self) -> dict[str, Any]:
        """Get a summary of metrics."""
        async with self._lock:
            summary = {
                "total_counters": len(self._metrics["counters"]),
                "total_gauges": len(self._metrics["gauges"]),
                "total_histograms": len(self._metrics["histograms"]),
                "total_timers": len(self._metrics["timers"]),
                "total_rates": len(self._metrics["rates"]),
                "total_errors": len(self._metrics["errors"]),
            }

            # Add counter totals
            counter_total = sum(self._metrics["counters"].values())
            summary["counter_total"] = counter_total

            # Add error summaries
            total_errors = sum(
                data["count"] for data in self._metrics["errors"].values()
            )
            summary["error_total"] = total_errors

            # Add performance summaries
            if self._metrics["timers"]:
                all_durations = []
                for timer_data in self._metrics["timers"].values():
                    all_durations.extend([d["duration"] for d in timer_data])

                if all_durations:
                    summary["avg_duration"] = sum(all_durations) / len(all_durations)
                    summary["min_duration"] = min(all_durations)
                    summary["max_duration"] = max(all_durations)

            return summary

    async def reset_metrics(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self._metrics = {
                "counters": defaultdict(int),
                "gauges": defaultdict(float),
                "histograms": defaultdict(lambda: deque(maxlen=self.max_history)),
                "timers": defaultdict(lambda: deque(maxlen=self.max_history)),
                "rates": defaultdict(lambda: {"count": 0, "window_start": time.time()}),
                "errors": defaultdict(
                    lambda: {
                        "count": 0,
                        "last_error": None,
                        "error_types": defaultdict(int),
                    }
                ),
            }

    async def get_health_status(self) -> dict[str, Any]:
        """Get health status based on metrics."""
        async with self._lock:
            current_time = time.time()

            # Check error rates
            recent_errors = 0
            for error_data in self._metrics["errors"].values():
                if (
                    error_data["last_error"]
                    and current_time - error_data["last_error"]["timestamp"] < 300
                ):  # 5 minutes
                    recent_errors += 1

            # Check response times
            slow_responses = 0
            if self._metrics["timers"]:
                for timer_data in self._metrics["timers"].values():
                    for timing in timer_data:
                        if (
                            current_time - timing["timestamp"] < 300
                            and timing["duration"] > 5.0
                        ):  # 5 seconds
                            slow_responses += 1

            # Determine health status
            if recent_errors > 10 or slow_responses > 5:
                status = "unhealthy"
            elif recent_errors > 5 or slow_responses > 2:
                status = "degraded"
            else:
                status = "healthy"

            return {
                "status": status,
                "recent_errors": recent_errors,
                "slow_responses": slow_responses,
                "timestamp": current_time,
            }


# Global metrics collector instance
_global_metrics_collector: MetricsCollector | None = None


def get_global_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector.

    Returns:
        Global metrics collector instance
    """
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = MetricsCollector()
    return _global_metrics_collector


def set_global_metrics_collector(collector: MetricsCollector) -> None:
    """Set the global metrics collector.

    Args:
        collector: Metrics collector instance
    """
    global _global_metrics_collector
    _global_metrics_collector = collector


# Metrics collection decorators
def collect_metrics(
    counter_name: str | None = None,
    timer_name: str | None = None,
    error_name: str | None = None,
    labels: dict[str, str] | None = None,
):
    """Decorator to collect metrics for functions.

    Args:
        counter_name: Counter metric name
        timer_name: Timer metric name
        error_name: Error metric name
        labels: Labels for metrics

    Returns:
        Decorator function
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            collector = get_global_metrics_collector()

            # Increment counter
            if counter_name:
                await collector.increment_counter(counter_name, labels=labels)

            # Time the function
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                # Record timing
                if timer_name:
                    duration = time.time() - start_time
                    await collector.record_timer(timer_name, duration, labels=labels)

                return result
            except Exception as error:
                # Record error
                if error_name:
                    await collector.record_error(error_name, error, labels=labels)
                raise

        def sync_wrapper(*args, **kwargs):
            collector = get_global_metrics_collector()

            # Increment counter
            if counter_name:
                asyncio.create_task(
                    collector.increment_counter(counter_name, labels=labels)
                )

            # Time the function
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Record timing
                if timer_name:
                    duration = time.time() - start_time
                    asyncio.create_task(
                        collector.record_timer(timer_name, duration, labels=labels)
                    )

                return result
            except Exception as error:
                # Record error
                if error_name:
                    asyncio.create_task(
                        collector.record_error(error_name, error, labels=labels)
                    )
                raise

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class PerformanceMonitor:
    """Performance monitoring with thresholds and alerting."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize performance monitor.

        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics_collector = metrics_collector
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "error_rate": 0.05,  # 5%
            "memory_usage": 0.8,  # 80%
            "cpu_usage": 0.9,  # 90%
        }
        self.alerts = []

    async def check_thresholds(self) -> list[dict[str, Any]]:
        """Check performance thresholds and generate alerts.

        Returns:
            List of alerts
        """
        alerts = []
        metrics = await self.metrics_collector.get_metrics()

        # Check response time threshold
        if "timers" in metrics:
            for timer_name, timer_data in metrics["timers"].items():
                if timer_data:
                    recent_times = [
                        t["duration"] for t in timer_data[-10:]
                    ]  # Last 10 measurements
                    if recent_times:
                        avg_time = sum(recent_times) / len(recent_times)
                        if avg_time > self.thresholds["response_time"]:
                            alerts.append(
                                {
                                    "type": "performance",
                                    "metric": "response_time",
                                    "timer": timer_name,
                                    "value": avg_time,
                                    "threshold": self.thresholds["response_time"],
                                    "timestamp": time.time(),
                                }
                            )

        # Check error rate threshold
        if "errors" in metrics and "counters" in metrics:
            total_requests = sum(metrics["counters"].values())
            total_errors = sum(
                error_data["count"] for error_data in metrics["errors"].values()
            )

            if total_requests > 0:
                error_rate = total_errors / total_requests
                if error_rate > self.thresholds["error_rate"]:
                    alerts.append(
                        {
                            "type": "error_rate",
                            "metric": "error_rate",
                            "value": error_rate,
                            "threshold": self.thresholds["error_rate"],
                            "total_requests": total_requests,
                            "total_errors": total_errors,
                            "timestamp": time.time(),
                        }
                    )

        # Store alerts
        self.alerts.extend(alerts)

        # Log alerts
        for alert in alerts:
            logger.log_performance_warning(
                operation=alert["metric"],
                duration=alert.get("value", 0),
                threshold=alert.get("threshold", 0),
                context=alert,
            )

        return alerts

    async def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report.

        Returns:
            Dictionary containing performance report
        """
        metrics = await self.metrics_collector.get_metrics()
        summary = await self.metrics_collector.get_summary()
        health = await self.metrics_collector.get_health_status()
        alerts = await self.check_thresholds()

        return {
            "timestamp": time.time(),
            "health_status": health,
            "metrics_summary": summary,
            "recent_alerts": alerts[-10:],  # Last 10 alerts
            "thresholds": self.thresholds,
            "detailed_metrics": metrics,
        }
