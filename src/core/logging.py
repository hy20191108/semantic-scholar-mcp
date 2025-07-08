"""Enterprise logging infrastructure with structured logging and correlation IDs."""

import asyncio
import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from logging.handlers import RotatingFileHandler
from typing import Any

from .config import LoggingConfig
from .protocols import ILogger

# Context variables for request tracking
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add correlation IDs
        if self.include_context:
            correlation_id = correlation_id_var.get()
            request_id = request_id_var.get()
            user_id = user_id_var.get()

            if correlation_id:
                log_data["correlation_id"] = correlation_id
            if request_id:
                log_data["request_id"] = request_id
            if user_id:
                log_data["user_id"] = user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info"
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def __init__(self, include_context: bool = True):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
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

    def error(self, message: str, exception: Exception | None = None, **kwargs: Any) -> None:
        """Log error message."""
        if exception:
            kwargs["exception"] = exception
        self._log(logging.ERROR, message, **kwargs)

    def with_context(self, **context: Any) -> "ContextLogger":
        """Create logger with additional context."""
        new_context = self._context.copy()
        new_context.update(context)
        return ContextLogger(self._logger, new_context)


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
        if hasattr(level, 'value'):
            level = level.value
        root_logger.setLevel(level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Create formatter
        if self.config.format == "json":
            formatter = StructuredFormatter(self.config.include_context)
        else:
            formatter = TextFormatter(self.config.include_context)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # File handler if configured
        if self.config.file_path:
            file_handler = RotatingFileHandler(
                filename=str(self.config.file_path),
                maxBytes=self.config.max_file_size,
                backupCount=self.config.backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    def get_logger(self, name: str) -> ContextLogger:
        """Get a logger instance."""
        logger = logging.getLogger(name)
        return ContextLogger(logger)


# Performance logging decorator
def log_performance(
    logger_name: str | None = None,
    log_args: bool = False,
    log_result: bool = False
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

                logger.error(
                    f"Failed {func.__name__}",
                    exception=e,
                    **context
                )
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

                logger.error(
                    f"Failed {func.__name__}",
                    exception=e,
                    **context
                )
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
        correlation_id: str | None = None
    ):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.correlation_id = correlation_id or correlation_id_var.get() or str(uuid.uuid4())
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
