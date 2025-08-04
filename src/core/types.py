"""Type definitions and aliases for the Semantic Scholar MCP server."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

if TYPE_CHECKING:
    from pydantic import BaseModel

# Generic type variables
T = TypeVar("T")
TModel = TypeVar("TModel", bound="BaseModel")

# Type aliases for common structures
JSON: TypeAlias = dict[str, Any]
JSONList: TypeAlias = list[JSON]
PaperId: TypeAlias = str
AuthorId: TypeAlias = str
FieldsOfStudy: TypeAlias = list[str]

# Semantic Scholar specific types
CitationCount: TypeAlias = int
Year: TypeAlias = int
Venue: TypeAlias = str | None
Abstract: TypeAlias = str | None
Url: TypeAlias = str

# API response types
SearchResult: TypeAlias = dict[str, int | list[JSON]]
PaperDetails: TypeAlias = JSON
AuthorDetails: TypeAlias = JSON
CitationsList: TypeAlias = JSONList
ReferencesList: TypeAlias = JSONList
RecommendationsList: TypeAlias = JSONList

# Error types
ErrorCode: TypeAlias = str
ErrorMessage: TypeAlias = str
ErrorDetails: TypeAlias = JSON | None

# Configuration types
ApiKey: TypeAlias = str | None
Timeout: TypeAlias = float
RetryCount: TypeAlias = int
RateLimit: TypeAlias = int

# Cache types
CacheKey: TypeAlias = str
CacheTTL: TypeAlias = int
CacheValue: TypeAlias = Any

# Pagination types
Offset: TypeAlias = int
Limit: TypeAlias = int
Total: TypeAlias = int

# Field selection types
Fields: TypeAlias = list[str]
IncludeFields: TypeAlias = Fields | None
ExcludeFields: TypeAlias = Fields | None

# Sort options
SortBy: TypeAlias = str
SortOrderDirection: TypeAlias = str

# Pagination and sorting types


@dataclass
class PaginationParams:
    """Pagination parameters."""

    page: int = 1
    page_size: int = 10
    offset: int | None = None
    limit: int | None = None


@dataclass
class SortOrder:
    """Sort order specification."""

    field: str
    direction: str = "asc"  # asc or desc


@dataclass
class SearchQuery:
    """Search query specification."""

    query: str
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None


# Metric names
MetricName: TypeAlias = str


class MetricNames:
    """Specific metric names for monitoring."""

    API_REQUEST_COUNT = "api.request.count"
    API_REQUEST_DURATION = "api.request.duration"
    API_REQUEST_ERROR = "api.request.error"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"


# Common field sets for API requests
BASIC_PAPER_FIELDS: list[str] = [
    "paperId",
    "title",
    "abstract",
    "year",
    "authors",
    "venue",
    "publicationTypes",
    "citationCount",
    "influentialCitationCount",
]

DETAILED_PAPER_FIELDS: list[str] = [
    *BASIC_PAPER_FIELDS,
    "externalIds",
    "url",
    "publicationDate",
    "referenceCount",
    "fieldsOfStudy",
]

AUTHOR_FIELDS: list[str] = [
    "authorId",
    "name",
    "affiliations",
    "paperCount",
]

CITATION_FIELDS: list[str] = [
    "paperId",
    "title",
    "year",
    "authors",
    "venue",
    "citationCount",
    "isInfluential",
]


# Enum-like types for API compatibility
class ExternalIdType:
    """External ID types supported by Semantic Scholar API."""

    DOI = "DOI"
    ARXIV = "ArXiv"
    MAG = "MAG"
    ACMID = "ACM"
    PUBMED = "PubMed"
    PUBMED_CENTRAL = "PubMedCentral"
    DBLP = "DBLP"
    CORPUS_ID = "CorpusId"


class PublicationType:
    """Publication types supported by Semantic Scholar API."""

    JOURNAL_ARTICLE = "JournalArticle"
    CONFERENCE = "Conference"
    REVIEW = "Review"
    DATASET = "Dataset"
    BOOK = "Book"
    BOOK_CHAPTER = "BookChapter"
    THESIS = "Thesis"
    EDITORIAL = "Editorial"
    NEWS = "News"
    STUDY = "Study"
    LETTER = "Letter"
    REPOSITORY = "Repository"
    UNKNOWN = "Unknown"


class FieldOfStudyType:
    """Field of study types."""

    COMPUTER_SCIENCE = "Computer Science"
    MEDICINE = "Medicine"
    CHEMISTRY = "Chemistry"
    BIOLOGY = "Biology"
    MATERIALS_SCIENCE = "Materials Science"
    PHYSICS = "Physics"
    GEOLOGY = "Geology"
    PSYCHOLOGY = "Psychology"
    ART = "Art"
    HISTORY = "History"
    GEOGRAPHY = "Geography"
    SOCIOLOGY = "Sociology"
    BUSINESS = "Business"
    POLITICAL_SCIENCE = "Political Science"
    ECONOMICS = "Economics"
    PHILOSOPHY = "Philosophy"
    MATHEMATICS = "Mathematics"
    ENGINEERING = "Engineering"
    ENVIRONMENTAL_SCIENCE = "Environmental Science"
    AGRICULTURAL_SCIENCE = "Agricultural and Food Sciences"
    EDUCATION = "Education"
    LAW = "Law"
    LINGUISTICS = "Linguistics"


class VenueType:
    """Venue types."""

    JOURNAL = "journal"
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    BOOK = "book"
    UNKNOWN = "unknown"


class SortType:
    """Sort types for API requests."""

    RELEVANCE = "relevance"
    CITATION_COUNT = "citationCount"
    YEAR = "year"
    PUBLICATION_DATE = "publicationDate"


class MetricType:
    """Metric types for performance tracking."""

    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_COUNT = "error_count"
    CACHE_HIT_RATE = "cache_hit_rate"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class LogLevel:
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat:
    """Log formats."""

    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class ValidationRule:
    """Validation rules."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"


