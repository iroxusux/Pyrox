"""Interfaces for generic scene bridge and binding contracts."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional, Protocol, runtime_checkable

from pyrox.interfaces.scene.scene import IScene


class BindingDirection(Enum):
    """Direction of data flow for scene bindings."""

    READ = "read"       # Source -> Scene
    WRITE = "write"     # Scene -> Source
    BOTH = "both"       # Bidirectional synchronization


@runtime_checkable
class ISceneBinding(Protocol):
    """Structural contract for a single scene binding record.

    Any object satisfying these attributes is a valid ISceneBinding — no
    inheritance from this class is required.
    """

    binding_key: str
    """Unique key that identifies the source value (e.g. a topic, channel name, or path)."""

    object_id: str
    """ID of the target scene object."""

    property_path: str
    """Dot-separated path to the property on the scene object (e.g. 'pose.x')."""

    direction: BindingDirection
    """Which direction data flows between source and scene."""

    enabled: bool
    """Whether this binding participates in sync cycles."""

    last_source_value: Any
    """Last value read from the source."""

    last_scene_value: Any
    """Last value written to the scene."""

    description: str
    """Optional human-readable label for the binding."""

    tags: list[str]
    """Arbitrary string tags for grouping or filtering bindings."""

    metadata: dict[str, Any]
    """Open-ended extra data (units, scaling hints, UI labels, etc.)."""


class ISceneBridge(ABC):
    """Abstract contract for a scene bridge engine.

    A bridge synchronizes data between an external source object and scene object
    properties. Implementations integrate domain-specific transports (sockets,
    queues, file watchers, simulation buses, etc.) by overriding the protected hook methods while
    inheriting the full binding management and sync lifecycle from the base class.

    Typical usage::

        bridge = MyBridge(scene=my_scene)

        bridge.add_binding(
            binding_key="inputs.speed",
            object_id="conveyor_1",
            property_path="speed",
            direction=BindingDirection.READ,
        )
        bridge.start()                         # activates source subscriptions
        bridge.handle_source_update(           # push source value into scene
            "inputs.speed", value=5.0
        )
        bridge.update_scene_to_source()        # flush WRITE bindings back to source
        bridge.stop()
    """

    # ------------------------------------------------------------------
    # Bound-object access
    # ------------------------------------------------------------------

    @abstractmethod
    def create_default_bound_object(self) -> Any:
        """Return the default source object when none is provided.

        Override in subclasses to provide a domain-specific default
        (e.g. a plain dict, a socket client, a live data session object).
        """
        ...

    @abstractmethod
    def get_bound_object(self) -> Any:
        """Return the current source object."""
        ...

    @abstractmethod
    def set_bound_object(self, bound_object: Optional[Any]) -> None:
        """Replace the current source object.

        Passing ``None`` resets it to the value returned by
        :meth:`create_default_bound_object`.
        """
        ...

    # ------------------------------------------------------------------
    # Scene access
    # ------------------------------------------------------------------

    @abstractmethod
    def get_scene(self) -> Optional[IScene]:
        """Return the scene this bridge is bound to."""
        ...

    @abstractmethod
    def set_scene(self, scene: Optional[IScene]) -> None:
        """Attach a new scene, stopping the bridge first if it is active."""
        ...

    # ------------------------------------------------------------------
    # Binding management
    # ------------------------------------------------------------------

    @abstractmethod
    def add_binding(
        self,
        binding_key: str,
        object_id: str,
        property_path: str,
        direction: BindingDirection = BindingDirection.READ,
        transform: Optional[Callable[[Any], Any]] = None,
        inverse_transform: Optional[Callable[[Any], Any]] = None,
        description: str = "",
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ISceneBinding:
        """Create and register a new binding.

        Args:
            binding_key:        Identifies the source value.
            object_id:          Target scene object ID.
            property_path:      Dot-separated attribute path on the scene object.
            direction:          Data-flow direction.
            transform:          Optional callable applied to incoming source values
                                before they are written to the scene.
            inverse_transform:  Optional callable applied to scene values before
                                they are written back to the source.
            description:        Human-readable label.
            tags:               Arbitrary grouping tags.
            metadata:           Extra key/value pairs (units, UI hints, etc.).

        Returns:
            The newly created :class:`ISceneBinding` instance.
        """
        ...

    @abstractmethod
    def remove_binding(
        self,
        binding_key: str,
        object_id: str,
        property_path: str,
    ) -> bool:
        """Remove a specific binding.

        Returns:
            ``True`` if a matching binding was found and removed, ``False`` otherwise.
        """
        ...

    @abstractmethod
    def clear_bindings(self) -> None:
        """Remove all bindings, stopping the bridge first if it is active."""
        ...

    @abstractmethod
    def get_bindings(self) -> list[ISceneBinding]:
        """Return all registered bindings."""
        ...

    @abstractmethod
    def get_bindings_for_object(self, object_id: str) -> list[ISceneBinding]:
        """Return all bindings targeting a specific scene object."""
        ...

    @abstractmethod
    def get_bindings_for_key(self, binding_key: str) -> list[ISceneBinding]:
        """Return all bindings for a given source key."""
        ...

    # ------------------------------------------------------------------
    # State & configuration
    # ------------------------------------------------------------------

    @abstractmethod
    def is_active(self) -> bool:
        """Return ``True`` while the bridge is running."""
        ...

    @abstractmethod
    def is_write_enabled(self) -> bool:
        """Return ``True`` if scene→source writes are enabled."""
        ...

    @abstractmethod
    def set_write_enabled(self, enabled: bool) -> None:
        """Enable or disable scene→source writes."""
        ...

    @abstractmethod
    def get_write_throttle(self) -> float:
        """Return the minimum milliseconds between writes for the same key."""
        ...

    @abstractmethod
    def set_write_throttle(self, throttle_ms: float) -> None:
        """Set the minimum milliseconds between writes for the same key."""
        ...

    @abstractmethod
    def get_binding_stats(self) -> dict[str, Any]:
        """Return a summary of binding counts by direction and enabled state."""
        ...

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def start(self) -> None:
        """Activate the bridge — subscribe to source, register tick callback.

        Has no effect (and logs a warning) if the bridge is already active.
        Logs an error and aborts if no scene has been set.
        """
        ...

    @abstractmethod
    def stop(self) -> None:
        """Deactivate the bridge — unsubscribe from source, unregister tick.

        Safe to call when the bridge is not active.
        """
        ...

    # ------------------------------------------------------------------
    # Sync operations
    # ------------------------------------------------------------------

    @abstractmethod
    def update_scene_to_source(self) -> None:
        """Flush current scene values for all WRITE/BOTH bindings back to source.

        Respects the write-throttle setting and skips unchanged values.
        Called automatically on each tick when the bridge is active, but can
        also be triggered manually for immediate flushes.
        """
        ...

    @abstractmethod
    def force_write_binding(
        self,
        binding_key: str,
        object_id: str,
        property_path: str,
    ) -> bool:
        """Write a single binding's current scene value to source immediately,
        bypassing write-throttle.

        Returns:
            ``True`` on success, ``False`` if the binding was not found,
            is disabled, is not writable, or the scene value could not be read.
        """
        ...

    @abstractmethod
    def handle_source_update(
        self,
        binding_key: str,
        value: Any,
        object_id: Optional[str] = None,
        property_path: Optional[str] = None,
    ) -> int:
        """Push an incoming source value to all matching READ/BOTH bindings.

        Optional ``object_id`` and ``property_path`` narrow which bindings are
        updated when the same key feeds multiple scene properties.

        Returns:
            Number of bindings that were updated.
        """
        ...

    @abstractmethod
    def poll_source_to_scene(self) -> int:
        """Read the bound object and apply current values to all READ/BOTH bindings.

        Returns:
            Number of bindings that were updated.
        """
        ...

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the bridge's binding configuration to a dictionary."""
        ...

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore binding configuration from a dictionary created by :meth:`to_dict`.

        Clears all existing bindings before loading.
        """
        ...
