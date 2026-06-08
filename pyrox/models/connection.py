from pyrox.interfaces import Connection, IConnectionRegistry, IConnectable
from pyrox.models.base import HasId


class Connectable(
    IConnectable,
    HasId,
):
    """Base implementation of IConnectable protocol."""

    def get_inputs(self) -> dict[str, object]:
        """Get available input connections.

        Returns dict mapping input names to methods, properties, or other connection endpoints.
        """
        return {}

    def get_outputs(self) -> dict[str, object]:
        """Get available output connections.

        Returns dict mapping output names to callback lists, properties, or other connection endpoints.
        """
        return {}


class ConnectionRegistry(IConnectionRegistry):
    """Manages connections between scene objects.

    Each connection wires a *source* object's callback list (e.g.
    ``on_activate``) to a *target* object's input method (e.g.
    ``set_active``).
    """

    def __init__(self):
        self._connections: list[Connection] = []
        self._objects: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _filter_by_obj_id(self, obj_id: str) -> list[Connection]:
        """Get all connections where the given object ID is either source or target."""
        return [
            c for c in self._connections
            if c.source_id == obj_id or c.target_id == obj_id
        ]

    def _unwire(self, conn: Connection) -> None:
        """Remove the stored callback reference from the source's list."""
        source = self._objects.get(conn.source_id)
        if source is None:
            return
        callback_list = getattr(source, conn.source_output, None)
        target_method = getattr(self._objects.get(conn.target_id), conn.target_input, None)
        if not callable(target_method):
            return
        if isinstance(callback_list, list) and target_method in callback_list:
            callback_list.remove(target_method)

    # ------------------------------------------------------------------
    # Object registration
    # ------------------------------------------------------------------

    def register_object(self, obj_id: str, obj: object) -> None:
        """Register an object that can participate in connections."""
        if obj_id in self._objects:
            self.unregister_object(obj_id)
        self._objects[obj_id] = obj

    def unregister_object(self, obj_id: str) -> None:
        """Unregister an object, unwire all its callbacks, and remove all
        connection records that reference it.
        """
        to_unwire = self._filter_by_obj_id(obj_id)
        for conn in to_unwire:
            self._unwire(conn)
        self._connections = [c for c in self._connections if c not in to_unwire]
        self._objects.pop(obj_id, None)

    def get_object(self, obj_id: str) -> object:
        """Get a registered object by ID."""
        return self._objects.get(obj_id)

    def get_objects(self) -> dict[str, object]:
        """Get all registered objects."""
        return self._objects

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
        enabled: bool = True,
    ) -> Connection:
        """Wire a connection between two registered objects.

        Args:
            source_id:   ID of the source object (must already be registered).
            output_name: Attribute on the source that holds the callback list.
            target_id:   ID of the target object (must already be registered).
            input_name:  Attribute / method on the target to call on event.
            enabled:     When ``False`` the connection is recorded but the
                         callback is *not* wired.  Useful for restoring
                         persisted-but-disabled connections.

        Returns:
            The new :class:`~pyrox.interfaces.Connection` record.

        Raises:
            KeyError:   If *source_id* or *target_id* is not registered.
            ValueError: If an identical connection already exists.
        """
        if source_id not in self._objects:
            raise KeyError(
                f"Source object '{source_id}' is not registered in the "
                f"connection registry. Call register_object first."
            )
        if target_id not in self._objects:
            raise KeyError(
                f"Target object '{target_id}' is not registered in the "
                f"connection registry. Call register_object first."
            )

        duplicate = any(
            c.source_id == source_id
            and c.source_output == output_name
            and c.target_id == target_id
            and c.target_input == input_name
            for c in self._connections
        )
        if duplicate:
            raise ValueError(
                f"Connection from '{source_id}.{output_name}' to "
                f"'{target_id}.{input_name}' already exists."
            )

        conn = Connection(source_id, output_name, target_id, input_name, enabled=enabled)

        if enabled:
            source = self._objects[source_id]
            target = self._objects[target_id]
            # Resolve attributes before mutating state (keep connect() atomic)
            callback_list = getattr(source, output_name)
            target_method = getattr(target, input_name)
            callback_list.append(target_method)

        # Record is appended only after wiring succeeds — keeps connect() atomic.
        self._connections.append(conn)
        return conn

    def disconnect(
        self,
        source_id: str,
        output_name: str,
        target_id: str,
        input_name: str,
    ) -> bool:
        """Remove a single connection and unwire its callback.

        Returns:
            ``True`` if the connection was found and removed; ``False`` if no
            matching connection existed.
        """
        key = (source_id, output_name, target_id, input_name)
        matching = [
            c for c in self._connections
            if (c.source_id, c.source_output, c.target_id, c.target_input) == key
        ]
        if not matching:
            return False

        for conn in matching:
            self._unwire(conn)

        self._connections = [
            c for c in self._connections
            if (c.source_id, c.source_output, c.target_id, c.target_input) != key
        ]
        return True

    def get_connections(self) -> list[Connection]:
        """Get all registered connections."""
        return self._connections

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> dict:
        """Serialize all connection records for saving."""
        return {
            "connections": [
                {
                    "source": c.source_id,
                    "output": c.source_output,
                    "target": c.target_id,
                    "input": c.target_input,
                    "enabled": c.enabled,
                }
                for c in self._connections
            ]
        }