class DataSource:
    """Data sources."""

    SEMANTIC_SCHOLAR = "semantic_scholar"
    CACHE = "cache"
    FALLBACK = "fallback"


class APIEndpoint:
    """API endpoints."""

    SEARCH = "/graph/v1/paper/search"
    PAPER = "/graph/v1/paper"
    AUTHOR = "/graph/v1/author"
    CITATIONS = "/citations"
    REFERENCES = "/references"
    RECOMMENDATIONS = "/recommendations"
    DATASETS = "/datasets/v1"


class ResponseFormat:
    """Response formats."""

    JSON = "json"
    XML = "xml"
    CSV = "csv"


class RequestMethod:
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class AuthType:
    """Authentication types."""

    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC = "basic"
    OAUTH = "oauth"


class RateLimitType:
    """Rate limit types."""

    REQUESTS_PER_SECOND = "requests_per_second"
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"


class CircuitBreakerState:
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class RetryStrategy:
    """Retry strategies."""

    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"


class ErrorSeverity:
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceMetric:
    """Performance metrics."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"


class HealthStatus:
    """Health status indicators."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CacheStrategy:
    """Cache strategies."""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    LIFO = "lifo"
    TTL = "ttl"


class ModelType:
    """Model types."""

    PAPER = "paper"
    AUTHOR = "author"
    CITATION = "citation"
    REFERENCE = "reference"
    DATASET = "dataset"


class SerializationFormat:
    """Serialization formats."""

    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    AVRO = "avro"


class CompressionType:
    """Compression types."""

    GZIP = "gzip"
    LZ4 = "lz4"
    SNAPPY = "snappy"
    NONE = "none"


class EncryptionType:
    """Encryption types."""

    AES = "aes"
    RSA = "rsa"
    NONE = "none"


class SecurityLevel:
    """Security levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class ComplianceLevel:
    """Compliance levels."""

    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class AuditEvent:
    """Audit event types."""

    ACCESS = "access"
    MODIFICATION = "modification"
    DELETION = "deletion"
    CREATION = "creation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"


class ResourceType:
    """Resource types."""

    PAPER = "paper"
    AUTHOR = "author"
    DATASET = "dataset"
    API_ENDPOINT = "api_endpoint"
    CACHE = "cache"


class TaskType:
    """Task types."""

    SEARCH = "search"
    RETRIEVAL = "retrieval"
    PROCESSING = "processing"
    CACHING = "caching"
    VALIDATION = "validation"


class ProcessingState:
    """Processing states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueType:
    """Queue types."""

    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"
    ROUND_ROBIN = "round_robin"


class NotificationType:
    """Notification types."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class IntegrationType:
    """Integration types."""

    MCP = "mcp"
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    BATCH = "batch"
    STREAMING = "streaming"


class DeploymentType:
    """Deployment types."""

    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"
    EDGE = "edge"
    CONTAINER = "container"
    SERVERLESS = "serverless"
