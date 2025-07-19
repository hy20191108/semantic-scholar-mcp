"""Comprehensive tests for error handling and logging systems."""

import asyncio

import pytest

from core.error_handler import (
    ErrorRecoveryStrategy,
    MCPErrorHandler,
    mcp_error_handler,
    validation_error_handler,
)
from core.exceptions import (
    APIError,
    CircuitBreakerError,
    ErrorCode,
    MCPTimeoutError,
    MCPToolError,
    RateLimitError,
    RetryExhaustedError,
    SemanticScholarMCPError,
    ValidationError,
    create_error_response,
    wrap_exception,
)
from core.metrics_collector import MetricsCollector, PerformanceMonitor


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_base_exception_creation(self):
        """Test base exception creation and serialization."""
        error = SemanticScholarMCPError(
            message="Test error",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"field": "test_field", "value": "invalid"},
            include_stack_trace=True,
        )

        assert error.message == "Test error"
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "test_field"
        assert "stack_trace" in error.details

        # Test serialization
        error_dict = error.to_dict()
        assert error_dict["error"]["code"] == "E2000"
        assert error_dict["error"]["message"] == "Test error"
        assert error_dict["error"]["type"] == "SemanticScholarMCPError"

    def test_validation_error(self):
        """Test ValidationError creation."""
        error = ValidationError(
            message="Invalid input",
            field="query",
            value="",
            validation_errors=[{"field": "query", "error": "required"}],
        )

        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.details["field"] == "query"
        assert error.details["value"] == ""
        assert len(error.details["validation_errors"]) == 1

    def test_api_error(self):
        """Test APIError creation."""
        error = APIError(
            message="API request failed",
            status_code=404,
            response_body='{"error": "Not found"}',
            request_id="test-123",
        )

        assert error.error_code == ErrorCode.API_ERROR
        assert error.details["status_code"] == 404
        assert error.details["response_body"] == '{"error": "Not found"}'
        assert error.details["request_id"] == "test-123"

    def test_rate_limit_error(self):
        """Test RateLimitError creation."""
        error = RateLimitError(
            message="Rate limit exceeded",
            retry_after=60,
            limit=100,
            remaining=0,
        )

        assert error.error_code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert error.details["retry_after"] == 60
        assert error.details["limit"] == 100
        assert error.details["remaining"] == 0

    def test_circuit_breaker_error(self):
        """Test CircuitBreakerError creation."""
        error = CircuitBreakerError(
            message="Circuit breaker is open",
            failure_count=5,
            failure_threshold=5,
            reset_timeout=60.0,
        )

        assert error.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert error.details["failure_count"] == 5
        assert error.details["failure_threshold"] == 5
        assert error.details["reset_timeout"] == 60.0

    def test_mcp_tool_error(self):
        """Test MCPToolError creation."""
        error = MCPToolError(
            message="Tool execution failed",
            tool_name="search_papers",
            arguments={"query": "test", "limit": 10},
            execution_id="exec-123",
        )

        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.details["tool_name"] == "search_papers"
        assert error.details["arguments"] == {"query": "test", "limit": 10}
        assert error.details["execution_id"] == "exec-123"

    def test_retry_exhausted_error(self):
        """Test RetryExhaustedError creation."""
        last_error = ValueError("Original error")
        retry_history = [
            {
                "attempt": 0,
                "error_type": "ValueError",
                "error_message": "Original error",
            },
            {
                "attempt": 1,
                "error_type": "ValueError",
                "error_message": "Original error",
            },
        ]

        error = RetryExhaustedError(
            message="All retries failed",
            max_retries=2,
            last_error=last_error,
            retry_history=retry_history,
        )

        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.details["max_retries"] == 2
        assert error.details["last_error"]["type"] == "ValueError"
        assert len(error.details["retry_history"]) == 2
        assert error.inner_exception == last_error

    def test_wrap_exception(self):
        """Test exception wrapping functionality."""
        original = ValueError("Original error")
        wrapped = wrap_exception(
            original,
            context={"operation": "test"},
            error_code=ErrorCode.VALIDATION_ERROR,
        )

        assert isinstance(wrapped, SemanticScholarMCPError)
        assert wrapped.error_code == ErrorCode.VALIDATION_ERROR
        assert wrapped.inner_exception == original
        assert wrapped.details["operation"] == "test"
        assert wrapped.details["original_exception"] == "ValueError"

    def test_create_error_response(self):
        """Test error response creation."""
        error = ValidationError("Test error", field="test")
        response = create_error_response(error, include_internal_details=True)

        assert "error" in response
        assert response["error"]["code"] == "E2000"
        assert response["error"]["message"] == "Test error"

        # Test without internal details
        response_clean = create_error_response(error, include_internal_details=False)
        assert "error" in response_clean


