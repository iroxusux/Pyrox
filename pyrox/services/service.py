"""Service Manager for Pyrox framework.
"""
from pyrox.interfaces import IStatusServiceMixin


class ServiceManager:
    """Centralized manager for core services in the Pyrox framework.

    Services can register with this manager class to allow for centralized access and management.
    This class is designed to be static and should not be instantiated.
    """
    _services: dict[str, type[IStatusServiceMixin] | IStatusServiceMixin] = {}

    def __init__(self):
        raise RuntimeError("ServiceManager is a static class and cannot be instantiated.")

    @classmethod
    def register_service(cls, name: str, service: type[IStatusServiceMixin] | IStatusServiceMixin) -> bool:
        """Register a service with the manager.

        Args:
            name: The unique name of the service.
            service: The service instance to register.

        Returns:
            bool: True if registration was successful, False if a service with the same name already exists.
        """
        if isinstance(service, type):
            if not issubclass(service, IStatusServiceMixin):
                raise ValueError(f"Service class '{service.__name__}' must inherit from IStatusServiceMixin.")
        else:
            if not isinstance(service, IStatusServiceMixin):
                raise ValueError(f"Service instance of type '{type(service).__name__}' must implement IStatusServiceMixin.")

        if name in cls._services:
            return False

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
    def get_service(cls, name: str) -> IStatusServiceMixin | None:
        """Retrieve a registered service by name.

        Args:
            name: The unique name of the service to retrieve.

        Returns:
            object | None: The service instance if found, or None if no service with that name is registered.
        """
        return cls._services.get(name)

    @classmethod
    def get_all_services(cls) -> dict[str, IStatusServiceMixin]:
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
