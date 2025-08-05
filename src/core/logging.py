"""Enterprise logging infrastructure with structured logging and correlation IDs."""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Any

from .config import LoggingConfig
from .interfaces import ILogger

# Context variables for request tracking
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
tool_name_var: ContextVar[str | None] = ContextVar("tool_name", default=None)
mcp_operation_var: ContextVar[str | None] = ContextVar("mcp_operation", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
execution_id_var: ContextVar[str | None] = ContextVar("execution_id", default=None)
error_chain_var: ContextVar[list[str] | None] = ContextVar("error_chain", default=None)
performance_trace_var: ContextVar[dict[str, float] | None] = ContextVar(
    "performance_trace", default=None
)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation IDs and MCP context
        if self.include_context:
            correlation_id = correlation_id_var.get()
            request_id = request_id_var.get()
            user_id = user_id_var.get()
            tool_name = tool_name_var.get()
            mcp_operation = mcp_operation_var.get()
            session_id = session_id_var.get()
            execution_id = execution_id_var.get()
            error_chain = error_chain_var.get() or []
            performance_trace = performance_trace_var.get() or {}

            if correlation_id:
                log_data["correlation_id"] = correlation_id
            if request_id:
                log_data["request_id"] = request_id
            if user_id:
                log_data["user_id"] = user_id
            if tool_name:
                log_data["tool_name"] = tool_name
            if mcp_operation:
                log_data["mcp_operation"] = mcp_operation
            if session_id:
                log_data["session_id"] = session_id
            if execution_id:
                log_data["execution_id"] = execution_id
            if error_chain:
                log_data["error_chain"] = error_chain
            if performance_trace:
                log_data["performance_trace"] = performance_trace

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self, include_context: bool = True):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        # Add correlation IDs to message if present
        if self.include_context:
            correlation_id = correlation_id_var.get()
            request_id = request_id_var.get()

            context_parts = []
            if correlation_id:
                context_parts.append(f"correlation_id={correlation_id}")
            if request_id:
                context_parts.append(f"request_id={request_id}")

            if context_parts:
                record.msg = f"[{' '.join(context_parts)}] {record.msg}"

        return super().format(record)


