from typing import Any
from pyrox.interfaces import Connection


class ConnectionRegistry:
    """Manages connections between scene objects."""

    def __init__(self):
        self._connections: list[Connection] = []
        self._objects: dict[str, Any] = {}

    def register_object(self, obj_id: str, obj: Any):
        """Register an object that can be connected."""
        self._objects[obj_id] = obj

    def connect(self, source_id: str, output_name: str,
                target_id: str, input_name: str) -> Connection:
        """Create a connection between objects."""
        conn = Connection(source_id, output_name, target_id, input_name)
        self._connections.append(conn)

        # Wire it up
        source = self._objects[source_id]
        target = self._objects[target_id]

        # Get the callback list (e.g., sensor.on_activate_callbacks)
        callback_list = getattr(source, output_name)
        target_method = getattr(target, input_name)

        callback_list.append(target_method)
        return conn

    def serialize(self) -> dict:
        """Serialize connections for saving."""
        return {
            "connections": [
                {
                    "source": c.source_id,
                    "output": c.source_output,
                    "target": c.target_id,
                    "input": c.target_input,
                    "enabled": c.enabled
                }
                for c in self._connections
            ]
        }
