"""Custom exception hierarchy for the Semantic Scholar MCP server.

This module defines a comprehensive exception hierarchy that provides
structured error handling throughout the application.
"""

from datetime import datetime
from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""

    # General errors (1000-1999)
    UNKNOWN_ERROR = "E1000"
    INTERNAL_ERROR = "E1001"
    NOT_IMPLEMENTED = "E1002"

    # Validation errors (2000-2999)
    VALIDATION_ERROR = "E2000"
    INVALID_INPUT = "E2001"
    MISSING_REQUIRED_FIELD = "E2002"
    INVALID_FORMAT = "E2003"
    VALUE_OUT_OF_RANGE = "E2004"

    # API errors (3000-3999)
    API_ERROR = "E3000"
    RATE_LIMIT_EXCEEDED = "E3001"
    NETWORK_ERROR = "E3002"
    TIMEOUT_ERROR = "E3003"
    SERVICE_UNAVAILABLE = "E3004"

    # Authentication/Authorization errors (4000-4999)
    UNAUTHORIZED = "E4000"
    FORBIDDEN = "E4001"
    TOKEN_EXPIRED = "E4002"
    INVALID_CREDENTIALS = "E4003"

    # Resource errors (5000-5999)
    NOT_FOUND = "E5000"
    ALREADY_EXISTS = "E5001"
    RESOURCE_LOCKED = "E5002"
    RESOURCE_DELETED = "E5003"

    # Configuration errors (6000-6999)
    CONFIGURATION_ERROR = "E6000"
    MISSING_CONFIGURATION = "E6001"
    INVALID_CONFIGURATION = "E6002"

    # Cache errors (7000-7999)
    CACHE_ERROR = "E7000"
    CACHE_MISS = "E7001"
    CACHE_EXPIRED = "E7002"
    CACHE_FULL = "E7003"

    # Database errors (8000-8999)
    DATABASE_ERROR = "E8000"
    CONNECTION_ERROR = "E8001"
    QUERY_ERROR = "E8002"
    TRANSACTION_ERROR = "E8003"


class SemanticScholarMCPError(Exception):
    """Base exception for all Semantic Scholar MCP errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: dict[str, Any] | None = None,
        inner_exception: Exception | None = None,
    ) -> None:
        """Initialize the base exception.

        Args:
            message: Human-readable error message
            error_code: Standardized error code
            details: Additional error details
            inner_exception: Original exception if wrapping
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.inner_exception = inner_exception
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        result = {
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "timestamp": self.timestamp.isoformat(),
                "type": self.__class__.__name__,
            }
        }

        if self.details:
            result["error"]["details"] = self.details

        if self.inner_exception:
            result["error"]["inner_error"] = {
                "type": type(self.inner_exception).__name__,
                "message": str(self.inner_exception),
            }

        return result

    def __str__(self) -> str:
        """String representation of the exception."""
        parts = [f"[{self.error_code.value}] {self.message}"]

        if self.details:
            parts.append(f"Details: {self.details}")

        if self.inner_exception:
            parts.append(f"Caused by: {type(self.inner_exception).__name__}: {self.inner_exception}")

        return " | ".join(parts)


class ValidationError(SemanticScholarMCPError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            validation_errors: List of validation errors
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        if validation_errors:
            details["validation_errors"] = validation_errors

        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details,
            **kwargs,
        )


class APIError(SemanticScholarMCPError):
    """Raised when external API calls fail."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: str | None = None,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: API response body
            request_id: Request ID for tracing
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if status_code:
            details["status_code"] = status_code
        if response_body:
            details["response_body"] = response_body
        if request_id:
            details["request_id"] = request_id

        super().__init__(
            message=message,
            error_code=ErrorCode.API_ERROR,
            details=details,
            **kwargs,
        )


class RateLimitError(SemanticScholarMCPError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        limit: int | None = None,
        remaining: int | None = None,
        reset_time: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
            limit: Rate limit maximum
            remaining: Remaining requests
            reset_time: When rate limit resets
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})
        kwargs.pop("error_code", None)  # Remove any existing error_code

        if retry_after is not None:
            details["retry_after"] = retry_after
        if limit is not None:
            details["limit"] = limit
        if remaining is not None:
            details["remaining"] = remaining
        if reset_time:
            details["reset_time"] = reset_time.isoformat()

        super().__init__(
            message=message,
            details=details,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            **kwargs
        )


class NetworkError(APIError):
    """Raised when network operations fail."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize network error.

        Args:
            message: Error message
            url: URL that failed
            timeout: Timeout value if applicable
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if url:
            details["url"] = url
        if timeout is not None:
            details["timeout"] = timeout

        kwargs["error_code"] = ErrorCode.NETWORK_ERROR
        super().__init__(message=message, details=details, **kwargs)


class ConfigurationError(SemanticScholarMCPError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_file: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that failed
            config_file: Configuration file path
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if config_key:
            details["config_key"] = config_key
        if config_file:
            details["config_file"] = config_file

        super().__init__(
            message=message,
            error_code=ErrorCode.CONFIGURATION_ERROR,
            details=details,
            **kwargs,
        )


class CacheError(SemanticScholarMCPError):
    """Raised when cache operations fail."""

    def __init__(
        self,
        message: str,
        cache_key: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize cache error.

        Args:
            message: Error message
            cache_key: Cache key involved
            operation: Cache operation that failed
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.CACHE_ERROR,
            details=details,
            **kwargs,
        )


class NotFoundError(SemanticScholarMCPError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize not found error.

        Args:
            message: Error message
            resource_type: Type of resource not found
            resource_id: ID of resource not found
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=details,
            **kwargs,
        )


class UnauthorizedError(SemanticScholarMCPError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Unauthorized access",
        realm: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize unauthorized error.

        Args:
            message: Error message
            realm: Authentication realm
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if realm:
            details["realm"] = realm

        super().__init__(
            message=message,
            error_code=ErrorCode.UNAUTHORIZED,
            details=details,
            **kwargs,
        )


class ForbiddenError(SemanticScholarMCPError):
    """Raised when access is forbidden."""

    def __init__(
        self,
        message: str = "Access forbidden",
        resource: str | None = None,
        action: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize forbidden error.

        Args:
            message: Error message
            resource: Resource access was attempted on
            action: Action that was forbidden
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action

        super().__init__(
            message=message,
            error_code=ErrorCode.FORBIDDEN,
            details=details,
            **kwargs,
        )


class DatabaseError(SemanticScholarMCPError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        table: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize database error.

        Args:
            message: Error message
            query: SQL query that failed
            table: Database table involved
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if query:
            details["query"] = query
        if table:
            details["table"] = table

        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            details=details,
            **kwargs,
        )


class ServiceUnavailableError(APIError):
    """Raised when a service is temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: str | None = None,
        retry_after: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize service unavailable error.

        Args:
            message: Error message
            service_name: Name of unavailable service
            retry_after: Seconds until service might be available
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if service_name:
            details["service_name"] = service_name
        if retry_after is not None:
            details["retry_after"] = retry_after

        kwargs["error_code"] = ErrorCode.SERVICE_UNAVAILABLE
        super().__init__(message=message, details=details, **kwargs)
