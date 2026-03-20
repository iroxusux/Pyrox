from typing import Any
from pyrox.interfaces import Connection


class IConnectionRegistry:
    """Connection registry interface"""

    def register_object(self, obj_id: str, obj: Any): ...
    def unregister_object(self, obj_id: str): ...
    def get_object(self, obj_id: str) -> Any: ...
    def get_objects(self) -> dict[str, Any]: ...

    def connect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
        enabled: bool = True,
    ) -> Connection: ...

    def disconnect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
    ) -> bool: ...

    def get_connections(self) -> list[Connection]: ...

    def serialize(self) -> dict: ...

    @property
    def connections(self) -> list[Connection]:
        """Get the list of connections."""
        return self.get_connections()

    @property
    def objects(self) -> dict[str, Any]:
        """Get the registered objects."""
        return self.get_objects()