class TestErrorRecovery:
    """Test error recovery strategies."""

    @pytest.mark.asyncio
    async def test_error_recovery_strategy_success(self):
        """Test successful recovery strategy."""
        strategy = ErrorRecoveryStrategy(max_retries=2, retry_delay=0.1)

        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await strategy.execute_with_retry(failing_function)
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_error_recovery_strategy_exhausted(self):
        """Test exhausted retry strategy."""
        strategy = ErrorRecoveryStrategy(max_retries=2, retry_delay=0.1)

        async def always_failing_function():
            raise ValueError("Persistent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await strategy.execute_with_retry(always_failing_function)

        error = exc_info.value
        assert error.details["max_retries"] == 2
        assert len(error.details["retry_history"]) == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_error_recovery_with_actions(self):
        """Test recovery strategy with recovery actions."""
        recovery_called = []

        async def recovery_action(error):
            recovery_called.append(error)

        strategy = ErrorRecoveryStrategy(
            max_retries=1,
            retry_delay=0.1,
            recovery_actions=[recovery_action],
        )

        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"

        result = await strategy.execute_with_retry(failing_function)
        assert result == "success"
        assert len(recovery_called) == 1
        assert isinstance(recovery_called[0], ValueError)


class TestMCPErrorHandler:
    """Test MCP error handler."""

    @pytest.mark.asyncio
    async def test_mcp_tool_error_handling(self):
        """Test MCP tool error handling."""
        handler = MCPErrorHandler()

        error = ValueError("Test error")
        response = await handler.handle_mcp_tool_error(
            error=error,
            tool_name="test_tool",
            arguments={"param": "value"},
            context={"session_id": "test-session"},
        )

        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == "E1001"  # INTERNAL_ERROR

    @pytest.mark.asyncio
    async def test_mcp_resource_error_handling(self):
        """Test MCP resource error handling."""
        handler = MCPErrorHandler()

        error = FileNotFoundError("Resource not found")
        response = await handler.handle_mcp_resource_error(
            error=error,
            resource_uri="papers/123",
            resource_type="paper",
        )

        assert "error" in response
        assert response["error"]["code"] == "E5000"  # NOT_FOUND

    @pytest.mark.asyncio
    async def test_mcp_prompt_error_handling(self):
        """Test MCP prompt error handling."""
        handler = MCPErrorHandler()

        error = ValueError("Invalid prompt arguments")
        response = await handler.handle_mcp_prompt_error(
            error=error,
            prompt_name="test_prompt",
            prompt_args={"topic": "test"},
        )

        assert "error" in response
        assert response["error"]["code"] == "E2000"  # VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation error handling."""
        handler = MCPErrorHandler()

        error = ValueError("Invalid value")
        response = await handler.handle_validation_error(
            error=error,
            field="test_field",
            value="invalid_value",
        )

        assert "error" in response
        assert response["error"]["code"] == "E2000"  # VALIDATION_ERROR

    def test_error_metrics_update(self):
        """Test error metrics updating."""
        handler = MCPErrorHandler()

        error = ValueError("Test error")
        handler._update_metrics(error, recovery_attempted=True, recovery_success=True)

        metrics = handler.get_metrics()
        assert metrics["total_errors"] == 1
        assert metrics["errors_by_type"]["ValueError"] == 1
        assert metrics["recovery_attempts"] == 1
        assert metrics["recovery_successes"] == 1


class TestErrorHandlerDecorators:
    """Test error handler decorators."""

    @pytest.mark.asyncio
    async def test_mcp_error_handler_decorator_success(self):
        """Test MCP error handler decorator with successful function."""

        @mcp_error_handler(tool_name="test_tool")
        async def successful_function(value: int) -> int:
            return value * 2

        result = await successful_function(5)
        assert result == 10

    @pytest.mark.asyncio
    async def test_mcp_error_handler_decorator_error(self):
        """Test MCP error handler decorator with failing function."""

        @mcp_error_handler(tool_name="test_tool")
        async def failing_function():
            raise ValueError("Test error")

        result = await failing_function()
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_validation_error_handler_decorator(self):
        """Test validation error handler decorator."""

        @validation_error_handler(field="test_field")
        async def validating_function(value: str) -> str:
            if not value:
                raise ValueError("Value cannot be empty")
            return value.upper()

        # Test successful validation
        result = await validating_function("test")
        assert result == "TEST"

        # Test failing validation
        result = await validating_function("")
        assert isinstance(result, dict)
        assert "error" in result


class TestMetricsCollector:
    """Test metrics collection system."""

    @pytest.mark.asyncio
    async def test_counter_metrics(self):
        """Test counter metrics."""
        collector = MetricsCollector()

        await collector.increment_counter("test_counter", 5)
        await collector.increment_counter("test_counter", 3)

        metrics = await collector.get_metrics()
        assert metrics["counters"]["test_counter"] == 8

    @pytest.mark.asyncio
    async def test_gauge_metrics(self):
        """Test gauge metrics."""
        collector = MetricsCollector()

        await collector.set_gauge("test_gauge", 42.5)
        await collector.set_gauge("test_gauge", 35.0)

        metrics = await collector.get_metrics()
        assert metrics["gauges"]["test_gauge"] == 35.0

    @pytest.mark.asyncio
    async def test_histogram_metrics(self):
        """Test histogram metrics."""
        collector = MetricsCollector()

        await collector.record_histogram("test_histogram", 10.0)
        await collector.record_histogram("test_histogram", 20.0)

        metrics = await collector.get_metrics()
        assert len(metrics["histograms"]["test_histogram"]) == 2
        assert metrics["histograms"]["test_histogram"][0]["value"] == 10.0

    @pytest.mark.asyncio
    async def test_timer_metrics(self):
        """Test timer metrics."""
        collector = MetricsCollector()

        await collector.record_timer("test_timer", 1.5)
        await collector.record_timer("test_timer", 2.3)

        metrics = await collector.get_metrics()
        assert len(metrics["timers"]["test_timer"]) == 2
        assert metrics["timers"]["test_timer"][0]["duration"] == 1.5

    @pytest.mark.asyncio
    async def test_error_metrics(self):
        """Test error metrics."""
        collector = MetricsCollector()

        error1 = ValueError("First error")
        error2 = TypeError("Second error")

        await collector.record_error("test_errors", error1)
        await collector.record_error("test_errors", error2)

        metrics = await collector.get_metrics()
        error_data = metrics["errors"]["test_errors"]
        assert error_data["count"] == 2
        assert error_data["error_types"]["ValueError"] == 1
        assert error_data["error_types"]["TypeError"] == 1

    @pytest.mark.asyncio
    async def test_metrics_with_labels(self):
        """Test metrics with labels."""
        collector = MetricsCollector()

        labels1 = {"service": "api", "method": "GET"}
        labels2 = {"service": "api", "method": "POST"}

        await collector.increment_counter("requests", labels=labels1)
        await collector.increment_counter("requests", labels=labels2)

        metrics = await collector.get_metrics()
        assert "requests(method=GET,service=api)" in metrics["counters"]
        assert "requests(method=POST,service=api)" in metrics["counters"]

    @pytest.mark.asyncio
    async def test_health_status(self):
        """Test health status calculation."""
        collector = MetricsCollector()

        # Record some recent errors
        error = ValueError("Test error")
        await collector.record_error("test_errors", error)

        health = await collector.get_health_status()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "recent_errors" in health
        assert "timestamp" in health


class TestPerformanceMonitor:
    """Test performance monitoring."""

    @pytest.mark.asyncio
    async def test_performance_threshold_checking(self):
        """Test performance threshold checking."""
        collector = MetricsCollector()
        monitor = PerformanceMonitor(collector)

        # Record slow response times
        await collector.record_timer("slow_operation", 3.0)  # Above 2.0s threshold
        await collector.record_timer("slow_operation", 4.0)

        alerts = await monitor.check_thresholds()
        assert len(alerts) > 0
        assert alerts[0]["type"] == "performance"
        assert alerts[0]["metric"] == "response_time"

    @pytest.mark.asyncio
    async def test_performance_report(self):
        """Test comprehensive performance report."""
        collector = MetricsCollector()
        monitor = PerformanceMonitor(collector)

        # Add some sample data
        await collector.increment_counter("requests")
        await collector.record_timer("api_call", 1.0)
        await collector.record_error("api_errors", ValueError("Test"))

        report = await monitor.get_performance_report()

        assert "timestamp" in report
        assert "health_status" in report
        assert "metrics_summary" in report
        assert "thresholds" in report
        assert "detailed_metrics" in report


@pytest.mark.asyncio
class TestIntegratedErrorHandling:
    """Test integrated error handling scenarios."""

    async def test_full_error_pipeline(self):
        """Test complete error handling pipeline."""
        # Setup
        MetricsCollector()
        handler = MCPErrorHandler()

        # Simulate a complex error scenario
        original_error = MCPTimeoutError("Request timed out", timeout_duration=30.0)

        response = await handler.handle_mcp_tool_error(
            error=original_error,
            tool_name="search_papers",
            arguments={"query": "test", "limit": 10},
            context={"user_id": "test-user", "session_id": "test-session"},
        )

        # Verify error response structure
        assert response["success"] is False
        assert "error" in response
        assert (
            response["error"]["code"] == "E3003"
        )  # TIMEOUT_ERROR for timeout exceptions

        # Verify metrics were updated
        metrics = handler.get_metrics()
        assert metrics["total_errors"] == 1

    async def test_concurrent_error_handling(self):
        """Test error handling under concurrent conditions."""
        handler = MCPErrorHandler()

        # Create multiple concurrent errors
        async def create_error(error_id: int):
            error = ValueError(f"Error {error_id}")
            return await handler.handle_mcp_tool_error(
                error=error,
                tool_name=f"tool_{error_id}",
                arguments={"id": error_id},
            )

        # Run multiple errors concurrently
        results = await asyncio.gather(*[create_error(i) for i in range(5)])

        # Verify all errors were handled
        assert len(results) == 5
        for result in results:
            assert result["success"] is False
            assert "error" in result

        # Verify metrics
        metrics = handler.get_metrics()
        assert metrics["total_errors"] == 5

    async def test_error_chain_tracking(self):
        """Test error chain tracking through multiple levels."""
        handler = MCPErrorHandler()

        # Create a chain of errors
        original = ValueError("Original error")
        wrapped = MCPToolError(
            "Tool error",
            tool_name="test_tool",
            inner_exception=original,
        )

        response = await handler.handle_mcp_tool_error(
            error=wrapped,
            tool_name="test_tool",
            arguments={},
        )

        # Verify error chain information
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["inner_error"]["type"] == "ValueError"
        assert response["error"]["inner_error"]["message"] == "Original error"
