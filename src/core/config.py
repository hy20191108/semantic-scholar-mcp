"""Configuration management system."""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

T = TypeVar("T", bound=BaseSettings)


class Environment(str, Enum):
    """Application environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

    @classmethod
    def from_string(cls, value: str) -> "Environment":
        """Create environment from string."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DEVELOPMENT


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    ttl_seconds: int = Field(default=3600, ge=0)
    max_size: int = Field(default=1000, ge=1)
    backend: str = "memory"  # memory, redis
    redis_url: str | None = None
    key_prefix: str = "semantic_scholar"


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""

    enabled: bool = True
    requests_per_second: float = Field(default=1.0, gt=0)
    burst_size: int = Field(default=10, ge=1)
    per_api_key: bool = True


class RetryConfig(BaseModel):
    """Retry configuration."""

    max_attempts: int = Field(default=3, ge=1)
    initial_delay: float = Field(default=1.0, gt=0)
    max_delay: float = Field(default=60.0, gt=0)
    exponential_base: float = Field(default=2.0, gt=1)
    jitter: bool = True


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""

    enabled: bool = True
    failure_threshold: int = Field(default=5, ge=1)
    recovery_timeout: float = Field(default=60.0, gt=0)
    expected_exception_types: list[str] = Field(
        default_factory=lambda: ["httpx.HTTPStatusError", "httpx.TimeoutException"]
    )


class SemanticScholarConfig(BaseSettings):
    """Semantic Scholar API configuration.

    Automatically loads settings from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str = "https://api.semanticscholar.org/graph/v1"
    api_key: SecretStr | None = Field(
        default=None,
        alias="SEMANTIC_SCHOLAR_API_KEY",
        validation_alias="SEMANTIC_SCHOLAR_API_KEY",
    )
    timeout: float = Field(default=30.0, gt=0)
    max_connections: int = Field(default=100, ge=1)
    max_keepalive_connections: int = Field(default=20, ge=1)
    default_fields: list[str] = Field(
        default_factory=lambda: [
            "paperId",
            "title",
            "abstract",
            "year",
            "authors",
            "venue",
            "citationCount",
            "influentialCitationCount",
        ]
    )


class MetricsConfig(BaseModel):
    """Metrics configuration."""

    enabled: bool = True
    backend: str = "memory"  # memory, prometheus, statsd
    export_interval: float = Field(default=60.0, gt=0)
    prometheus_port: int = Field(default=9090, ge=1024, le=65535)
    statsd_host: str = "localhost"
    statsd_port: int = Field(default=8125, ge=1024, le=65535)
    prefix: str = "semantic_scholar_mcp"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = LogLevel.INFO
    format: str = "json"  # json, text
    include_timestamp: bool = True
    include_context: bool = True
    file_path: Path | None = None
    max_file_size: int = Field(default=10 * 1024 * 1024, ge=1)  # 10MB
    backup_count: int = Field(default=5, ge=0)

    # MCP-specific debug configuration
    debug_mcp_mode: bool = Field(
        default=False, json_schema_extra={"env": "DEBUG_MCP_MODE"}
    )
    log_mcp_messages: bool = Field(
        default=False, json_schema_extra={"env": "LOG_MCP_MESSAGES"}
    )
    log_api_payloads: bool = Field(
        default=False, json_schema_extra={"env": "LOG_API_PAYLOADS"}
    )
    log_performance_metrics: bool = Field(
        default=False, json_schema_extra={"env": "LOG_PERFORMANCE_METRICS"}
    )
    debug_level_override: LogLevel | None = Field(
        default=None, json_schema_extra={"env": "DEBUG_LEVEL_OVERRIDE"}
    )


class PDFProcessingConfig(BaseModel):
    """Configuration for PDF processing and artifact storage."""

    enabled: bool = True
    max_pdf_size_mb: int = Field(default=25, ge=1)
    max_pages: int | None = Field(default=None, ge=1)
    request_timeout_seconds: float = Field(default=120.0, gt=0)
    download_chunk_size: int = Field(default=1024 * 64, ge=4096)
    pdf_dir: Path = Field(
        default=Path(".semantic_scholar_mcp/artifacts/pdfs"),
        json_schema_extra={"env": "PDF_PROCESSING__PDF_DIR"},
    )
    markdown_dir: Path = Field(
        default=Path(".semantic_scholar_mcp/artifacts/markdown"),
        json_schema_extra={"env": "PDF_PROCESSING__MARKDOWN_DIR"},
    )
    cache_index_file: Path = Field(
        default=Path(".semantic_scholar_mcp/cache/pdf_index.json"),
        json_schema_extra={"env": "PDF_PROCESSING__CACHE_INDEX_FILE"},
    )
    image_dir_name: str = Field(default="images")
    image_format: str = Field(default="png")
    artifact_ttl_hours: int | None = Field(
        default=None,
        json_schema_extra={"env": "PDF_PROCESSING__ARTIFACT_TTL_HOURS"},
    )
    enable_memory_capture: bool = Field(
        default=True, json_schema_extra={"env": "PDF_PROCESSING__ENABLE_MEMORY_CAPTURE"}
    )
    memory_dir: Path = Field(
        default=Path(".semantic_scholar_mcp/memories"),
        json_schema_extra={"env": "PDF_PROCESSING__MEMORY_DIR"},
    )
    default_output_mode: str = Field(
        default="chunks", json_schema_extra={"env": "PDF_PROCESSING__DEFAULT_OUTPUT"}
    )
    store_markdown_artifacts: bool = Field(
        default=True, json_schema_extra={"env": "PDF_PROCESSING__STORE_MARKDOWN"}
    )
    store_chunk_artifacts: bool = Field(
        default=True, json_schema_extra={"env": "PDF_PROCESSING__STORE_CHUNKS"}
    )
    chunk_preview_length: int = Field(default=280, ge=64, le=2000)


class DashboardConfig(BaseModel):
    """Dashboard configuration."""

    enabled: bool = False
    host: str = Field(default="0.0.0.0")  # noqa: S104
    port: int = Field(
        default=25000, ge=1024, le=65535
    )  # Changed from 24282 to avoid Serena conflict
    auto_refresh_seconds: int = Field(default=5, ge=1)
    max_log_messages: int = Field(default=1000, ge=100)
    enable_log_collection: bool = True
    open_on_launch: bool = True


class ServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = "semantic-scholar-mcp"
    version: str = "0.1.0"
    description: str = "MCP server for Semantic Scholar API"
    max_concurrent_requests: int = Field(default=10, ge=1)
    request_timeout: float = Field(default=300.0, gt=0)
    shutdown_timeout: float = Field(default=30.0, gt=0)


class ApplicationConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, json_schema_extra={"env": "ENVIRONMENT"}
    )

    # Direct API key field for backward compatibility
    semantic_scholar_api_key: SecretStr | None = Field(
        default=None, alias="SEMANTIC_SCHOLAR_API_KEY"
    )

    # Component configurations
    server: ServerConfig = Field(default_factory=ServerConfig)
    semantic_scholar: SemanticScholarConfig = Field(
        default_factory=SemanticScholarConfig
    )
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    pdf_processing: PDFProcessingConfig = Field(default_factory=PDFProcessingConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)

    # Feature flags
    enable_cache: bool = True
    enable_rate_limiting: bool = True
    enable_circuit_breaker: bool = True
    enable_metrics: bool = True
    enable_health_checks: bool = True

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment(cls, v: Any) -> Environment:
        """Validate and convert environment."""
        if isinstance(v, str):
            return Environment.from_string(v)
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization to copy API key to nested config."""
        super().model_post_init(__context)
        # Copy API key from top-level to nested config if present
        if self.semantic_scholar_api_key and not self.semantic_scholar.api_key:
            self.semantic_scholar.api_key = self.semantic_scholar_api_key

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT

    def get_log_level(self) -> str:
        """Get appropriate log level for environment."""
        if self.is_production():
            return LogLevel.WARNING.value
        if self.environment == Environment.STAGING:
            return LogLevel.INFO.value
        return LogLevel.DEBUG.value