class ContextLogger(ILogger):
    """Logger implementation with context support."""

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        self._logger = logger
        self._context = context or {}

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        extra = self._context.copy()
        extra.update(kwargs)

        # Extract exception if provided
        exception = extra.pop("exception", None)
        exc_info = None
        if exception:
            exc_info = (type(exception), exception, exception.__traceback__)

        self._logger.log(level, message, exc_info=exc_info, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)

    def error(
        self, message: str, exception: Exception | None = None, **kwargs: Any
    ) -> None:
        """Log error message."""
        if exception:
            kwargs["exception"] = exception
        self._log(logging.ERROR, message, **kwargs)

    def with_context(self, **context: Any) -> "ContextLogger":
        """Create logger with additional context."""
        new_context = self._context.copy()
        new_context.update(context)
        return ContextLogger(self._logger, new_context)

    def debug_mcp(self, message: str, **kwargs: Any) -> None:
        """Log MCP-specific debug message (only when DEBUG_MCP_MODE is enabled)."""
        if os.getenv("DEBUG_MCP_MODE", "false").lower() == "true":
            kwargs["mcp_debug"] = True
            self.debug(message, **kwargs)

    def trace_tool_execution(
        self, tool_name: str, operation: str, **kwargs: Any
    ) -> None:
        """Log tool execution trace."""
        kwargs.update(
            {"tool_name": tool_name, "operation": operation, "execution_trace": True}
        )
        self.debug_mcp(f"Tool execution: {tool_name}.{operation}", **kwargs)

    def log_api_request(self, method: str, url: str, **kwargs: Any) -> None:
        """Log API request details (when API payload logging is enabled)."""
        if os.getenv("LOG_API_PAYLOADS", "false").lower() == "true":
            kwargs.update({"api_request": True, "method": method, "url": url})
            self.debug_mcp(f"API Request: {method} {url}", **kwargs)

    def log_api_response(
        self, status_code: int, response_time: float, **kwargs: Any
    ) -> None:
        """Log API response details (when API payload logging is enabled)."""
        if os.getenv("LOG_API_PAYLOADS", "false").lower() == "true":
            kwargs.update(
                {
                    "api_response": True,
                    "status_code": status_code,
                    "response_time_ms": response_time * 1000,
                }
            )
            self.debug_mcp(
                f"API Response: {status_code} ({response_time:.2f}s)", **kwargs
            )

    def log_circuit_breaker_state(self, state: str, **kwargs: Any) -> None:
        """Log circuit breaker state changes."""
        kwargs.update({"circuit_breaker": True, "state": state})
        self.info(f"Circuit breaker state: {state}", **kwargs)

    def log_with_stack_trace(self, level: int, message: str, **kwargs: Any) -> None:
        """Log message with stack trace for debugging."""
        if os.getenv("DEBUG_MCP_MODE", "false").lower() == "true":
            kwargs["stack_trace"] = "".join(traceback.format_stack())
        self._log(level, message, **kwargs)

    def log_error_with_context(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        error_id: str | None = None,
        recovery_actions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error with comprehensive context and recovery information."""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_id": error_id or str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recovery_actions": recovery_actions or [],
        }

        if context:
            error_context.update(context)

        # Add error to chain
        current_chain = error_chain_var.get() or []
        current_chain.append(error_context["error_id"])
        error_chain_var.set(current_chain)

        # Add stack trace
        if hasattr(error, "__traceback__") and error.__traceback__:
            error_context["stack_trace"] = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

        # Filter out reserved logging keywords to avoid conflicts
        filtered_context = {
            k: v
            for k, v in error_context.items()
            if k
            not in {
                "args",
                "name",
                "msg",
                "filename",
                "lineno",
                "funcName",
                "levelno",
                "levelname",
                "pathname",
                "module",
            }
        }
        kwargs.update(filtered_context)
        self.error(f"Error occurred: {error}", **kwargs)

    def log_error_recovery(
        self,
        error_id: str,
        recovery_action: str,
        success: bool,
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error recovery attempt."""
        recovery_context = {
            "error_id": error_id,
            "recovery_action": recovery_action,
            "recovery_success": success,
            "recovery_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if details:
            recovery_context.update(details)

        kwargs.update(recovery_context)
        level = logging.INFO if success else logging.WARNING
        self._log(
            level,
            f"Recovery {'succeeded' if success else 'failed'}: {recovery_action}",
            **kwargs,
        )

    def log_performance_warning(
        self,
        operation: str,
        duration: float,
        threshold: float,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log performance warning when operation exceeds threshold."""
        perf_context = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "threshold_ms": threshold * 1000,
            "performance_warning": True,
        }

        if context:
            perf_context.update(context)

        kwargs.update(perf_context)
        self.warning(
            f"Performance warning: {operation} took {duration:.2f}s "
            f"(threshold: {threshold:.2f}s)",
            **kwargs,
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log security-related events."""
        security_context = {
            "event_type": event_type,
            "severity": severity,
            "security_event": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if details:
            security_context.update(details)

        kwargs.update(security_context)
        level = logging.ERROR if severity == "high" else logging.WARNING
        self._log(level, f"Security event: {event_type}", **kwargs)

    def log_resource_usage(
        self,
        resource_type: str,
        current_usage: float,
        limit: float,
        unit: str = "count",
        **kwargs: Any,
    ) -> None:
        """Log resource usage metrics."""
        usage_context = {
            "resource_type": resource_type,
            "current_usage": current_usage,
            "limit": limit,
            "unit": unit,
            "usage_percentage": (current_usage / limit) * 100 if limit > 0 else 0,
            "resource_usage": True,
        }

        kwargs.update(usage_context)
        level = logging.WARNING if current_usage > limit * 0.8 else logging.INFO
        self._log(
            level,
            f"Resource usage: {resource_type} {current_usage}/{limit} {unit}",
            **kwargs,
        )


class LoggerFactory:
    """Factory for creating loggers."""

    def __init__(self, config: LoggingConfig):
        self.config = config
        self._setup_root_logger()

    def _setup_root_logger(self) -> None:
        """Set up the root logger configuration."""
        root_logger = logging.getLogger()
        # Handle both enum and string values for level
        level = self.config.level
        if hasattr(level, "value"):
            level = level.value
        root_logger.setLevel(level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Create formatter
        if self.config.format == "json":
            formatter = StructuredFormatter(self.config.include_context)
        else:
            formatter = TextFormatter(self.config.include_context)

        # Console handler (stderr for MCP compatibility)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler if configured
        if self.config.file_path:
            file_handler = RotatingFileHandler(
                filename=str(self.config.file_path),
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count,
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    def get_logger(self, name: str) -> ContextLogger:
        """Get a logger instance."""
        logger = logging.getLogger(name)
        return ContextLogger(logger)


# Performance logging decorator
def log_performance(
    logger_name: str | None = None, log_args: bool = False, log_result: bool = False
):
    """Decorator to log function performance."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = LoggerFactory(LoggingConfig()).get_logger(
                logger_name or f"{func.__module__}.{func.__name__}"
            )

            start_time = time.time()
            context = {
                "function": func.__name__,
                "func_module": func.__module__,
            }

            if log_args:
                context["args"] = str(args)
                context["kwargs"] = str(kwargs)

            logger.info(f"Starting {func.__name__}", **context)

            try:
                result = await func(*args, **kwargs)

                elapsed_time = time.time() - start_time
                context["elapsed_seconds"] = elapsed_time

                if log_result:
                    context["result"] = str(result)

                logger.info(f"Completed {func.__name__}", **context)

                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                context["elapsed_seconds"] = elapsed_time

                logger.error(f"Failed {func.__name__}", exception=e, **context)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = LoggerFactory(LoggingConfig()).get_logger(
                logger_name or f"{func.__module__}.{func.__name__}"
            )

            start_time = time.time()
            context = {
                "function": func.__name__,
                "func_module": func.__module__,
            }

            if log_args:
                context["args"] = str(args)
                context["kwargs"] = str(kwargs)

            logger.info(f"Starting {func.__name__}", **context)

            try:
                result = func(*args, **kwargs)

                elapsed_time = time.time() - start_time
                context["elapsed_seconds"] = elapsed_time

                if log_result:
                    context["result"] = str(result)

                logger.info(f"Completed {func.__name__}", **context)

                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                context["elapsed_seconds"] = elapsed_time

                logger.error(f"Failed {func.__name__}", exception=e, **context)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Context managers for correlation tracking
class CorrelationContext:
    """Context manager for correlation ID tracking."""

    def __init__(self, correlation_id: str | None = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._token = None

    def __enter__(self):
        self._token = correlation_id_var.set(self.correlation_id)
        return self.correlation_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        correlation_id_var.reset(self._token)


class RequestContext:
    """Context manager for request tracking (supports both sync and async)."""

    def __init__(
        self,
        request_id: str | None = None,
        user_id: str | None = None,
        correlation_id: str | None = None,
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.correlation_id = (
            correlation_id or correlation_id_var.get() or str(uuid.uuid4())
        )
        self._tokens = []

    def __enter__(self):
        self._tokens.append(request_id_var.set(self.request_id))
        self._tokens.append(correlation_id_var.set(self.correlation_id))
        if self.user_id:
            self._tokens.append(user_id_var.set(self.user_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in reversed(self._tokens):
            if token:
                token.var.reset(token)

    async def __aenter__(self):
        """Async context manager entry."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return self.__exit__(exc_type, exc_val, exc_tb)


class MCPToolContext:
    """Context manager for MCP tool execution tracking."""

    def __init__(
        self,
        tool_name: str,
        operation: str = "execute",
        correlation_id: str | None = None,
    ):
        self.tool_name = tool_name
        self.operation = operation
        self.correlation_id = (
            correlation_id or correlation_id_var.get() or str(uuid.uuid4())
        )
        self._tokens = []
        self._start_time = None

    def __enter__(self):
        self._start_time = time.time()
        self._tokens.append(tool_name_var.set(self.tool_name))
        self._tokens.append(mcp_operation_var.set(self.operation))
        self._tokens.append(correlation_id_var.set(self.correlation_id))

        # Log tool start if MCP debugging is enabled
        if os.getenv("DEBUG_MCP_MODE", "false").lower() == "true":
            logger = get_logger(f"mcp.tool.{self.tool_name}")
            logger.debug_mcp(
                f"Tool {self.tool_name} starting",
                tool_operation=self.operation,
                start_time=self._start_time,
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Log tool completion if MCP debugging is enabled
        if os.getenv("DEBUG_MCP_MODE", "false").lower() == "true" and self._start_time:
            elapsed = time.time() - self._start_time
            logger = get_logger(f"mcp.tool.{self.tool_name}")

            if exc_type is None:
                logger.debug_mcp(
                    f"Tool {self.tool_name} completed successfully",
                    tool_operation=self.operation,
                    elapsed_seconds=elapsed,
                )
            else:
                logger.debug_mcp(
                    f"Tool {self.tool_name} failed",
                    tool_operation=self.operation,
                    elapsed_seconds=elapsed,
                    exception_type=exc_type.__name__ if exc_type else None,
                    exception_message=str(exc_val) if exc_val else None,
                )

        for token in reversed(self._tokens):
            if token:
                token.var.reset(token)

    async def __aenter__(self):
        """Async context manager entry."""
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        return self.__exit__(exc_type, exc_val, exc_tb)


# Global logger instance
_logger_factory: LoggerFactory | None = None


def initialize_logging(config: LoggingConfig) -> None:
    """Initialize global logging configuration."""
    global _logger_factory
    _logger_factory = LoggerFactory(config)


def get_logger(name: str) -> ContextLogger:
    """Get a logger instance."""
    if not _logger_factory:
        # Use default config if not initialized
        initialize_logging(LoggingConfig())

    return _logger_factory.get_logger(name)
