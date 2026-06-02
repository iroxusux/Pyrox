"""Service Manager for Pyrox framework.
"""
from typing import Any, Type
from pyrox.interfaces import IHasViewableServiceAttributes, ISupportsServiceStatus, IStatusServiceMixin


class StatusServiceMixin(IStatusServiceMixin):
    """A mixin class that provides default implementations for service status and viewable attributes.

    This class can be used as a base for services that want to support status reporting and have viewable attributes.
    """

    def __init__(self):
        self._active = False
        self._initialized = False
        self._viewable_attributes = {}

    def is_service_active(self) -> bool:
        return self._active

    def is_service_initialized(self) -> bool:
        return self._initialized

    def get_viewable_attributes(self) -> dict[str, Any]:
        return self._viewable_attributes


class ServiceManager:
    """Centralized manager for core services in the Pyrox framework.

    Services can register with this manager class to allow for centralized access and management.
    This class is designed to be static and should not be instantiated.
    """
    _services: dict[str, object] = {}

    def __init__(self):
        raise RuntimeError("ServiceManager is a static class and cannot be instantiated.")

    @classmethod
    def register_service(cls, name: str, service: object) -> bool:
        """Register a service with the manager.

        Args:
            name: The unique name of the service.
            service: The service instance to register.

        Returns:
            bool: True if registration was successful, False if a service with the same name already exists.
        """
        if name in cls._services:
            return False  # Service with this name already exists
        cls._services[name] = service
        return True

    @classmethod
    def unregister_service(cls, name: str) -> bool:
        """Unregister a service from the manager.

        Args:
            name: The unique name of the service to remove.

        Returns:
            bool: True if the service was removed, False if no service with that name was registered.
        """
        if name not in cls._services:
            return False
        del cls._services[name]
        return True

    @classmethod
    def has_service(cls, name: str) -> bool:
        """Check whether a service is registered under the given name.

        Args:
            name: The unique name of the service to check.

        Returns:
            bool: True if a service with that name is registered, False otherwise.
        """
        return name in cls._services

    @classmethod
    def get_service(cls, name: str) -> object | None:
        """Retrieve a registered service by name.

        Args:
            name: The unique name of the service to retrieve.

        Returns:
            object | None: The service instance if found, or None if no service with that name is registered.
        """
        return cls._services.get(name)

    @classmethod
    def get_service_of_type(cls, service_type: Type) -> list[object]:
        """Retrieve all registered services that are instances of the given type.

        Args:
            service_type: The type (class) to filter services by.

        Returns:
            list[object]: A list of service instances matching the given type.
        """
        return [s for s in cls._services.values() if isinstance(s, service_type)]

    @classmethod
    def get_all_services(cls) -> dict[str, object]:
        """Get a shallow copy of all registered services.

        Returns:
            dict[str, object]: A dictionary mapping service names to their instances.
        """
        return dict(cls._services)

    @classmethod
    def list_service_names(cls) -> list[str]:
        """Return a list of all currently registered service names.

        Returns:
            list[str]: The names of all registered services.
        """
        return list(cls._services.keys())

    @classmethod
    def service_count(cls) -> int:
        """Return the number of currently registered services.

        Returns:
            int: The count of registered services.
        """
        return len(cls._services)

    @classmethod
    def clear(cls) -> None:
        """Unregister all services from the manager.

        Intended for use in tests or application teardown.
        """
        cls._services.clear()

    @classmethod
    def get_services_with_status(cls) -> list[dict[str, ISupportsServiceStatus]]:
        """Get a list of registered services that support status reporting.

        Returns:
            list[dict[str, ISupportsServiceStatus]]: A list of dictionaries containing service names and their status objects.
        """
        services_with_status = []
        for name, service in cls._services.items():
            if isinstance(service, ISupportsServiceStatus):
                services_with_status.append({name: service})
        return services_with_status

    @classmethod
    def get_services_with_viewable_attributes(cls) -> list[dict[str, IHasViewableServiceAttributes]]:
        """Get a list of registered services that have viewable attributes.

        Returns:
            list[dict[str, IHasViewableServiceAttributes]]: A list of dictionaries containing service names and their attribute objects.
        """
        services_with_attributes = []
        for name, service in cls._services.items():
            if isinstance(service, IHasViewableServiceAttributes):
                services_with_attributes.append({name: service})
        return services_with_attributes
