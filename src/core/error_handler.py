"""Comprehensive error handler for MCP operations."""

import asyncio
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
from typing import Any, TypeVar

from .exceptions import (
    MCPPromptError,
    MCPResourceError,
    MCPToolError,
    RetryExhaustedError,
    SemanticScholarMCPError,
    ValidationError,
    create_error_response,
)
from .logging import (
    correlation_id_var,
    execution_id_var,
    get_logger,
    mcp_operation_var,
    request_id_var,
    tool_name_var,
)

T = TypeVar("T")

logger = get_logger(__name__)


class ErrorRecoveryStrategy:
    """Strategy for handling and recovering from errors."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        exponential_backoff: bool = True,
        recovery_actions: list[Callable] | None = None,
    ):
        """Initialize error recovery strategy.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries (seconds)
            exponential_backoff: Whether to use exponential backoff
            recovery_actions: List of recovery actions to attempt
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff
        self.recovery_actions = recovery_actions or []

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            RetryExhaustedError: When all retries are exhausted
        """
        retry_history = []
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = (
                        self.retry_delay * (2 ** (attempt - 1))
                        if self.exponential_backoff
                        else self.retry_delay
                    )
                    logger.info(
                        f"Retrying after {delay}s (attempt {attempt}/"
                        f"{self.max_retries})"
                    )
                    await asyncio.sleep(delay)

                result = (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )

                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt}")

                return result

            except Exception as error:
                last_error = error
                retry_history.append(
                    {
                        "attempt": attempt,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

                if attempt < self.max_retries:
                    logger.warning(f"Attempt {attempt} failed: {error}")
                    # Try recovery actions
                    for recovery_action in self.recovery_actions:
                        try:
                            await recovery_action(error)
                        except Exception as recovery_error:
                            logger.warning(f"Recovery action failed: {recovery_error}")

        raise RetryExhaustedError(
            message=f"All {self.max_retries} retry attempts failed",
            max_retries=self.max_retries,
            last_error=last_error,
            retry_history=retry_history,
        )


class MCPErrorHandler:
    """Comprehensive error handler for MCP operations."""

    def __init__(self, recovery_strategy: ErrorRecoveryStrategy | None = None):
        """Initialize MCP error handler.

        Args:
            recovery_strategy: Strategy for error recovery
        """
        self.recovery_strategy = recovery_strategy or ErrorRecoveryStrategy()
        self.error_metrics = {
            "total_errors": 0,
            "errors_by_type": {},
            "recovery_attempts": 0,
            "recovery_successes": 0,
        }

    def _update_metrics(
        self,
        error: Exception,
        recovery_attempted: bool = False,
        recovery_success: bool = False,
    ):
        """Update error metrics.

        Args:
            error: Exception that occurred
            recovery_attempted: Whether recovery was attempted
            recovery_success: Whether recovery was successful
        """
        self.error_metrics["total_errors"] += 1
        error_type = type(error).__name__
        self.error_metrics["errors_by_type"][error_type] = (
            self.error_metrics["errors_by_type"].get(error_type, 0) + 1
        )

        if recovery_attempted:
            self.error_metrics["recovery_attempts"] += 1
            if recovery_success:
                self.error_metrics["recovery_successes"] += 1

    def get_metrics(self) -> dict[str, Any]:
        """Get current error metrics.

        Returns:
            Dictionary of error metrics
        """
        return self.error_metrics.copy()

    async def handle_mcp_tool_error(
        self,
        error: Exception,
        tool_name: str,
        arguments: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle MCP tool execution errors.

        Args:
            error: Exception that occurred
            tool_name: Name of the tool
            arguments: Tool arguments
            context: Additional context

        Returns:
            Error response dictionary
        """
        execution_id = str(uuid.uuid4())
        error_context = {
            "tool_name": tool_name,
            "arguments": arguments,
            "execution_id": execution_id,
            **(context or {}),
        }

        # Set context variables
        tool_name_var.set(tool_name)
        execution_id_var.set(execution_id)
        mcp_operation_var.set("tool_execution")

        # Log error with context
        logger.log_error_with_context(
            error,
            context=error_context,
            error_id=execution_id,
            recovery_actions=["retry", "fallback", "circuit_breaker"],
        )

        # Wrap exception if needed
        if not isinstance(error, SemanticScholarMCPError):
            mcp_error = MCPToolError(
                message=str(error),
                tool_name=tool_name,
                arguments=arguments,
                execution_id=execution_id,
                inner_exception=error,
            )
        else:
            mcp_error = error

        # Update metrics
        self._update_metrics(mcp_error)

        # Create error response
        response = create_error_response(mcp_error, include_internal_details=False)

        # Add success flag
        response["success"] = False

        return response

    async def handle_mcp_resource_error(
        self,
        error: Exception,
        resource_uri: str,
        resource_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle MCP resource errors.

        Args:
            error: Exception that occurred
            resource_uri: URI of the resource
            resource_type: Type of resource
            context: Additional context

        Returns:
            Error response dictionary
        """
        error_context = {
            "resource_uri": resource_uri,
            "resource_type": resource_type,
            **(context or {}),
        }

        # Set context variables
        mcp_operation_var.set("resource_access")

        # Log error with context
        logger.log_error_with_context(
            error,
            context=error_context,
            recovery_actions=["retry", "alternate_resource"],
        )

        # Wrap exception if needed
        if not isinstance(error, SemanticScholarMCPError):
            mcp_error = MCPResourceError(
                message=str(error),
                resource_uri=resource_uri,
                resource_type=resource_type,
                inner_exception=error,
            )
        else:
            mcp_error = error

        # Update metrics
        self._update_metrics(mcp_error)

        return create_error_response(mcp_error, include_internal_details=False)

    async def handle_mcp_prompt_error(
        self,
        error: Exception,
        prompt_name: str,
        prompt_args: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle MCP prompt errors.

        Args:
            error: Exception that occurred
            prompt_name: Name of the prompt
            prompt_args: Prompt arguments
            context: Additional context

        Returns:
            Error response dictionary
        """
        error_context = {
            "prompt_name": prompt_name,
            "prompt_args": prompt_args,
            **(context or {}),
        }

        # Set context variables
        mcp_operation_var.set("prompt_execution")

        # Log error with context
        logger.log_error_with_context(
            error,
            context=error_context,
            recovery_actions=["validate_args", "retry"],
        )

        # Wrap exception if needed
        if not isinstance(error, SemanticScholarMCPError):
            mcp_error = MCPPromptError(
                message=str(error),
                prompt_name=prompt_name,
                prompt_args=prompt_args,
                inner_exception=error,
            )
        else:
            mcp_error = error

        # Update metrics
        self._update_metrics(mcp_error)

        return create_error_response(mcp_error, include_internal_details=False)

    async def handle_validation_error(
        self,
        error: Exception,
        field: str | None = None,
        value: Any = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle validation errors.

        Args:
            error: Exception that occurred
            field: Field that failed validation
            value: Invalid value
            context: Additional context

        Returns:
            Error response dictionary
        """
        error_context = {
            "field": field,
            "value": value,
            **(context or {}),
        }

        # Log error with context
        logger.log_error_with_context(
            error,
            context=error_context,
            recovery_actions=["validate_input", "provide_default"],
        )

        # Wrap exception if needed
        if not isinstance(error, ValidationError):
            validation_error = ValidationError(
                message=str(error),
                field=field,
                value=value,
                inner_exception=error,
            )
        else:
            validation_error = error

        # Update metrics
        self._update_metrics(validation_error)

        return create_error_response(validation_error, include_internal_details=False)


def mcp_error_handler(
    error_handler: MCPErrorHandler | None = None,
    recovery_strategy: ErrorRecoveryStrategy | None = None,
    tool_name: str | None = None,
):
    """Decorator for MCP error handling.

    Args:
        error_handler: Error handler instance
        recovery_strategy: Recovery strategy
        tool_name: Name of the tool (auto-detected if not provided)

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = error_handler or MCPErrorHandler(recovery_strategy)
        actual_tool_name = tool_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Generate execution context
            execution_id = str(uuid.uuid4())
            correlation_id = correlation_id_var.get() or str(uuid.uuid4())
            request_id = request_id_var.get() or str(uuid.uuid4())

            # Set context variables
            correlation_id_var.set(correlation_id)
            request_id_var.set(request_id)
            execution_id_var.set(execution_id)
            tool_name_var.set(actual_tool_name)
            mcp_operation_var.set("tool_execution")

            try:
                # Execute function with retry logic
                result = await handler.recovery_strategy.execute_with_retry(
                    func, *args, **kwargs
                )

                # Log successful execution
                logger.info(f"Tool {actual_tool_name} executed successfully")

                return result

            except Exception as error:
                # Handle the error
                return await handler.handle_mcp_tool_error(
                    error=error,
                    tool_name=actual_tool_name,
                    arguments={"args": args, "kwargs": kwargs},
                    context={
                        "execution_id": execution_id,
                        "correlation_id": correlation_id,
                        "request_id": request_id,
                    },
                )

                # Return error response instead of raising

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            # For synchronous functions, run the async wrapper
            return asyncio.run(async_wrapper(*args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validation_error_handler(
    field: str | None = None,
    error_handler: MCPErrorHandler | None = None,
):
    """Decorator for validation error handling.

    Args:
        field: Field name being validated
        error_handler: Error handler instance

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        handler = error_handler or MCPErrorHandler()

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as error:
                # Handle validation error
                return await handler.handle_validation_error(
                    error=error,
                    field=field,
                    value=kwargs.get("value") or (args[0] if args else None),
                    context={
                        "function": func.__name__,
                        "args": args,
                        "kwargs": kwargs,
                    },
                )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as error:
                # Handle validation error synchronously
                return asyncio.run(
                    handler.handle_validation_error(
                        error=error,
                        field=field,
                        value=kwargs.get("value") or (args[0] if args else None),
                        context={
                            "function": func.__name__,
                            "args": args,
                            "kwargs": kwargs,
                        },
                    )
                )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Global error handler instance
global_error_handler = MCPErrorHandler()


def set_global_error_handler(handler: MCPErrorHandler) -> None:
    """Set the global error handler.

    Args:
        handler: Error handler instance
    """
    global global_error_handler
    global_error_handler = handler


def get_global_error_handler() -> MCPErrorHandler:
    """Get the global error handler.

    Returns:
        Global error handler instance
    """
    return global_error_handler


# Alias for backward compatibility
ErrorHandler = MCPErrorHandler
