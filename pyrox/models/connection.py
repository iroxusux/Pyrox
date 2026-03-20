from __future__ import annotations

from typing import Any

from pyrox.interfaces import Connection, IConnectionRegistry


class ConnectionRegistry(IConnectionRegistry):
    """Manages connections between scene objects.

    Each connection wires a *source* object's callback list (e.g.
    ``on_activate``) to a *target* object's input method (e.g.
    ``set_active``).  The registry tracks both the logical `Connection` record
    and the actual bound-method reference so that callbacks can be cleanly
    removed when objects are unregistered or connections are removed.
    """

    def __init__(self):
        self._connections: list[Connection] = []
        self._objects: dict[str, Any] = {}
        # Maps (source_id, output, target_id, input) → the callback ref stored
        # in the source's callback list, enabling clean removal.
        self._callback_refs: dict[tuple[str, str, str, str], Any] = {}

    # ------------------------------------------------------------------
    # Object registration
    # ------------------------------------------------------------------

    def register_object(self, obj_id: str, obj: Any) -> None:
        """Register an object that can participate in connections."""
        self._objects[obj_id] = obj

    def unregister_object(self, obj_id: str) -> None:
        """Unregister an object, unwire all its callbacks, and remove all
        connection records that reference it.

        Bug fix: previously the connection records were dropped but the
        callback references remained in the source's callback list, causing
        dangling calls after the target was gone.
        """
        # Collect and unwire every connection touching this object *before*
        # deleting it, so we can still resolve `self._objects[target_id]`
        # when unwiring connections where this object is the source.
        to_remove = [
            c for c in self._connections
            if c.source_id == obj_id or c.target_id == obj_id
        ]
        for conn in to_remove:
            self._unwire(conn)

        self._connections = [
            c for c in self._connections
            if c.source_id != obj_id and c.target_id != obj_id
        ]

        self._objects.pop(obj_id, None)

    def get_object(self, obj_id: str) -> Any:
        """Get a registered object by ID."""
        return self._objects.get(obj_id)

    def get_objects(self) -> dict[str, Any]:
        """Get all registered objects."""
        return self._objects

    # ------------------------------------------------------------------
    # Internal wiring helpers
    # ------------------------------------------------------------------

    def _unwire(self, conn: Connection) -> None:
        """Remove the stored callback reference from the source's list."""
        key = (conn.source_id, conn.source_output, conn.target_id, conn.target_input)
        callback_ref = self._callback_refs.pop(key, None)
        if callback_ref is None:
            return
        source = self._objects.get(conn.source_id)
        if source is None:
            return
        callback_list = getattr(source, conn.source_output, None)
        if isinstance(callback_list, list) and callback_ref in callback_list:
            callback_list.remove(callback_ref)

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

        key = (source_id, output_name, target_id, input_name)
        if key in self._callback_refs:
            raise ValueError(
                f"Connection {source_id}.{output_name} → "
                f"{target_id}.{input_name} already exists. "
                f"Call disconnect first to replace it."
            )

        conn = Connection(source_id, output_name, target_id, input_name, enabled=enabled)

        if enabled:
            source = self._objects[source_id]
            target = self._objects[target_id]
            # Resolve attributes before mutating state (keep connect() atomic)
            callback_list = getattr(source, output_name)
            target_method = getattr(target, input_name)
            callback_list.append(target_method)
            self._callback_refs[key] = target_method

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
