"""Custom exception hierarchy for the Semantic Scholar MCP server.

This module defines a comprehensive exception hierarchy that provides
structured error handling throughout the application.
"""

import traceback
from datetime import datetime, timezone
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
        include_stack_trace: bool = False,
    ) -> None:
        """Initialize the base exception.

        Args:
            message: Human-readable error message
            error_code: Standardized error code
            details: Additional error details
            inner_exception: Original exception if wrapping
            include_stack_trace: Whether to include stack trace in details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.inner_exception = inner_exception
        self.timestamp = datetime.now(timezone.utc)

        # Add stack trace if requested
        if include_stack_trace:
            self.details["stack_trace"] = "".join(traceback.format_stack())

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
            parts.append(
                f"Caused by: {type(self.inner_exception).__name__}: "
                f"{self.inner_exception}"
            )

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
            **kwargs,
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


class MCPTimeoutError(SemanticScholarMCPError):
    """Raised when operations time out."""

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_duration: float | None = None,
        operation_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize timeout error.

        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            operation_type: Type of operation that timed out
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if timeout_duration is not None:
            details["timeout_duration"] = timeout_duration
        if operation_type:
            details["operation_type"] = operation_type

        kwargs["error_code"] = ErrorCode.TIMEOUT_ERROR
        super().__init__(message=message, details=details, **kwargs)


class CircuitBreakerError(SemanticScholarMCPError):
    """Raised when circuit breaker is open."""

    def __init__(
        self,
        message: str = "Circuit breaker is open",
        failure_count: int | None = None,
        failure_threshold: int | None = None,
        reset_timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize circuit breaker error.

        Args:
            message: Error message
            failure_count: Current failure count
            failure_threshold: Threshold for opening circuit
            reset_timeout: Time until circuit reset attempt
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if failure_count is not None:
            details["failure_count"] = failure_count
        if failure_threshold is not None:
            details["failure_threshold"] = failure_threshold
        if reset_timeout is not None:
            details["reset_timeout"] = reset_timeout

        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            details=details,
            **kwargs,
        )


class RetryExhaustedError(SemanticScholarMCPError):
    """Raised when retry attempts are exhausted."""

    def __init__(
        self,
        message: str = "Retry attempts exhausted",
        max_retries: int | None = None,
        last_error: Exception | None = None,
        retry_history: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize retry exhausted error.

        Args:
            message: Error message
            max_retries: Maximum number of retries attempted
            last_error: Last error that occurred
            retry_history: History of retry attempts
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if max_retries is not None:
            details["max_retries"] = max_retries
        if last_error:
            details["last_error"] = {
                "type": type(last_error).__name__,
                "message": str(last_error),
            }
        if retry_history:
            details["retry_history"] = retry_history

        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            details=details,
            inner_exception=last_error,
            **kwargs,
        )


class MCPToolError(SemanticScholarMCPError):
    """Raised when MCP tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        execution_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MCP tool error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            arguments: Arguments passed to the tool
            execution_id: Unique execution identifier
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        details["tool_name"] = tool_name
        if arguments:
            details["arguments"] = arguments
        if execution_id:
            details["execution_id"] = execution_id

        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            details=details,
            **kwargs,
        )


class MCPResourceError(SemanticScholarMCPError):
    """Raised when MCP resource operations fail."""

    def __init__(
        self,
        message: str,
        resource_uri: str,
        resource_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MCP resource error.

        Args:
            message: Error message
            resource_uri: URI of the resource
            resource_type: Type of resource
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        details["resource_uri"] = resource_uri
        if resource_type:
            details["resource_type"] = resource_type

        super().__init__(
            message=message,
            error_code=ErrorCode.NOT_FOUND,
            details=details,
            **kwargs,
        )


class MCPPromptError(SemanticScholarMCPError):
    """Raised when MCP prompt operations fail."""

    def __init__(
        self,
        message: str,
        prompt_name: str,
        prompt_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize MCP prompt error.

        Args:
            message: Error message
            prompt_name: Name of the prompt
            prompt_args: Arguments passed to the prompt
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        details["prompt_name"] = prompt_name
        if prompt_args:
            details["prompt_args"] = prompt_args

        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            details=details,
            **kwargs,
        )


class DataProcessingError(SemanticScholarMCPError):
    """Raised when data processing operations fail."""

    def __init__(
        self,
        message: str,
        data_type: str | None = None,
        processing_step: str | None = None,
        data_sample: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize data processing error.

        Args:
            message: Error message
            data_type: Type of data being processed
            processing_step: Step in processing that failed
            data_sample: Sample of problematic data
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        if data_type:
            details["data_type"] = data_type
        if processing_step:
            details["processing_step"] = processing_step
        if data_sample is not None:
            details["data_sample"] = str(data_sample)[:1000]  # Truncate long samples

        super().__init__(
            message=message,
            error_code=ErrorCode.INTERNAL_ERROR,
            details=details,
            **kwargs,
        )


class ExternalServiceError(APIError):
    """Raised when external service integration fails."""

    def __init__(
        self,
        message: str,
        service_name: str,
        service_endpoint: str | None = None,
        service_version: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize external service error.

        Args:
            message: Error message
            service_name: Name of external service
            service_endpoint: Service endpoint URL
            service_version: Service version
            **kwargs: Additional arguments for base exception
        """
        details = kwargs.pop("details", {})

        details["service_name"] = service_name
        if service_endpoint:
            details["service_endpoint"] = service_endpoint
        if service_version:
            details["service_version"] = service_version

        super().__init__(message=message, details=details, **kwargs)


def wrap_exception(
    exception: Exception,
    context: dict[str, Any] | None = None,
    error_code: ErrorCode | None = None,
    include_stack_trace: bool = True,
) -> SemanticScholarMCPError:
    """Wrap any exception into a SemanticScholarMCPError.

    Args:
        exception: Original exception
        context: Additional context information
        error_code: Error code to use
        include_stack_trace: Whether to include stack trace

    Returns:
        Wrapped exception
    """
    if isinstance(exception, SemanticScholarMCPError):
        return exception

    message = str(exception)
    error_code = error_code or ErrorCode.INTERNAL_ERROR
    details = context or {}
    details["original_exception"] = type(exception).__name__

    return SemanticScholarMCPError(
        message=message,
        error_code=error_code,
        details=details,
        inner_exception=exception,
        include_stack_trace=include_stack_trace,
    )


def create_error_response(
    exception: Exception,
    include_internal_details: bool = False,
) -> dict[str, Any]:
    """Create standardized error response from exception.

    Args:
        exception: Exception to convert
        include_internal_details: Whether to include internal details

    Returns:
        Error response dictionary
    """
    if isinstance(exception, SemanticScholarMCPError):
        response = exception.to_dict()
    else:
        wrapped = wrap_exception(exception)
        response = wrapped.to_dict()

    if (
        not include_internal_details
        and "error" in response
        and "details" in response["error"]
    ):
        sensitive_keys = ["stack_trace", "query", "internal_state"]
        for key in sensitive_keys:
            response["error"]["details"].pop(key, None)

    return response
