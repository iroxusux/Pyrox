from typing import Any
from pyrox.interfaces import IConnectable, Connection
from pyrox.models.protocols.meta import HasId


class Connectable(
    IConnectable,
    HasId,
):
    """Base implementation of IConnectable protocol."""

    def __init__(
        self,
        id: str,
    ) -> None:
        HasId.__init__(self, id=id)
        self._connections: list[Connection] = []

    def get_connections(self) -> list[Connection]:
        """Get the list of connections for this connectable."""
        return self._connections

    def set_connections(self, connections: list[Connection]) -> None:
        """Set the list of connections for this connectable."""
        self._connections = connections

    def get_inputs(self) -> dict[str, Any]:
        """Get available input connections.

        Returns dict mapping input names to methods, properties, or other connection endpoints.
        """
        raise NotImplementedError()

    def get_outputs(self) -> dict[str, Any]:
        """Get available output connections.

        Returns dict mapping output names to callback lists, properties, or other connection endpoints.
        """
        raise NotImplementedError()
