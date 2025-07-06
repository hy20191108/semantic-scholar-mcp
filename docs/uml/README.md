# UML Diagrams

This directory contains UML diagrams for the Semantic Scholar MCP Server architecture.

## Diagrams

### 1. Class Diagram (`class-diagram.puml`)
Shows the complete class structure including:
- Protocol interfaces (ILogger, ICache, ICircuitBreaker, etc.)
- Domain models (Paper, Author, Citation, Reference)
- Infrastructure components (SemanticScholarClient, CircuitBreaker, RateLimiter)
- Configuration classes
- Relationships and dependencies

### 2. Sequence Diagram - Search Papers (`sequence-diagram-search.puml`)
Illustrates the flow of a paper search request:
- Request handling through MCP layers
- Caching behavior
- Rate limiting and circuit breaker patterns
- Error handling and retry logic
- Response formatting

### 3. Component Diagram (`component-diagram.puml`)
Shows the high-level architecture:
- Layered architecture (MCP, Business Logic, Resilience, Infrastructure, Core)
- External system integration
- Dependency flow following clean architecture principles

### 4. Activity Diagram - Paper Retrieval (`activity-diagram-paper-retrieval.puml`)
Details the workflow for retrieving a paper with optional citations/references:
- Validation steps
- Cache checking logic
- Resilience pattern execution
- Parallel data fetching
- Error handling paths

### 5. State Diagram - Circuit Breaker (`state-diagram-circuit-breaker.puml`)
Shows the circuit breaker state machine:
- CLOSED state (normal operation)
- OPEN state (fast failing)
- HALF_OPEN state (recovery testing)
- State transitions and conditions

### 6. Deployment Diagram (`deployment-diagram.puml`)
Illustrates the deployment architecture:
- Client environments (Claude Desktop, VS Code, Terminal)
- Server components
- External service integration
- Communication protocols

## Viewing the Diagrams

### Option 1: PlantUML Online
1. Visit https://www.plantuml.com/plantuml/uml/
2. Copy the contents of any `.puml` file
3. Paste into the editor

### Option 2: VS Code Extension
1. Install the PlantUML extension
2. Open any `.puml` file
3. Press `Alt+D` to preview

### Option 3: Generate Images
```bash
# Install PlantUML
brew install plantuml  # macOS
apt-get install plantuml  # Ubuntu

# Generate PNG images
plantuml -tpng *.puml

# Generate SVG images
plantuml -tsvg *.puml
```

## Architecture Highlights

### Enterprise Patterns
- **Dependency Injection**: All dependencies injected through constructors
- **Interface Segregation**: Small, focused protocol interfaces
- **Repository Pattern**: Clear separation of data access
- **Factory Pattern**: LoggerFactory for creating configured loggers

### Resilience Patterns
- **Circuit Breaker**: Prevents cascading failures
- **Rate Limiting**: Token bucket algorithm
- **Retry with Backoff**: Exponential backoff with jitter
- **Caching**: Multi-level caching strategy

### Clean Architecture
- Dependencies point inward
- Core layer has no external dependencies
- Business logic isolated from infrastructure
- Clear boundaries between layers