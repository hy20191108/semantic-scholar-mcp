"""Dependency injection container implementation."""

import inspect
from collections.abc import Callable
from contextvars import ContextVar
from enum import Enum
from functools import wraps
from threading import Lock
from typing import Any, Optional, Protocol, TypeVar, get_origin, get_type_hints

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime enumeration."""

    TRANSIENT = "transient"  # New instance each time
    SCOPED = "scoped"      # New instance per scope
    SINGLETON = "singleton" # Single instance for app lifetime


class ServiceDescriptor:
    """Describes a service registration."""

    def __init__(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | T,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        factory: Callable[..., T] | None = None
    ):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory
        self.instance: T | None = None

        # If implementation is already an instance, it's a singleton
        if not inspect.isclass(implementation) and not callable(implementation):
            self.lifetime = ServiceLifetime.SINGLETON
            self.instance = implementation


class IServiceProvider(Protocol):
    """Service provider protocol."""

    def get_service(self, service_type: type[T]) -> T | None:
        """Get service instance."""
        ...

    def get_required_service(self, service_type: type[T]) -> T:
        """Get required service instance."""
        ...

    def get_services(self, service_type: type[T]) -> list[T]:
        """Get all services of type."""
        ...


class IServiceScope(Protocol):
    """Service scope protocol."""

    @property
    def service_provider(self) -> IServiceProvider:
        """Get scoped service provider."""
        ...

    def dispose(self) -> None:
        """Dispose scope and its services."""
        ...


class ServiceScope:
    """Implementation of service scope."""

    def __init__(self, provider: "ServiceProvider", parent: Optional["ServiceProvider"] = None):
        self._provider = provider
        self._parent = parent
        self._instances: dict[type, Any] = {}
        self._disposed = False

    @property
    def service_provider(self) -> "ServiceProvider":
        """Get scoped service provider."""
        return self._provider

    def get_or_create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Get or create scoped instance."""
        if self._disposed:
            raise RuntimeError("Cannot access disposed scope")

        service_type = descriptor.service_type

        if service_type in self._instances:
            return self._instances[service_type]

        if descriptor.lifetime == ServiceLifetime.SINGLETON and self._parent:
            return self._parent.get_service(service_type)

        instance = self._provider.create_instance(descriptor)

        if descriptor.lifetime == ServiceLifetime.SCOPED:
            self._instances[service_type] = instance

        return instance

    def dispose(self) -> None:
        """Dispose scope and its services."""
        if self._disposed:
            return

        for instance in self._instances.values():
            if hasattr(instance, "dispose"):
                instance.dispose()
            elif hasattr(instance, "__exit__"):
                instance.__exit__(None, None, None)

        self._instances.clear()
        self._disposed = True

    def __enter__(self) -> "ServiceScope":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.dispose()


