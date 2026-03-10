from typing import Any
from pyrox.interfaces import Connection


class IConnectionRegistry:
    """Connection registry interface"""

    def register_object(self, obj_id: str, obj: Any):
        """Register an object that can be connected."""
        ...

    def unregister_object(self, obj_id: str):
        """Unregister an object, unwire all its callbacks, and remove its connection records."""
        ...

    def connect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
        enabled: bool = True,
    ) -> Connection:
        """Wire a connection between two registered objects.

        Raises:
            KeyError:   If either object is not registered.
            ValueError: If an identical connection already exists.
        """
        ...

    def disconnect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
    ) -> bool:
        """Remove a single connection and unwire its callback.

        Returns:
            True if the connection was found and removed, False otherwise.
        """
        ...

    def serialize(self) -> dict:
        """Serialize connections for saving."""
        ...
