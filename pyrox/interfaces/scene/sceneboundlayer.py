"""Interface for the scene bound layer — a composite bound object."""
from __future__ import annotations

from typing import Any, Iterator, Optional, Protocol, runtime_checkable


@runtime_checkable
class ISceneBoundLayer(Protocol):
    """Contract for a composite bound object that aggregates named bindable sources.

    A ``SceneBoundLayer`` acts as the single ``bound_object`` attached to a
    :class:`~pyrox.interfaces.scene.scenebridge.ISceneBridge`, while internally
    hosting an ordered collection of *named sources* — each representing a
    distinct external entity (controller, keyboard, application service, etc.).

    Binding paths within the bridge naturally adopt the convention::

        "<source_name>.<property_path_on_source>"

    For example, if a ``"keyboard"`` source is registered that exposes a
    ``key_a`` attribute, the corresponding bridge binding key would be
    ``"keyboard.key_a"``.

    The layer itself is transparent to the bridge: it satisfies attribute access
    so that the bridge's nested property traversal routes through to the correct
    sub-source automatically.

    Typical usage::

        layer = SceneBoundLayer()
        layer.register_source("keyboard", keyboard_driver)
        layer.register_source("plc", plc_controller)
        layer.register_source("sim", external_app)

        bridge = MyBridge(scene=my_scene, bound_object=layer)
        bridge.add_binding(
            binding_key="plc.conveyor_speed",
            object_id="conveyor_1",
            property_path="speed",
            direction=BindingDirection.READ,
        )
        bridge.start()
    """

    # ------------------------------------------------------------------
    # Source registration
    # ------------------------------------------------------------------

    def register_source(self, name: str, source: Any) -> None:
        """Register a named bindable source.

        Args:
            name:   Identifier used to namespace property paths (e.g. ``"keyboard"``).
                    Must be a non-empty string that is a valid Python identifier.
            source: Any object whose attributes can be read from or written to
                    by the bridge (e.g. a controller instance, a data namespace,
                    an application service, etc.).

        Raises:
            ValueError: If *name* is empty or is already registered.
        """
        ...

    def unregister_source(self, name: str) -> None:
        """Remove a previously registered source by name.

        No-op if *name* is not currently registered.
        """
        ...

    # ------------------------------------------------------------------
    # Source access
    # ------------------------------------------------------------------

    def get_source(self, name: str) -> Optional[Any]:
        """Return the source registered under *name*, or ``None`` if absent."""
        ...

    def list_sources(self) -> list[str]:
        """Return the ordered list of registered source names."""
        ...

    def has_source(self, name: str) -> bool:
        """Return ``True`` if a source is registered under *name*."""
        ...

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[str]:
        """Iterate over registered source names."""
        ...

    def __len__(self) -> int:
        """Return the number of registered sources."""
        ...

    def __contains__(self, name: object) -> bool:
        """Support ``"keyboard" in layer`` membership checks."""
        ...

    # ------------------------------------------------------------------
    # Property introspection
    # ------------------------------------------------------------------

    def enumerate_source_properties(self, name: str) -> list[str]:
        """Return the sorted list of public property names on the named source.

        Private names (starting with ``_``) and callables are excluded.
        Returns an empty list when *name* is not registered.
        """
        ...

    def list_binding_keys(self) -> list[str]:
        """Return all available ``"source_name.property"`` key paths.

        Iterates every registered source and prepends its name to each exposed
        property, yielding a flat, sorted list of fully-qualified keys ready
        to use as ``binding_key`` on the bridge.
        """
        ...
