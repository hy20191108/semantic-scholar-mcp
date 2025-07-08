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


class SemanticScholarConfig(BaseModel):
    """Semantic Scholar API configuration."""

    base_url: str = "https://api.semanticscholar.org/graph/v1"
    api_key: SecretStr | None = Field(default=None, env="SEMANTIC_SCHOLAR_API_KEY")
    timeout: float = Field(default=30.0, gt=0)
    max_connections: int = Field(default=100, ge=1)
    max_keepalive_connections: int = Field(default=20, ge=1)
    default_fields: list[str] = Field(
        default_factory=lambda: [
            "paperId", "title", "abstract", "year", "authors",
            "venue", "citationCount", "influentialCitationCount"
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
        extra="ignore"
    )

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        env="ENVIRONMENT"
    )

    # Component configurations
    server: ServerConfig = Field(default_factory=ServerConfig)
    semantic_scholar: SemanticScholarConfig = Field(default_factory=SemanticScholarConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

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
        self,
        config: ApplicationConfig,
        env: Environment
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
        if config.semantic_scholar.api_key and config.rate_limit.requests_per_second > 1:
            if not config.is_production():
                errors.append(
                    "High rate limit with API key in non-production environment"
                )

        # Validate cache config
        if config.cache.backend == "redis" and not config.cache.redis_url:
            errors.append("Redis URL required when using Redis cache backend")

        # Validate metrics config
        if config.metrics.backend == "prometheus" and config.metrics.prometheus_port < 1024:
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
