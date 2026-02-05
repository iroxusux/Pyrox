from dataclasses import dataclass
from typing import Any, Protocol
from pyrox.interfaces.protocols.meta import IHasId


@dataclass
class Connection:
    """Represents a connection between two objects."""
    source_id: str  # Object ID
    source_output: str  # Output name (e.g., "on_activate")
    target_id: str  # Object ID
    target_input: str  # Method/property name
    enabled: bool = True


class IConnectable(
    IHasId,
    Protocol
):
    """Protocol for objects that can be connected in the scene."""

    def get_connections(self) -> list[Connection]:
        """Get the list of connections for this connectable."""
        ...

    def set_connections(self, connections: list[Connection]) -> None:
        """Set the list of connections for this connectable."""
        ...

    def get_outputs(self) -> dict[str, Any]:
        """Get available output connections.

        Returns dict mapping output names to callback lists, properties, or other connection endpoints.
        """
        ...

    def get_inputs(self) -> dict[str, Any]:
        """Get available input connections.

        Returns dict mapping input names to methods, properties, or other connection endpoints.
        """
        ...

    @property
    def connections(self) -> list[Connection]:
        """Get the list of connections.

        Returns:
            list[Connection]: List of connections.
        """
        return self.get_connections()
