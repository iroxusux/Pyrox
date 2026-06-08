from abc import ABC, abstractmethod
from dataclasses import dataclass
from pyrox.interfaces.base import IHasId


@dataclass
class Connection:
    """Represents a connection between two objects."""
    source_id: str  # Object ID
    source_output: str  # Output name (e.g., "on_activate")
    target_id: str  # Object ID
    target_input: str  # Method/property name
    enabled: bool = True


class IConnectable(IHasId):
    """Protocol for objects that can be connected.
    """

    @abstractmethod
    def get_outputs(self) -> dict[str, object]: ...
    @abstractmethod
    def get_inputs(self) -> dict[str, object]: ...


class IConnectionRegistry(ABC):
    """Connection registry interface"""

    @abstractmethod
    def register_object(self, obj_id: str, obj: object): ...
    @abstractmethod
    def unregister_object(self, obj_id: str): ...
    @abstractmethod
    def get_object(self, obj_id: str) -> object: ...
    @abstractmethod
    def get_objects(self) -> dict[str, object]: ...

    @abstractmethod
    def connect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
        enabled: bool = True,
    ) -> Connection: ...

    @abstractmethod
    def disconnect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
    ) -> bool: ...

    @abstractmethod
    def get_connections(self) -> list[Connection]: ...

    @abstractmethod
    def serialize(self) -> dict: ...

    @property
    def connections(self) -> list[Connection]:
        """Get the list of connections."""
        return self.get_connections()

    @property
    def objects(self) -> dict[str, object]:
        """Get the registered objects."""
        return self.get_objects()
