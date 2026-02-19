"""Concrete implementation of the scene bound layer.

A :class:`SceneBoundLayer` is the single ``bound_object`` passed to a
:class:`~pyrox.models.scene.scenebridge.SceneBridge`.  Internally it hosts a
named collection of *sources* — individual objects such as external controllers,
keyboard drivers, application services, or plain data namespaces — each
accessible through a consistent, namespaced property path.

Bridge binding keys therefore adopt a two-segment convention::

    "<source_name>.<property_path_on_source>"

This is transparent to the bridge: its existing dot-separated property
traversal naturally delegates through the layer to the correct sub-source,
requiring no changes to :class:`~pyrox.models.scene.scenebridge.SceneBridge`.
"""
from __future__ import annotations

from typing import Any, Iterator, Optional

from pyrox.services.logging import log


class SceneBoundLayer:
    """Composite bound object that aggregates named, independently bindable sources.

    Pass an instance of this class as the ``bound_object`` argument to any
    :class:`~pyrox.models.scene.scenebridge.SceneBridge` subclass.  Bindings
    whose ``binding_key`` starts with a registered source name will be
    automatically routed through the layer to that source during both read
    (source → scene) and write (scene → source) sync cycles.

    Example::

        layer = SceneBoundLayer()
        layer.register_source("keyboard", keyboard_driver)
        layer.register_source("plc", my_controller)
        layer.register_source("sim", external_app)

        bridge = MyBridge(scene=my_scene, bound_object=layer)

        # Reads `my_controller.conveyor_speed` and pushes it to the scene.
        bridge.add_binding(
            binding_key="plc.conveyor_speed",
            object_id="belt_1",
            property_path="speed",
            direction=BindingDirection.READ,
        )

    Attribute access is routed to sources via :meth:`__getattr__`, so all three
    of the following are equivalent::

        layer.keyboard          # __getattr__ lookup
        layer.get_source("keyboard")
        layer["keyboard"]       # __getitem__ lookup

    Sources may be any Python object — plain ``dict``, ``SimpleNamespace``,
    dataclass, or a full domain model.  The bridge's nested property traversal
    handles both attribute-style and dict-style sub-properties automatically.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Use object.__setattr__ to avoid triggering our custom __setattr__ before
        # _sources is initialised.
        object.__setattr__(self, '_sources', {})

    # ------------------------------------------------------------------
    # Source registration
    # ------------------------------------------------------------------

    def register_source(self, name: str, source: Any) -> None:
        """Register a named bindable source.

        Args:
            name:   Non-empty Python identifier used to namespace binding paths.
            source: Any object whose properties will be read from / written to
                    by the bridge.

        Raises:
            ValueError: If *name* is empty or not a valid Python identifier.
            KeyError:   If a source is already registered under *name*.
        """
        if not name:
            raise ValueError("Source name cannot be empty")
        if not name.isidentifier():
            raise ValueError(f"Source name '{name}' is not a valid Python identifier")

        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        if name in sources:
            raise KeyError(f"A source named '{name}' is already registered; "
                           f"call unregister_source first to replace it")

        sources[name] = source
        log(self).info(f"Registered source '{name}' ({type(source).__name__})")

    def unregister_source(self, name: str) -> None:
        """Remove a registered source.  No-op if *name* is not present."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        if name in sources:
            del sources[name]
            log(self).info(f"Unregistered source '{name}'")

    # ------------------------------------------------------------------
    # Source access
    # ------------------------------------------------------------------

    def get_source(self, name: str) -> Optional[Any]:
        """Return the source registered under *name*, or ``None`` if absent."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return sources.get(name)

    def list_sources(self) -> list[str]:
        """Return the ordered list of registered source names."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return list(sources.keys())

    def has_source(self, name: str) -> bool:
        """Return ``True`` if *name* is currently registered."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return name in sources

    # ------------------------------------------------------------------
    # Attribute / item proxying
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        """Route attribute access to the registered source named *name*.

        This allows the bridge's nested property traversal to resolve paths
        such as ``"plc.conveyor_speed"`` transparently::

            layer.plc          # returns the 'plc' source
            layer.plc.conveyor_speed  # reads the conveyor_speed property

        Raises:
            AttributeError: If no source is registered under *name*.
        """
        # Guard: don't intercept dunder or private names — they go through
        # normal attribute resolution and raise AttributeError if absent.
        if name.startswith('_'):
            raise AttributeError(name)

        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        if name in sources:
            return sources[name]

        raise AttributeError(
            f"'{type(self).__name__}' has no source named '{name}'. "
            f"Registered sources: {list(sources.keys())}"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        """Route attribute assignment to the registered source named *name*.

        If a source is registered under *name* the assignment is forwarded to
        it directly (replacing the registered object with *value*).  This
        mirrors how the bridge's ``_set_nested_value`` method writes back
        properties when the layer is the root of a write path.

        For any name that is *not* an existing source the default object
        attribute mechanism is used.
        """
        if not name.startswith('_'):
            sources: dict[str, Any] = object.__getattribute__(self, '_sources')
            if name in sources:
                sources[name] = value
                return

        object.__setattr__(self, name, value)

    def __getitem__(self, name: str) -> Any:
        """Return the source registered under *name* (dict-style access)."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        try:
            return sources[name]
        except KeyError:
            raise KeyError(f"No source named '{name}' registered in this layer")

    def __setitem__(self, name: str, source: Any) -> None:
        """Register or replace a source using dict-style assignment."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        sources[name] = source

    # ------------------------------------------------------------------
    # Iteration & membership
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[str]:
        """Iterate over registered source names."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return iter(list(sources.keys()))

    def __len__(self) -> int:
        """Return the number of registered sources."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return len(sources)

    def __contains__(self, name: object) -> bool:
        """Support ``"keyboard" in layer`` membership checks."""
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        return name in sources

    # ------------------------------------------------------------------
    # Property introspection
    # ------------------------------------------------------------------

    def enumerate_source_properties(self, name: str) -> list[str]:
        """Return the list of public property names exposed by the named source.

        Supports plain dicts (string keys), objects with ``__dict__``
        (dataclasses, SimpleNamespace, regular instances) and any other object
        via :func:`dir`.  Private names (starting with ``_``) and callables
        are excluded.

        Args:
            name: Registered source name.

        Returns:
            Sorted list of property name strings.  Empty list if the source is
            not registered or has no inspectable public properties.
        """
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        source = sources.get(name)
        if source is None:
            return []
        return self._inspect_properties(source)

    def list_binding_keys(self) -> list[str]:
        """Return all available ``"source_name.property"`` binding key paths.

        Iterates every registered source and prepends its name to each exposed
        property, yielding a flat, sorted list of fully-qualified keys ready to
        use as ``binding_key`` arguments on the bridge.

        Example::

            layer.register_source("plc", SimpleNamespace(speed=0, active=True))
            layer.register_source("keyboard", SimpleNamespace(key_a=False))
            layer.list_binding_keys()
            # ['keyboard.key_a', 'plc.active', 'plc.speed']
        """
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        keys: list[str] = []
        for source_name, source in sources.items():
            for prop in self._inspect_properties(source):
                keys.append(f"{source_name}.{prop}")
        return sorted(keys)

    @staticmethod
    def _inspect_properties(source: Any) -> list[str]:
        """Return public, non-callable property names for *source*."""
        if isinstance(source, dict):
            return sorted(k for k in source if isinstance(k, str) and not k.startswith('_'))

        # Use dir() so both class-level and instance-level attributes are found.
        result = []
        for name in dir(source):
            if name.startswith('_'):
                continue
            try:
                val = getattr(source, name)
            except Exception:
                continue
            if callable(val):
                continue
            result.append(name)
        return sorted(result)

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        sources: dict[str, Any] = object.__getattribute__(self, '_sources')
        names = list(sources.keys())
        return f"SceneBoundLayer(sources={names})"
