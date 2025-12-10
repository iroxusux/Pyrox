"""Integration interface abstractions for Pyrox framework.

These interfaces define the contracts for dependency injection, service registries,
backend management, and plugin systems without implementation dependencies,
enabling flexible and extensible integration patterns.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Type, TypeVar

# Generic type for dependency injection
T = TypeVar('T')


class IServiceRegistry(ABC):
    """Interface for service registry implementations.

    Provides functionality for registering, resolving, and managing services
    in a dependency injection container, enabling loose coupling between components.
    """

    @abstractmethod
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        singleton: bool = True
    ) -> None:
        """Register a service factory function.

        Args:
            service_type: The service interface type.
            factory: Function that creates service instances.
            singleton: True to cache factory result, False to call factory each time.
        """
        pass

    @abstractmethod
    def register_service(
        self,
        service_type: Type[T],
        implementation: T,
        singleton: bool = True
    ) -> None:
        """Register a service implementation.

        Args:
            service_type: The service interface type.
            implementation: The service implementation instance.
            singleton: True to use the same instance, False to create new instances.
        """
        pass

    @abstractmethod
    def get_registered_services(self) -> List[Type]:
        """Get list of all registered service types.

        Returns:
            List[Type]: List of registered service interface types.
        """
        pass

    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """Get a service instance by type.

        Args:
            service_type: The service interface type.

        Returns:
            T: The service instance.

        Raises:
            ServiceNotFoundError: If service is not registered.
        """
        pass

    @abstractmethod
    def has_service(self, service_type: Type[T]) -> bool:
        """Check if a service is registered.

        Args:
            service_type: The service interface type.

        Returns:
            bool: True if service is registered, False otherwise.
        """
        pass

    @abstractmethod
    def unregister_service(self, service_type: Type[T]) -> bool:
        """Unregister a service.

        Args:
            service_type: The service interface type.

        Returns:
            bool: True if service was unregistered, False if not found.
        """
        pass

    @abstractmethod
    def clear_services(self) -> None:
        """Clear all registered services."""
        pass


class IBackendRegistry(ABC):
    """Interface for GUI backend registry implementations.

    Provides functionality for registering, discovering, and managing
    different GUI backend implementations, solving circular dependencies.
    """

    @abstractmethod
    def create_backend(self, backend_name: str, **kwargs) -> Any:
        """Create a backend instance.

        Args:
            framework_name: Name of the GUI framework.
            **kwargs: Backend creation parameters.

        Returns:
            Any: The created backend instance.
        """
        pass

    @abstractmethod
    def get_available_backends(self) -> List[str]:
        """Get list of available and working frameworks on this system.

        Returns:
            List[str]: List of framework names that are available.
        """
        pass

    @abstractmethod
    def get_backend(self, backend_name: str) -> Type[Any]:
        """Get a backend class by framework name.

        Args:
            framework_name: Name of the GUI framework.

        Returns:
            Type[Any]: The backend class.

        Raises:
            BackendNotFoundError: If backend is not registered.
        """
        pass

    @abstractmethod
    def has_backend(self, backend_name: str) -> bool:
        """Check if a backend is registered.

        Args:
            framework_name: Name of the GUI framework.

        Returns:
            bool: True if backend is registered, False otherwise.
        """
        pass

    @abstractmethod
    def register_backend(self, backend_name: str, backend_class: Type[Any]) -> None:
        """Register a GUI backend implementation.

        Args:
            backend_name: Name of the GUI backend (e.g., 'tkinter', 'qt').
            backend_class: The backend class to register.
        """
        pass

    @abstractmethod
    def unregister_backend(self, backend_name: str) -> bool:
        """Unregister a backend.

        Args:
            framework_name: Name of the GUI framework.

        Returns:
            bool: True if backend was unregistered, False if not found.
        """
        pass


class IDependencyInjector(ABC):
    """Interface for dependency injection implementations.

    Provides functionality for automatic dependency resolution and injection,
    enabling clean separation of concerns and testable code.
    """

    @abstractmethod
    def inject_dependencies(self, target: Any) -> None:
        """Inject dependencies into a target object.

        Args:
            target: Object to inject dependencies into.
        """
        pass

    @abstractmethod
    def create_with_dependencies(self, target_type: Type[T], **kwargs) -> T:
        """Create an instance with automatic dependency injection.

        Args:
            target_type: Type to create.
            **kwargs: Additional constructor parameters.

        Returns:
            T: Created instance with injected dependencies.
        """
        pass

    @abstractmethod
    def register_dependency_provider(
        self,
        dependency_type: Type[T],
        provider: Callable[[], T]
    ) -> None:
        """Register a dependency provider.

        Args:
            dependency_type: Type of dependency to provide.
            provider: Function that provides the dependency.
        """
        pass

    @abstractmethod
    def resolve_dependency(self, dependency_type: Type[T]) -> T:
        """Resolve a dependency by type.

        Args:
            dependency_type: Type of dependency to resolve.

        Returns:
            T: Resolved dependency instance.
        """
        pass

    @abstractmethod
    def has_dependency_provider(self, dependency_type: Type[T]) -> bool:
        """Check if a dependency provider is registered.

        Args:
            dependency_type: Type of dependency to check.

        Returns:
            bool: True if provider is registered, False otherwise.
        """
        pass


class IPluginManager(ABC):
    """Interface for plugin management systems.

    Provides functionality for loading, managing, and executing plugins,
    enabling extensible application architectures.
    """

    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from a file path.

        Args:
            plugin_path: Path to the plugin file.

        Returns:
            bool: True if plugin was loaded successfully.
        """
        pass

    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name.

        Args:
            plugin_name: Name of the plugin to unload.

        Returns:
            bool: True if plugin was unloaded successfully.
        """
        pass

    @abstractmethod
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names.

        Returns:
            List[str]: List of loaded plugin names.
        """
        pass

    @abstractmethod
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin to check.

        Returns:
            bool: True if plugin is loaded, False otherwise.
        """
        pass

    @abstractmethod
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get information about a plugin.

        Args:
            plugin_name: Name of the plugin.

        Returns:
            Dict[str, Any]: Plugin information dictionary.
        """
        pass

    @abstractmethod
    def discover_plugins(self, search_paths: List[str]) -> List[str]:
        """Discover plugins in the specified search paths.

        Args:
            search_paths: List of paths to search for plugins.

        Returns:
            List[str]: List of discovered plugin paths.
        """
        pass

    @abstractmethod
    def register_plugin_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a plugin hook callback.

        Args:
            hook_name: Name of the hook.
            callback: Function to call when hook is triggered.
        """
        pass

    @abstractmethod
    def trigger_plugin_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Trigger a plugin hook and collect results.

        Args:
            hook_name: Name of the hook to trigger.
            *args: Arguments to pass to hook callbacks.
            **kwargs: Keyword arguments to pass to hook callbacks.

        Returns:
            List[Any]: List of results from hook callbacks.
        """
        pass


__all__ = (
    'IServiceRegistry',
    'IBackendRegistry',
    'IDependencyInjector',
    'IPluginManager',
)
