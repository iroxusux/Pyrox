from typing import Any
from pyrox.interfaces import Connection


class IConnectionRegistry:
    """Connection registry interface
    """

    def register_object(self, obj_id: str, obj: Any):
        """Register an object that can be connected."""
        ...

    def unregister_object(self, obj_id: str):
        """Unregister an object and remove its connections."""
        ...

    def connect(self, source_id: str, output_name: str,
                target_id: str, input_name: str) -> Connection:
        """Create a connection between objects."""
        ...

    def serialize(self) -> dict:
        """Serialize connections for saving."""
        ...
