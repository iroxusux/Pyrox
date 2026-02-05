"""Protocol for objects that support properties.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class IHasProperties(Protocol):
    """Protocol for objects that support properties.
    """

    @property
    def properties(self) -> dict[str, object]:
        """Get the properties of the object.

        Returns:
            dict[str, object]: A dictionary of property names to their values.
        """
        return self.get_properties()

    def get_property(self, name: str) -> object:
        """Get a property by name.

        Args:
            name (str): The name of the property.

        Returns:
            object: The value of the property.
        """
        ...

    def set_property(self, name: str, value: object) -> None:
        """Set a property by name.

        Args:
            name (str): The name of the property.
            value (object): The value to set the property to.
        """
        ...

    def get_properties(self) -> dict[str, object]:
        """Get the properties of the object.

        Returns:
            dict[str, object]: A dictionary of property names to their values.
        """
        ...

    def set_properties(self, properties: dict[str, object]) -> None:
        """Set the properties of the object.

        Args:
            properties (dict[str, object]): A dictionary of property names to their values.
        """
        ...


__all__ = ["IHasProperties"]
