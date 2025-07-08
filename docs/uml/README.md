# UML Diagrams

This directory contains UML diagrams for the Semantic Scholar MCP Server architecture.

**📋 Dual Format Support**: Each diagram is provided in both editable `.puml` source files and GitHub-ready `.svg` rendered files.

## Diagrams

### Overview Diagrams

#### 1. Class Diagram (`01-overview-class-diagram.puml` / `.svg`)
Shows the complete class structure including:
- Protocol interfaces (ILogger, ICache, ICircuitBreaker, etc.)
- Domain models (Paper, Author, Citation, Reference)
- Infrastructure components (SemanticScholarClient, CircuitBreaker, RateLimiter)
- Configuration classes
- Relationships and dependencies

#### 2. Component Diagram (`02-overview-component-diagram.puml` / `.svg`)
Shows the high-level architecture:
- Layered architecture (MCP, Business Logic, Resilience, Infrastructure, Core)
- External system integration
- Dependency flow following clean architecture principles

#### 3. Deployment Diagram (`03-overview-deployment-diagram.puml` / `.svg`)
Illustrates the deployment architecture:
- Client environments (Claude Desktop, VS Code, Terminal)
- Server components
- External service integration
- Communication protocols

### Flow Diagrams

#### 4. Paper Search Sequence Diagram (`04-flow-paper-search-sequence.puml` / `.svg`)
Illustrates the flow of a paper search request:
- Request handling through MCP layers
- Caching behavior
- Rate limiting and circuit breaker patterns
- Error handling and retry logic
- Response formatting

#### 5. Paper Retrieval Activity Diagram (`05-flow-paper-retrieval-activity.puml` / `.svg`)
Details the workflow for retrieving a paper with optional citations/references:
- Validation steps
- Cache checking logic
- Resilience pattern execution
- Parallel data fetching
- Error handling paths

### Pattern Diagrams

#### 6. Circuit Breaker State Diagram (`06-pattern-circuit-breaker-state.puml` / `.svg`)
Shows the circuit breaker state machine:
- CLOSED state (normal operation)
- OPEN state (fast failing)
- HALF_OPEN state (recovery testing)
- State transitions and conditions

## Viewing the Diagrams

### 🎯 Recommended: SVG Files (GitHub Ready)
**Easiest approach**: Simply open any `.svg` file directly on GitHub for high-quality diagram viewing.
- Scalable vector graphics with zoom capability
- Instant browser rendering
- No additional tools required

**Example**: Click `01-overview-class-diagram.svg` to view the class diagram immediately.

### PlantUML Source Files
Use `.puml` files when editing or converting to other formats is needed:

#### Option 1: PlantUML Online
1. Visit https://www.plantuml.com/plantuml/uml/
2. Copy the contents of any `.puml` file
3. Paste into the editor

#### Option 2: VS Code Extension
1. Install the PlantUML extension
2. Open any `.puml` file
3. Press `Alt+D` to preview

#### Option 3: Generate Images Locally
```bash
# Install PlantUML
brew install plantuml  # macOS
apt-get install plantuml  # Ubuntu

# Or download JAR directly (no sudo required)
wget -O plantuml.jar "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"

# Generate PNG images
java -jar plantuml.jar -tpng *.puml

# Generate SVG images (already provided)
java -jar plantuml.jar -tsvg *.puml
```

## Diagram Organization

The diagrams are organized with a clear naming convention:
- **Numbering**: Sequential numbers (01-06) for logical viewing order
- **Categories**: 
  - `overview-*`: High-level architectural views
  - `flow-*`: Process and interaction flows
  - `pattern-*`: Specific design patterns and state machines
- **Descriptive names**: Clear indication of diagram content and purpose
- **Dual formats**: Both `.puml` (source) and `.svg` (rendered) for each diagram

## File Structure
```
docs/uml/
├── 01-overview-class-diagram.puml       # Class diagram source
├── 01-overview-class-diagram.svg        # ← GitHub ready
├── 02-overview-component-diagram.puml   # Component diagram source  
├── 02-overview-component-diagram.svg    # ← GitHub ready
├── 03-overview-deployment-diagram.puml  # Deployment diagram source
├── 03-overview-deployment-diagram.svg   # ← GitHub ready
├── 04-flow-paper-search-sequence.puml   # Sequence diagram source
├── 04-flow-paper-search-sequence.svg    # ← GitHub ready
├── 05-flow-paper-retrieval-activity.puml # Activity diagram source
├── 05-flow-paper-retrieval-activity.svg  # ← GitHub ready
├── 06-pattern-circuit-breaker-state.puml # State diagram source
├── 06-pattern-circuit-breaker-state.svg  # ← GitHub ready
└── README.md                             # This file
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