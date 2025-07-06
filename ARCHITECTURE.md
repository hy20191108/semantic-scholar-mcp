# Semantic Scholar MCP Server Architecture

## Overview

The Semantic Scholar MCP Server is an enterprise-grade implementation following clean architecture principles, with a strong focus on resilience, maintainability, and performance.

## Architecture Principles

### 1. Clean Architecture
- **Dependency Rule**: Dependencies point inward - outer layers depend on inner layers
- **Core Layer**: Contains business entities and rules with no external dependencies
- **Use Cases**: Application-specific business logic isolated from frameworks
- **Interface Adapters**: Convert data between use cases and external systems
- **Frameworks & Drivers**: External tools and frameworks at the outermost layer

### 2. SOLID Principles
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Implementations are interchangeable through interfaces
- **Interface Segregation**: Small, focused interfaces (protocols)
- **Dependency Inversion**: Depend on abstractions, not concretions

### 3. Domain-Driven Design
- **Domain Models**: Rich models representing Semantic Scholar entities
- **Value Objects**: Immutable objects like PaperId, AuthorId
- **Aggregates**: Paper as aggregate root with Citations and References
- **Repository Pattern**: Abstract data access through interfaces

## Layer Architecture

### Core Layer (`src/core/`)
The innermost layer containing:
- **Protocols**: Interface definitions using Python Protocol
- **Exceptions**: Domain-specific exception hierarchy
- **Types**: Type aliases and domain primitives
- **Base Models**: Abstract base classes for entities

No external dependencies allowed in this layer.

### Domain Layer (`src/semantic_scholar_mcp/`)
Business logic and domain models:
- **Domain Models**: Paper, Author, Citation, Reference
- **Business Rules**: Validation logic, invariants
- **Value Objects**: SearchQuery, SearchFilters
- **Domain Services**: Search operations, recommendations

### Application Layer
Use case implementations:
- **API Client**: SemanticScholarClient with business operations
- **MCP Server**: Tool, Resource, and Prompt handlers
- **Orchestration**: Coordinating multiple domain operations

### Infrastructure Layer
External concerns and implementations:
- **HTTP Client**: httpx integration
- **Caching**: In-memory cache implementation
- **Logging**: Structured logging with correlation IDs
- **Configuration**: Environment-based configuration

## Design Patterns

### 1. Repository Pattern
```python
class IRepository(Protocol):
    async def get(self, id: str) -> Optional[Entity]: ...
    async def save(self, entity: Entity) -> None: ...
```

### 2. Factory Pattern
```python
class LoggerFactory:
    def get_logger(self, name: str) -> ILogger:
        # Create configured logger instance
```

### 3. Strategy Pattern
```python
class ExponentialBackoffRetryStrategy:
    def get_delay(self, attempt: int) -> float:
        # Calculate retry delay
```

### 4. Decorator Pattern
```python
@log_performance()
async def search_papers(...):
    # Automatic performance logging
```

### 5. Circuit Breaker Pattern
Prevents cascading failures:
- **Closed**: Normal operation, tracking failures
- **Open**: Fast fail, no downstream calls
- **Half-Open**: Testing recovery with limited requests

### 6. Observer Pattern
Context managers for correlation tracking:
```python
async with RequestContext(correlation_id=correlation_id):
    # All logs include correlation ID
```

## Resilience Patterns

### 1. Circuit Breaker
- Failure threshold: 5 failures
- Recovery timeout: 60 seconds
- Half-open trials: 3 successful requests

### 2. Rate Limiting
- Token bucket algorithm
- Configurable rate and burst
- Async-safe implementation

### 3. Retry Strategy
- Exponential backoff with jitter
- Configurable delays and attempts
- Selective retry based on error type

### 4. Timeouts
- Connection timeout: 10 seconds
- Read timeout: 30 seconds
- Total timeout: 60 seconds

### 5. Caching
- LRU eviction strategy
- TTL-based expiration
- Type-safe cache keys

## Data Flow

### Search Request Flow
1. **MCP Client** → Tool invocation
2. **FastMCP Server** → Route to handler
3. **Tool Handler** → Validate input
4. **API Client** → Check cache
5. **Rate Limiter** → Acquire tokens
6. **Circuit Breaker** → Check state
7. **HTTP Client** → Make request
8. **Retry Logic** → Handle failures
9. **Parser** → Create domain models
10. **Cache** → Store results
11. **Response** → Format and return

### Error Handling Flow
1. **Exception** → Caught at origin
2. **Logging** → Structured error log
3. **Metrics** → Increment counters
4. **Circuit Breaker** → Update state
5. **Retry** → Attempt recovery
6. **Response** → User-friendly error

## Configuration

### Environment-Based
```python
class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
```

### Configuration Hierarchy
1. Default values in code
2. Configuration files
3. Environment variables
4. Runtime parameters

### Secrets Management
- API keys stored as SecretStr
- Never logged or serialized
- Loaded from environment

## Monitoring & Observability

### 1. Structured Logging
- JSON format for machine parsing
- Correlation IDs for request tracking
- Log levels per environment
- Automatic performance logging

### 2. Metrics Collection
- Request counts by status
- Response time histograms
- Cache hit rates
- Circuit breaker state

### 3. Health Checks
- Liveness: Process is running
- Readiness: Can serve requests
- Dependencies: API connectivity

### 4. Tracing
- Correlation IDs across services
- Request/response logging
- Performance measurements
- Error tracking

## Security Considerations

### 1. Input Validation
- Pydantic models for all inputs
- Field-level validation
- Type checking at boundaries

### 2. Rate Limiting
- Protect against abuse
- Configurable limits
- Token bucket algorithm

### 3. Error Handling
- No sensitive data in errors
- Generic messages to users
- Detailed logs internally

### 4. Configuration
- Secrets in environment
- No hardcoded credentials
- Secure defaults

## Performance Optimizations

### 1. Caching Strategy
- Cache search results (5 min)
- Cache paper details (1 hour)
- Skip cache for detailed requests
- LRU eviction

### 2. Connection Pooling
- Persistent HTTP connections
- Configurable pool size
- Keep-alive connections

### 3. Async Operations
- Non-blocking I/O throughout
- Concurrent request handling
- Efficient resource usage

### 4. Batch Operations
- Batch paper retrieval
- Reduce API calls
- Optimize network usage

## Testing Strategy

### 1. Unit Tests
- Test individual components
- Mock external dependencies
- Focus on business logic

### 2. Integration Tests
- Test component interactions
- Use test doubles for APIs
- Verify resilience patterns

### 3. Contract Tests
- Verify API contracts
- Schema validation
- Backward compatibility

### 4. Performance Tests
- Load testing
- Latency measurements
- Resource usage

## Deployment

### 1. Dependencies
- Python >= 3.10
- uv package manager
- Environment variables

### 2. Running
```bash
# Development
uv run mcp dev

# Production
uv run mcp start
```

### 3. Docker Support
```dockerfile
FROM python:3.10-slim
# Multi-stage build
# Non-root user
# Health checks
```

## Future Enhancements

### 1. Features
- WebSocket support for real-time updates
- GraphQL API integration
- Advanced search syntax
- Citation network analysis

### 2. Technical
- Distributed caching (Redis)
- Message queue integration
- Horizontal scaling
- OpenTelemetry integration

### 3. Resilience
- Adaptive circuit breakers
- Predictive rate limiting
- Chaos engineering tests
- Multi-region failover