class ConfigurationManager:
    """Configuration manager with environment-specific overrides."""

    def __init__(self, base_path: Path | None = None):
        """Initialize configuration manager."""
        self._base_path = base_path or Path.cwd()
        self._configs: dict[Environment, ApplicationConfig] = {}
        self._current_env = Environment.from_string(
            os.getenv("ENVIRONMENT", "development")
        )

    @lru_cache(maxsize=1)
    def load_config(self, env: Environment | None = None) -> ApplicationConfig:
        """Load configuration for environment."""
        env = env or self._current_env

        if env not in self._configs:
            # Load base configuration
            config = ApplicationConfig()

            # Apply environment-specific overrides
            env_file = self._base_path / f".env.{env.value}"
            if env_file.exists():
                config = ApplicationConfig(_env_file=str(env_file))

            # Apply environment-specific adjustments
            self._apply_environment_defaults(config, env)

            self._configs[env] = config

        return self._configs[env]

    def _apply_environment_defaults(
        self, config: ApplicationConfig, env: Environment
    ) -> None:
        """Apply environment-specific defaults."""
        config.environment = env

        if env == Environment.PRODUCTION:
            # Production settings
            config.logging.level = LogLevel.WARNING
            config.cache.ttl_seconds = 7200  # 2 hours
            config.rate_limit.requests_per_second = 0.5
            config.circuit_breaker.failure_threshold = 3

        elif env == Environment.DEVELOPMENT:
            # Development settings
            config.logging.level = LogLevel.DEBUG
            config.cache.ttl_seconds = 300  # 5 minutes
            config.rate_limit.enabled = False
            config.metrics.enabled = False

        elif env == Environment.TESTING:
            # Testing settings
            config.logging.level = LogLevel.DEBUG
            config.cache.enabled = False
            config.rate_limit.enabled = False
            config.circuit_breaker.enabled = False
            config.metrics.enabled = False

    def get_current_config(self) -> ApplicationConfig:
        """Get configuration for current environment."""
        return self.load_config()

    def validate_config(self, config: ApplicationConfig) -> list[str]:
        """Validate configuration and return errors."""
        errors = []

        # Validate Semantic Scholar config
        if (
            config.semantic_scholar.api_key
            and config.rate_limit.requests_per_second > 1
        ) and not config.is_production():
            errors.append("High rate limit with API key in non-production environment")

        # Validate cache config
        if config.cache.backend == "redis" and not config.cache.redis_url:
            errors.append("Redis URL required when using Redis cache backend")

        # Validate metrics config
        if (
            config.metrics.backend == "prometheus"
            and config.metrics.prometheus_port < 1024
        ):
            errors.append("Prometheus port should be >= 1024")

        return errors


# Global configuration instance
_config_manager = ConfigurationManager()


def get_config() -> ApplicationConfig:
    """Get current application configuration."""
    return _config_manager.get_current_config()


def set_config_path(path: Path) -> None:
    """Set configuration base path."""
    global _config_manager
    _config_manager = ConfigurationManager(path)
