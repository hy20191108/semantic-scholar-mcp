"""Base models for the Semantic Scholar MCP server."""

from abc import ABC
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseEntity(BaseModel):
    """Base entity with common fields."""

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Post initialization hook."""
        super().model_post_init(__context)
        if self.updated_at is None:
            self.updated_at = self.created_at


class CacheableModel(BaseModel, ABC):
    """Base model for cacheable entities."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid"
    )

    cache_key: str | None = Field(default=None, exclude=True)
    cache_ttl: int = Field(default=3600, exclude=True)  # 1 hour default

    def generate_cache_key(self) -> str:
        """Generate a unique cache key for this model."""
        return f"{self.__class__.__name__}:{uuid4()!s}"

    def model_post_init(self, __context: Any) -> None:
        """Generate cache key after initialization."""
        super().model_post_init(__context)
        if self.cache_key is None:
            self.cache_key = self.generate_cache_key()


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    success: bool = Field(default=True)
    data: T | None = Field(default=None)
    error: dict[str, Any] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def success_response(
        cls,
        data: T,
        metadata: dict[str, Any] | None = None
    ) -> "ApiResponse[T]":
        """Create a successful response."""
        return cls(
            success=True,
            data=data,
            error=None,
            metadata=metadata
        )

    @classmethod
    def error_response(
        cls,
        error_code: str,
        error_message: str,
        details: dict[str, Any] | None = None
    ) -> "ApiResponse[T]":
        """Create an error response."""
        return cls(
            success=False,
            data=None,
            error={
                "code": error_code,
                "message": error_message,
                "details": details or {}
            }
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    model_config = ConfigDict(
        validate_assignment=True,
        arbitrary_types_allowed=True
    )

    items: list[T] = Field(default_factory=list)
    total: int = Field(ge=0)
    offset: int = Field(ge=0, default=0)
    limit: int = Field(ge=1, le=1000, default=10)
    has_more: bool = Field(default=False)

    def model_post_init(self, __context: Any) -> None:
        """Calculate has_more after initialization."""
        super().model_post_init(__context)
        self.has_more = (self.offset + len(self.items)) < self.total
