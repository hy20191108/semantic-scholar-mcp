"""Protocol definitions for dependency injection and abstraction."""

from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

T = TypeVar("T")
TModel = TypeVar("TModel")
TKey = TypeVar("TKey", contravariant=True)
TValue = TypeVar("TValue")
TValidate = TypeVar("TValidate", contravariant=True)


@runtime_checkable
class IDisposable(Protocol):
    """Protocol for disposable resources."""

    async def dispose(self) -> None:
        """Dispose of resources."""
        ...


@runtime_checkable
class ILogger(Protocol):
    """Protocol for logging services."""

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        ...

    def error(
        self, message: str, exception: Exception | None = None, **kwargs: Any
    ) -> None:
        """Log error message."""
        ...

    def with_context(self, **context: Any) -> "ILogger":
        """Create logger with additional context."""
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """Protocol for metrics collection."""

    def increment(
        self, metric: str, value: int = 1, tags: dict[str, str] | None = None
    ) -> None:
        """Increment a counter metric."""
        ...

    def gauge(
        self, metric: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Set a gauge metric."""
        ...

    def histogram(
        self, metric: str, value: float, tags: dict[str, str] | None = None
    ) -> None:
        """Record a histogram value."""
        ...

    async def flush(self) -> None:
        """Flush pending metrics."""
        ...


@runtime_checkable
class ICache(Protocol, Generic[TKey, TValue]):
    """Protocol for caching services."""

    async def get(self, key: TKey) -> TValue | None:
        """Get value from cache."""
        ...

    async def set(self, key: TKey, value: TValue, ttl: int | None = None) -> None:
        """Set value in cache."""
        ...

    async def delete(self, key: TKey) -> bool:
        """Delete value from cache."""
        ...

    async def exists(self, key: TKey) -> bool:
        """Check if key exists."""
        ...


# Add all required protocols for test compatibility
@runtime_checkable
class IValidator(Protocol):
    """Protocol for validators."""

    def validate(self, value: Any) -> bool:
        """Validate a value."""
        ...


@runtime_checkable
class IMetrics(Protocol):
    """Protocol for metrics."""

    def record(self, metric: str, value: float) -> None:
        """Record a metric."""
        ...


@runtime_checkable
class IErrorHandler(Protocol):
    """Protocol for error handlers."""

    def handle_error(self, error: Exception) -> None:
        """Handle an error."""
        ...

    def recover(self, error: Exception) -> Any:
        """Recover from an error."""
        ...


@runtime_checkable
class IConfigurable(Protocol):
    """Protocol for configurable components."""

    def configure(self, config: dict[str, Any]) -> None:
        """Configure the component."""
        ...


@runtime_checkable
class IObservable(Protocol):
    """Protocol for observable components."""

    def subscribe(self, observer: "IObserver") -> None:
        """Subscribe an observer."""
        ...


@runtime_checkable
class IObserver(Protocol):
    """Protocol for observers."""

    def notify(self, event: Any) -> None:
        """Handle notification."""
        ...


@runtime_checkable
class IEventHandler(Protocol):
    """Protocol for event handlers."""

    def handle_event(self, event: Any) -> None:
        """Handle an event."""
        ...


@runtime_checkable
class IRequestHandler(Protocol):
    """Protocol for request handlers."""

    def handle_request(self, request: Any) -> Any:
        """Handle a request."""
        ...


@runtime_checkable
class IResponseHandler(Protocol):
    """Protocol for response handlers."""

    def handle_response(self, response: Any) -> Any:
        """Handle a response."""
        ...


@runtime_checkable
class IMiddleware(Protocol):
    """Protocol for middleware."""

    def process(self, request: Any, next_handler: Any) -> Any:
        """Process request through middleware."""
        ...


@runtime_checkable
class IAuthenticator(Protocol):
    """Protocol for authenticators."""

    def authenticate(self, credentials: Any) -> bool:
        """Authenticate credentials."""
        ...


@runtime_checkable
class IAuthorizer(Protocol):
    """Protocol for authorizers."""

    def authorize(self, user: Any, resource: Any) -> bool:
        """Authorize access."""
        ...


@runtime_checkable
class IResourceManager(Protocol):
    """Protocol for resource managers."""

    def acquire(self, resource_id: str) -> Any:
        """Acquire a resource."""
        ...


@runtime_checkable
class ISessionManager(Protocol):
    """Protocol for session managers."""

    def create_session(self, user: Any) -> str:
        """Create a session."""
        ...


@runtime_checkable
class ITokenManager(Protocol):
    """Protocol for token managers."""

    def create_token(self, payload: dict[str, Any]) -> str:
        """Create a token."""
        ...


@runtime_checkable
class ISecurityManager(Protocol):
    """Protocol for security managers."""

    def secure(self, data: Any) -> Any:
        """Secure data."""
        ...


@runtime_checkable
class IComplianceManager(Protocol):
    """Protocol for compliance managers."""

    def check_compliance(self, data: Any) -> bool:
        """Check compliance."""
        ...


@runtime_checkable
class IBackupManager(Protocol):
    """Protocol for backup managers."""

    def backup(self, data: Any) -> str:
        """Backup data."""
        ...


@runtime_checkable
class IHealthChecker(Protocol):
    """Protocol for health checkers."""

    def check_health(self) -> bool:
        """Check health."""
        ...


@runtime_checkable
class IMonitor(Protocol):
    """Protocol for monitors."""

    def monitor(self, target: Any) -> None:
        """Monitor target."""
        ...


@runtime_checkable
class IProfiler(Protocol):
    """Protocol for profilers."""

    def profile(self, operation: Any) -> dict[str, Any]:
        """Profile operation."""
        ...


@runtime_checkable
class ISerializer(Protocol):
    """Protocol for serializers."""

    def serialize(self, data: Any) -> bytes:
        """Serialize data."""
        ...


@runtime_checkable
class IDeserializer(Protocol):
    """Protocol for deserializers."""

    def deserialize(self, data: bytes) -> Any:
        """Deserialize data."""
        ...


@runtime_checkable
class IEncoder(Protocol):
    """Protocol for encoders."""

    def encode(self, data: Any) -> str:
        """Encode data."""
        ...


@runtime_checkable
class IDecoder(Protocol):
    """Protocol for decoders."""

    def decode(self, data: str) -> Any:
        """Decode data."""
        ...


@runtime_checkable
class ICompressor(Protocol):
    """Protocol for compressors."""

    def compress(self, data: bytes) -> bytes:
        """Compress data."""
        ...


@runtime_checkable
class IDecompressor(Protocol):
    """Protocol for decompressors."""

    def decompress(self, data: bytes) -> bytes:
        """Decompress data."""
        ...


@runtime_checkable
class IEncryptor(Protocol):
    """Protocol for encryptors."""

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        ...


@runtime_checkable
class IDecryptor(Protocol):
    """Protocol for decryptors."""

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data."""
        ...


@runtime_checkable
class IHasher(Protocol):
    """Protocol for hashers."""

    def hash(self, data: bytes) -> str:
        """Hash data."""
        ...


@runtime_checkable
class ISigner(Protocol):
    """Protocol for signers."""

    def sign(self, data: bytes) -> str:
        """Sign data."""
        ...


@runtime_checkable
class IVerifier(Protocol):
    """Protocol for verifiers."""

    def verify(self, data: bytes, signature: str) -> bool:
        """Verify signature."""
        ...


@runtime_checkable
class ITransformer(Protocol):
    """Protocol for transformers."""

    def transform(self, data: Any) -> Any:
        """Transform data."""
        ...


@runtime_checkable
class IProcessor(Protocol):
    """Protocol for processors."""

    def process(self, data: Any) -> Any:
        """Process data."""
        ...


@runtime_checkable
class IAnalyzer(Protocol):
    """Protocol for analyzers."""

    def analyze(self, data: Any) -> dict[str, Any]:
        """Analyze data."""
        ...


@runtime_checkable
class ICalculator(Protocol):
    """Protocol for calculators."""

    def calculate(self, data: Any) -> float:
        """Calculate value."""
        ...


@runtime_checkable
class IOptimizer(Protocol):
    """Protocol for optimizers."""

    def optimize(self, data: Any) -> Any:
        """Optimize data."""
        ...


@runtime_checkable
class IScheduler(Protocol):
    """Protocol for schedulers."""

    def schedule(self, task: Any) -> None:
        """Schedule task."""
        ...


@runtime_checkable
class IExecutor(Protocol):
    """Protocol for executors."""

    def execute(self, task: Any) -> Any:
        """Execute task."""
        ...


@runtime_checkable
class IDistributor(Protocol):
    """Protocol for distributors."""

    def distribute(self, data: Any) -> None:
        """Distribute data."""
        ...


@runtime_checkable
class IBalancer(Protocol):
    """Protocol for balancers."""

    def balance(self, requests: list[Any]) -> list[Any]:
        """Balance requests."""
        ...


@runtime_checkable
class IRouter(Protocol):
    """Protocol for routers."""

    def route(self, request: Any) -> str:
        """Route request."""
        ...


@runtime_checkable
class INavigator(Protocol):
    """Protocol for navigators."""

    def navigate(self, from_point: Any, to_point: Any) -> list[Any]:
        """Navigate between points."""
        ...


@runtime_checkable
class IPathfinder(Protocol):
    """Protocol for pathfinders."""

    def find_path(self, start: Any, end: Any) -> list[Any]:
        """Find path."""
        ...


@runtime_checkable
class IResolver(Protocol):
    """Protocol for resolvers."""

    def resolve(self, reference: Any) -> Any:
        """Resolve reference."""
        ...


@runtime_checkable
class ILocator(Protocol):
    """Protocol for locators."""

    def locate(self, criteria: Any) -> Any:
        """Locate item."""
        ...


@runtime_checkable
class IDiscoverer(Protocol):
    """Protocol for discoverers."""

    def discover(self, criteria: Any) -> list[Any]:
        """Discover items."""
        ...


@runtime_checkable
class IBuilder(Protocol):
    """Protocol for builders."""

    def build(self, specification: Any) -> Any:
        """Build item."""
        ...


@runtime_checkable
class IFactory(Protocol):
    """Protocol for factories."""

    def create(self, type_name: str, **kwargs: Any) -> Any:
        """Create instance."""
        ...


@runtime_checkable
class ICreator(Protocol):
    """Protocol for creators."""

    def create(self, **kwargs: Any) -> Any:
        """Create instance."""
        ...


@runtime_checkable
class IGenerator(Protocol):
    """Protocol for generators."""

    def generate(self, specification: Any) -> Any:
        """Generate item."""
        ...


@runtime_checkable
class IProducer(Protocol):
    """Protocol for producers."""

    def produce(self, item: Any) -> None:
        """Produce item."""
        ...


@runtime_checkable
class IConsumer(Protocol):
    """Protocol for consumers."""

    def consume(self) -> Any:
        """Consume item."""
        ...


@runtime_checkable
class IPublisher(Protocol):
    """Protocol for publishers."""

    def publish(self, message: Any) -> None:
        """Publish message."""
        ...


@runtime_checkable
class ISubscriber(Protocol):
    """Protocol for subscribers."""

    def subscribe(self, topic: str) -> None:
        """Subscribe to topic."""
        ...


@runtime_checkable
class IBroker(Protocol):
    """Protocol for brokers."""

    def broker(self, message: Any) -> None:
        """Broker message."""
        ...


@runtime_checkable
class IMediator(Protocol):
    """Protocol for mediators."""

    def mediate(self, request: Any) -> Any:
        """Mediate request."""
        ...


@runtime_checkable
class IFacade(Protocol):
    """Protocol for facades."""

    def execute(self, operation: str, **kwargs: Any) -> Any:
        """Execute operation."""
        ...


@runtime_checkable
class IProxy(Protocol):
    """Protocol for proxies."""

    def execute(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Execute method."""
        ...


@runtime_checkable
class IDecorator(Protocol):
    """Protocol for decorators."""

    def decorate(self, target: Any) -> Any:
        """Decorate target."""
        ...


@runtime_checkable
class IAdapter(Protocol):
    """Protocol for adapters."""

    def adapt(self, source: Any) -> Any:
        """Adapt source."""
        ...


@runtime_checkable
class IBridge(Protocol):
    """Protocol for bridges."""

    def bridge(self, source: Any, target: Any) -> None:
        """Bridge source to target."""
        ...


@runtime_checkable
class IComposite(Protocol):
    """Protocol for composites."""

    def add(self, component: Any) -> None:
        """Add component."""
        ...


@runtime_checkable
class IIterator(Protocol):
    """Protocol for iterators."""

    def next(self) -> Any:
        """Get next item."""
        ...


@runtime_checkable
class IVisitor(Protocol):
    """Protocol for visitors."""

    def visit(self, node: Any) -> None:
        """Visit node."""
        ...


@runtime_checkable
class ICommand(Protocol):
    """Protocol for commands."""

    def execute(self) -> None:
        """Execute command."""
        ...


@runtime_checkable
class IStrategy(Protocol):
    """Protocol for strategies."""

    def execute(self, context: Any) -> Any:
        """Execute strategy."""
        ...


@runtime_checkable
class IState(Protocol):
    """Protocol for states."""

    def handle(self, context: Any) -> None:
        """Handle state."""
        ...


@runtime_checkable
class ITemplate(Protocol):
    """Protocol for templates."""

    def render(self, context: Any) -> str:
        """Render template."""
        ...


@runtime_checkable
class IChain(Protocol):
    """Protocol for chain handlers."""

    def handle(self, request: Any) -> Any:
        """Handle request."""
        ...


@runtime_checkable
class IInterpreter(Protocol):
    """Protocol for interpreters."""

    def interpret(self, expression: Any) -> Any:
        """Interpret expression."""
        ...


@runtime_checkable
class IMemento(Protocol):
    """Protocol for mementos."""

    def save_state(self) -> Any:
        """Save state."""
        ...


@runtime_checkable
class IObserverProtocol(Protocol):
    """Protocol for observer pattern."""

    def update(self, subject: Any) -> None:
        """Update observer."""
        ...


@runtime_checkable
class IPrototype(Protocol):
    """Protocol for prototypes."""

    def clone(self) -> Any:
        """Clone prototype."""
        ...


@runtime_checkable
class ISingleton(Protocol):
    """Protocol for singletons."""

    @classmethod
    def get_instance(cls) -> Any:
        """Get singleton instance."""
        ...


@runtime_checkable
class IFlyweight(Protocol):
    """Protocol for flyweights."""

    def operation(self, context: Any) -> None:
        """Execute operation."""
        ...

    async def clear(self) -> None:
        """Clear all cache entries."""
        ...


@runtime_checkable
class IHealthCheckable(Protocol):
    """Protocol for health checkable services."""

    async def check_health(self) -> dict[str, Any]:
        """Check service health."""
        ...


@runtime_checkable
class IConfigurableGeneric(Protocol, Generic[T]):
    """Protocol for configurable services with generic type."""

    def configure(self, config: T) -> None:
        """Configure the service."""
        ...

    def get_config(self) -> T:
        """Get current configuration."""
        ...


@runtime_checkable
class IRetryable(Protocol):
    """Protocol for retryable operations."""

    async def execute_with_retry(
        self, operation: Any, max_attempts: int = 3, backoff_factor: float = 2.0
    ) -> Any:
        """Execute operation with retry logic."""
        ...


@runtime_checkable
class IRateLimiter(Protocol):
    """Protocol for rate limiting."""

    async def acquire(self, key: str, cost: int = 1) -> bool:
        """Acquire rate limit token."""
        ...

    async def wait_if_needed(self, key: str, cost: int = 1) -> None:
        """Wait if rate limit is exceeded."""
        ...

    def get_remaining(self, key: str) -> int:
        """Get remaining tokens."""
        ...


@runtime_checkable
class ICircuitBreaker(Protocol):
    """Protocol for circuit breaker pattern."""

    async def call(self, operation: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute operation through circuit breaker."""
        ...

    def get_state(self) -> str:
        """Get circuit breaker state."""
        ...

    def reset(self) -> None:
        """Reset circuit breaker."""
        ...


@runtime_checkable
class IRepository(Protocol, Generic[T, TKey]):
    """Protocol for repository pattern."""

    async def get_by_id(self, id: TKey) -> T | None:
        """Get entity by ID."""
        ...

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        """Get all entities with pagination."""
        ...

    async def create(self, entity: T) -> T:
        """Create new entity."""
        ...

    async def update(self, entity: T) -> T:
        """Update existing entity."""
        ...

    async def delete(self, id: TKey) -> bool:
        """Delete entity by ID."""
        ...

    async def exists(self, id: TKey) -> bool:
        """Check if entity exists."""
        ...


@runtime_checkable
class IUnitOfWork(Protocol):
    """Protocol for unit of work pattern."""

    async def __aenter__(self) -> "IUnitOfWork":
        """Enter unit of work context."""
        ...

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit unit of work context."""
        ...

    async def commit(self) -> None:
        """Commit changes."""
        ...

    async def rollback(self) -> None:
        """Rollback changes."""
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """Protocol for event publishing."""

    async def publish(self, event_name: str, data: Any) -> None:
        """Publish an event."""
        ...

    def subscribe(self, event_name: str, handler: Any) -> None:
        """Subscribe to an event."""
        ...

    def unsubscribe(self, event_name: str, handler: Any) -> None:
        """Unsubscribe from an event."""
        ...


@runtime_checkable
class IValidatorGeneric(Protocol, Generic[TValidate]):
    """Protocol for validation services with generic type."""

    def validate(self, value: TValidate) -> list[str]:
        """Validate value and return errors."""
        ...

    def is_valid(self, value: TValidate) -> bool:
        """Check if value is valid."""
        ...


@runtime_checkable
class ISerializerGeneric(Protocol, Generic[T]):
    """Protocol for serialization services with generic type."""

    def serialize(self, obj: T) -> str:
        """Serialize object to string."""
        ...

    def deserialize(self, data: str, type_hint: type[T]) -> T:
        """Deserialize string to object."""
        ...
