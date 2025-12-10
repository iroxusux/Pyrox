from typing import Any, Callable, Dict, List, Type, TypeVar
from pyrox.interfaces import IBackendRegistry, IGuiBackend, IServiceRegistry

T = TypeVar('T')


class BackendNotFoundError(Exception):
    """Raised when a requested backend is not registered."""
    pass


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""
    pass


class ServiceRegistry(IServiceRegistry):

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, bool] = {}

    def clear_services(self) -> None:
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        singleton: bool = True
    ) -> None:
        self._factories[service_type] = factory
        self._singletons[service_type] = singleton

    def register_service(
        self,
        service_type: Type[T],
        implementation: T,
        singleton: bool = True
    ) -> None:
        self._services[service_type] = implementation
        self._singletons[service_type] = singleton

    def get_registered_services(self) -> List[Type]:
        return list(set(self._services.keys()).union(set(self._factories.keys())))

    def get_service(self, service_type: Type[T]) -> T:
        if service_type in self._services:
            return self._services[service_type]
        elif service_type in self._factories:
            factory = self._factories[service_type]
            instance = factory()
            if self._singletons.get(service_type, True):
                self._services[service_type] = instance
            return instance
        else:
            raise ServiceNotFoundError(f"Service {service_type} not registered")

    def has_service(self, service_type: Type) -> bool:
        return service_type in self._services or service_type in self._factories

    def unregister_service(self, service_type: type[T]) -> bool:
        removed = False
        if service_type in self._services:
            del self._services[service_type]
            removed = True
        if service_type in self._factories:
            del self._factories[service_type]
            del self._singletons[service_type]
            removed = True
        return removed


class BackendRegistry(IBackendRegistry):
    def __init__(self):
        self._backends: Dict[str, Type[IGuiBackend]] = {}

    def create_backend(self, backend_name: str, **kwargs) -> IGuiBackend:
        if backend_name not in self._backends:
            raise BackendNotFoundError(f"Backend {backend_name} not registered")

        backend_class = self._backends[backend_name]
        return backend_class(**kwargs)

    def get_available_backends(self) -> List[str]:
        available = []
        for name, backend_class in self._backends.items():
            backend = backend_class()
            if backend.is_available():
                available.append(name)
        return available

    def get_backend(self, backend_name: str) -> Type[Any]:
        if backend_name not in self._backends:
            raise BackendNotFoundError(f"Backend {backend_name} not registered")
        return self._backends[backend_name]

    def has_backend(self, backend_name: str) -> bool:
        return backend_name in self._backends

    def register_backend(
        self,
        backend_name: str,
        backend_class: Type[IGuiBackend]
    ) -> None:
        self._backends[backend_name] = backend_class

    def unregister_backend(self, backend_name: str) -> bool:
        if backend_name in self._backends:
            del self._backends[backend_name]
            return True
        return False
