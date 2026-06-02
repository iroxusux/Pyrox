"""Service interface abstractions for Pyrox framework.
"""
from abc import ABC, abstractmethod
from typing import Any


class ISupportsServiceStatus(ABC):
    """Protocol for objects that can report their service status."""

    @abstractmethod
    def is_service_active(self) -> bool:
        """Check if the service is currently active.

        Returns:
            bool: True if the service is active, False otherwise.
        """

    @abstractmethod
    def is_service_initialized(self) -> bool:
        """Check if the service has been initialized.

        Returns:
            bool: True if the service is initialized, False otherwise.
        """


class IHasViewableServiceAttributes(ABC):
    """Protocol for services that have viewable attributes."""

    @abstractmethod
    def get_viewable_attributes(self) -> dict[str, Any]:
        """Get a dictionary of viewable attributes for the service.

        Returns:
            dict[str, Any]: A dictionary of attribute names and their values.
        """


class IStatusServiceMixin(
    ISupportsServiceStatus,
    IHasViewableServiceAttributes,
):
    """A mixin interface that combines service status and viewable attributes protocols."""


__all__ = (
    'ISupportsServiceStatus',
    'IHasViewableServiceAttributes',
    'IStatusServiceMixin',
)