class ServiceProvider:
    """Dependency injection service provider."""

    def __init__(self, services: "ServiceCollection"):
        self._descriptors = services.build()
        self._singletons: dict[type, Any] = {}
        self._lock = Lock()
        self._current_scope: ContextVar[ServiceScope | None] = ContextVar(
            "current_scope", default=None
        )

    def get_service(self, service_type: type[T]) -> T | None:
        """Get service instance."""
        try:
            return self.get_required_service(service_type)
        except KeyError:
            return None

    def get_required_service(self, service_type: type[T]) -> T:
        """Get required service instance."""
        if service_type not in self._descriptors:
            # Check if it's a generic type
            origin = get_origin(service_type)
            if origin:
                # Try to find a registration for the origin type
                for registered_type in self._descriptors:
                    if get_origin(registered_type) == origin:
                        return self._resolve_service(self._descriptors[registered_type])

            raise KeyError(f"Service of type {service_type} is not registered")

        return self._resolve_service(self._descriptors[service_type])

    def get_services(self, service_type: type[T]) -> list[T]:
        """Get all services of type."""
        services = []
        for desc_type, descriptor in self._descriptors.items():
            if issubclass(desc_type, service_type):
                services.append(self._resolve_service(descriptor))
        return services

    def create_scope(self) -> ServiceScope:
        """Create new service scope."""
        scope = ServiceScope(self, self)
        return scope

    def _resolve_service(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve service instance."""
        # Check current scope
        scope = self._current_scope.get()
        if scope and descriptor.lifetime == ServiceLifetime.SCOPED:
            return scope.get_or_create_instance(descriptor)

        # Handle singleton
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.instance is not None:
                return descriptor.instance

            with self._lock:
                if descriptor.service_type in self._singletons:
                    return self._singletons[descriptor.service_type]

                instance = self.create_instance(descriptor)
                self._singletons[descriptor.service_type] = instance
                return instance

        # Handle transient
        return self.create_instance(descriptor)

    def create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create new instance of service."""
        if descriptor.instance is not None:
            return descriptor.instance

        if descriptor.factory:
            return descriptor.factory(self)

        implementation = descriptor.implementation

        if not inspect.isclass(implementation):
            return implementation

        # Get constructor parameters
        init_signature = inspect.signature(implementation.__init__)
        kwargs = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == "self":
                continue

            # Get type hint
            param_type = param.annotation
            if param_type == inspect.Parameter.empty:
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                continue

            # Resolve dependency
            try:
                kwargs[param_name] = self.get_required_service(param_type)
            except KeyError:
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
                else:
                    raise

        return implementation(**kwargs)


class ServiceCollection:
    """Service collection for registering services."""

    def __init__(self):
        self._services: list[ServiceDescriptor] = []

    def add_transient(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | None = None
    ) -> "ServiceCollection":
        """Add transient service."""
        impl = implementation or service_type
        self._services.append(
            ServiceDescriptor(service_type, impl, ServiceLifetime.TRANSIENT)
        )
        return self

    def add_scoped(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | None = None
    ) -> "ServiceCollection":
        """Add scoped service."""
        impl = implementation or service_type
        self._services.append(
            ServiceDescriptor(service_type, impl, ServiceLifetime.SCOPED)
        )
        return self

    def add_singleton(
        self,
        service_type: type[T],
        implementation: type[T] | Callable[..., T] | T | None = None
    ) -> "ServiceCollection":
        """Add singleton service."""
        impl = implementation or service_type
        self._services.append(
            ServiceDescriptor(service_type, impl, ServiceLifetime.SINGLETON)
        )
        return self

    def add_singleton_instance(self, service_type: type[T], instance: T) -> "ServiceCollection":
        """Add singleton instance."""
        self._services.append(
            ServiceDescriptor(service_type, instance, ServiceLifetime.SINGLETON)
        )
        return self

    def add_factory(
        self,
        service_type: type[T],
        factory: Callable[[ServiceProvider], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    ) -> "ServiceCollection":
        """Add service with factory."""
        descriptor = ServiceDescriptor(service_type, factory, lifetime)
        descriptor.factory = factory
        self._services.append(descriptor)
        return self

    def build(self) -> dict[type, ServiceDescriptor]:
        """Build service descriptors dictionary."""
        descriptors = {}
        for service in self._services:
            descriptors[service.service_type] = service
        return descriptors


# Decorator for dependency injection
def inject(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for automatic dependency injection."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        # Get service provider from first argument if it's a class method
        provider = None
        if args and hasattr(args[0], "_service_provider"):
            provider = args[0]._service_provider

        if not provider:
            return func(*args, **kwargs)

        # Get type hints
        hints = get_type_hints(func)

        # Inject dependencies
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name in kwargs or param_name == "self":
                continue

            if param_name in hints:
                param_type = hints[param_name]
                service = provider.get_service(param_type)
                if service is not None:
                    kwargs[param_name] = service

        return func(*args, **kwargs)

    return wrapper


# Service locator pattern (for legacy code)
class ServiceLocator:
    """Static service locator."""

    _provider: ServiceProvider | None = None

    @classmethod
    def set_provider(cls, provider: ServiceProvider) -> None:
        """Set service provider."""
        cls._provider = provider

    @classmethod
    def get_service(cls, service_type: type[T]) -> T | None:
        """Get service instance."""
        if not cls._provider:
            raise RuntimeError("Service provider not set")
        return cls._provider.get_service(service_type)

    @classmethod
    def get_required_service(cls, service_type: type[T]) -> T:
        """Get required service instance."""
        if not cls._provider:
            raise RuntimeError("Service provider not set")
        return cls._provider.get_required_service(service_type)
