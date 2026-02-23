"""Generic scene bridge models.

Provides a reusable base bridge for synchronizing data between scene object
properties and an external source object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable, Optional

from pyrox.interfaces import (
    BindingDirection,
    IScene,
    ISceneBridge,
    ISceneBinding,
    ISceneBoundLayer,
)
from pyrox.services.logging import log


@dataclass
class SceneBinding:
    """Concrete binding record.

    Satisfies the :class:`~pyrox.interfaces.ISceneBinding` Protocol structurally —
    no explicit inheritance needed.  Type checkers enforce the contract at use sites.
    """

    binding_key: str
    object_id: str
    property_path: str
    direction: BindingDirection = BindingDirection.READ
    transform: Optional[Callable[[Any], Any]] = None
    inverse_transform: Optional[Callable[[Any], Any]] = None
    enabled: bool = True
    last_source_value: Any = None
    last_scene_value: Any = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SceneBridge(ISceneBridge):
    """Generic service that bridges scene object properties with a source object.

    Subclasses can override the hook methods to integrate transports such as
    sockets, queues, APIs, file watchers, or simulation buses.
    """

    def __init__(
        self,
        scene: Optional[IScene] = None,
        bound_object: Optional[ISceneBoundLayer] = None,
    ):
        self._scene = scene
        self._bound_object = (
            bound_object if bound_object is not None else self.create_default_bound_object()
        )
        self._bindings: dict[str, SceneBinding] = {}
        self._active = False
        self._write_enabled = True
        self._last_write_time: dict[str, float] = {}
        self._write_throttle_ms = 100.0
        self._last_read_time: dict[str, float] = {}
        self._read_throttle_ms = 100.0
        self._tick_callback_registered = False

    def create_default_bound_object(self) -> ISceneBoundLayer:
        """Create the default source object for bindings.

        Subclasses should override this to provide domain-specific source objects.
        """
        # Lazy import to avoid circular dependencies with SceneBoundLayer
        from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
        return SceneBoundLayer()

    def get_scene(self) -> Optional[IScene]:
        return self._scene

    def set_scene(self, scene: Optional[IScene]) -> None:
        if self._active:
            self.stop()
        self._scene = scene

    def get_bound_object(self) -> ISceneBoundLayer:
        return self._bound_object

    def set_bound_object(self, bound_object: Optional[ISceneBoundLayer]) -> None:
        if bound_object is None:
            bound_object = self.create_default_bound_object()
        self._bound_object = bound_object

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
        binding = SceneBinding(
            binding_key=binding_key,
            object_id=object_id,
            property_path=property_path,
            direction=direction,
            transform=transform,
            inverse_transform=inverse_transform,
            description=description,
            tags=tags or [],
            metadata=metadata or {},
        )

        binding_id = self._binding_id(binding_key, object_id, property_path)
        self._bindings[binding_id] = binding

        if self._active and direction in (BindingDirection.READ, BindingDirection.BOTH):
            self._on_binding_activated(binding)

        log(self).debug(
            f"Added binding: {binding_key} -> {object_id}.{property_path} ({direction.value})"
        )
        return binding

    def remove_binding(self, binding_key: str, object_id: str, property_path: str) -> bool:
        binding_id = self._binding_id(binding_key, object_id, property_path)
        binding = self._bindings.get(binding_id)
        if not binding:
            return False

        if self._active and binding.direction in (BindingDirection.READ, BindingDirection.BOTH):
            self._on_binding_deactivated(binding)

        del self._bindings[binding_id]
        log(self).debug(f"Removed binding: {binding_id}")
        return True

    def clear_bindings(self) -> None:
        if self._active:
            self.stop()
        self._bindings.clear()
        self._last_write_time.clear()
        self._last_read_time.clear()
        log(self).debug("Cleared all bindings")

    def get_bindings(self) -> list[ISceneBinding]:
        return list(self._bindings.values())

    def get_bindings_for_object(self, object_id: str) -> list[ISceneBinding]:
        return [binding for binding in self._bindings.values() if binding.object_id == object_id]

    def get_bindings_for_key(self, binding_key: str) -> list[ISceneBinding]:
        return [binding for binding in self._bindings.values() if binding.binding_key == binding_key]

    def is_active(self) -> bool:
        return self._active

    def is_write_enabled(self) -> bool:
        return self._write_enabled

    def set_write_enabled(self, enabled: bool) -> None:
        self._write_enabled = enabled
        log(self).debug(f"Bridge write {'enabled' if enabled else 'disabled'}")

    def get_write_throttle(self) -> float:
        return self._write_throttle_ms

    def set_write_throttle(self, throttle_ms: float) -> None:
        self._write_throttle_ms = throttle_ms
        log(self).debug(f"Bridge write throttle set to {throttle_ms}ms")

    def get_read_throttle(self) -> float:
        return self._read_throttle_ms

    def set_read_throttle(self, throttle_ms: float) -> None:
        self._read_throttle_ms = throttle_ms
        log(self).debug(f"Bridge read throttle set to {throttle_ms}ms")

    def get_binding_stats(self) -> dict[str, Any]:
        read_count = sum(
            1 for binding in self._bindings.values() if binding.direction == BindingDirection.READ
        )
        write_count = sum(
            1 for binding in self._bindings.values() if binding.direction == BindingDirection.WRITE
        )
        both_count = sum(
            1 for binding in self._bindings.values() if binding.direction == BindingDirection.BOTH
        )
        enabled_count = sum(1 for binding in self._bindings.values() if binding.enabled)

        return {
            "total": len(self._bindings),
            "enabled": enabled_count,
            "disabled": len(self._bindings) - enabled_count,
            "read": read_count,
            "write": write_count,
            "both": both_count,
            "active": self._active,
            "write_enabled": self._write_enabled,
        }

    def start(self) -> None:
        if self._active:
            log(self).warning("Bridge already active")
            return

        if not self._scene:
            log(self).error("Cannot start bridge without a scene")
            return

        self._on_start()

        for binding in self._bindings.values():
            if binding.enabled and binding.direction in (BindingDirection.READ, BindingDirection.BOTH):
                self._on_binding_activated(binding)

        if not self._tick_callback_registered:
            self._tick_callback_registered = self._register_tick_callback(self._on_tick)

        self._active = True
        log(self).debug(f"Scene bridge started with {len(self._bindings)} bindings")

    def stop(self) -> None:
        if not self._active:
            return

        for binding in self._bindings.values():
            if binding.direction in (BindingDirection.READ, BindingDirection.BOTH):
                self._on_binding_deactivated(binding)

        if self._tick_callback_registered:
            self._unregister_tick_callback(self._on_tick)
            self._tick_callback_registered = False

        self._on_stop()
        self._active = False
        log(self).debug("Scene bridge stopped")

    def _on_tick(self, *_) -> None:
        self.update_source_to_scene()
        self.update_scene_to_source()

    def update_scene_to_source(self) -> None:
        if not self._active or not self._write_enabled:
            return

        current_time = time.time() * 1000

        for binding in self._bindings.values():
            if not binding.enabled:
                continue

            if binding.direction not in (BindingDirection.WRITE, BindingDirection.BOTH):
                continue

            last_write = self._last_write_time.get(binding.binding_key, 0)
            if current_time - last_write < self._write_throttle_ms:
                continue

            scene_value = self._get_scene_property(binding.object_id, binding.property_path)
            if scene_value is None:
                continue

            if scene_value == binding.last_scene_value:
                continue

            source_value = scene_value
            if binding.inverse_transform:
                try:
                    source_value = binding.inverse_transform(scene_value)
                except Exception as exc:
                    log(self).error(f"Transform error for {binding.binding_key}: {exc}")
                    binding.enabled = False
                    continue

            try:
                self._write_source_value(binding, source_value)
            except Exception as exc:
                log(self).error(f"Write error for {binding.binding_key}: {exc}")
                binding.enabled = False
                continue

            binding.last_scene_value = scene_value
            self._last_write_time[binding.binding_key] = current_time

    def force_write_binding(self, binding_key: str, object_id: str, property_path: str) -> bool:
        binding_id = self._binding_id(binding_key, object_id, property_path)
        binding = self._bindings.get(binding_id)
        if not binding:
            log(self).warning(f"Binding not found: {binding_id}")
            return False

        if not binding.enabled:
            log(self).warning(f"Binding disabled: {binding_id}")
            return False

        if binding.direction not in (BindingDirection.WRITE, BindingDirection.BOTH):
            log(self).warning(f"Binding is not configured for writing: {binding_id}")
            return False

        scene_value = self._get_scene_property(binding.object_id, binding.property_path)
        if scene_value is None:
            log(self).warning(f"Could not get scene value for {binding_id}")
            return False

        source_value = scene_value
        if binding.inverse_transform:
            try:
                source_value = binding.inverse_transform(scene_value)
            except Exception as exc:
                log(self).error(f"Transform error for {binding.binding_key}: {exc}")
                return False

        try:
            self._write_source_value(binding, source_value)
        except Exception as exc:
            log(self).error(f"Force write error for {binding.binding_key}: {exc}")
            return False

        binding.last_scene_value = scene_value
        self._last_write_time[binding.binding_key] = time.time() * 1000
        log(self).debug(f"Force wrote source value: {binding.binding_key} = {source_value}")
        return True

    def handle_source_update(
        self,
        binding_key: str,
        value: Any,
        object_id: Optional[str] = None,
        property_path: Optional[str] = None,
    ) -> int:
        """Apply source updates to matching scene bindings.

        Returns the number of bindings updated.
        """

        updated = 0
        for binding in self._bindings.values():
            if not binding.enabled:
                continue
            if binding.direction not in (BindingDirection.READ, BindingDirection.BOTH):
                continue
            if binding.binding_key != binding_key:
                continue
            if object_id is not None and binding.object_id != object_id:
                continue
            if property_path is not None and binding.property_path != property_path:
                continue

            self._apply_source_value_to_scene(binding, value)
            updated += 1

        return updated

    def poll_source_to_scene(self) -> int:
        """Poll source values for READ/BOTH bindings and apply them to the scene."""

        updated = 0
        for binding in self._bindings.values():
            if not binding.enabled:
                continue
            if binding.direction not in (BindingDirection.READ, BindingDirection.BOTH):
                continue

            try:
                source_value = self._read_source_value(binding)
            except Exception as exc:
                log(self).error(f"Read error for {binding.binding_key}: {exc}")
                continue

            if source_value is None:
                continue

            self._apply_source_value_to_scene(binding, source_value)
            updated += 1

        return updated

    def update_source_to_scene(self) -> None:
        """Tick-driven source → scene sync for READ/BOTH bindings.

        Mirrors :meth:`update_scene_to_source` in the opposite direction.  On each
        tick the bound object is polled for every READ or BOTH binding; values that
        have not changed since the last application are skipped, and repeated calls
        within the configured :attr:`read_throttle_ms` window are suppressed.

        Called automatically by :meth:`_on_tick` — invoke manually only when an
        out-of-band forced refresh is needed.
        """
        if not self._active:
            return

        current_time = time.time() * 1000

        for binding in self._bindings.values():
            if not binding.enabled:
                continue

            if binding.direction not in (BindingDirection.READ, BindingDirection.BOTH):
                continue

            last_read = self._last_read_time.get(binding.binding_key, 0)
            if current_time - last_read < self._read_throttle_ms:
                continue

            try:
                source_value = self._read_source_value(binding)
            except Exception as exc:
                log(self).error(f"Read error for {binding.binding_key}: {exc}")
                binding.enabled = False
                continue

            if source_value is None:
                continue

            if source_value == binding.last_source_value:
                continue

            scene_value = source_value
            if binding.transform:
                try:
                    scene_value = binding.transform(source_value)
                except Exception as exc:
                    log(self).error(f"Transform error for {binding.binding_key}: {exc}")
                    binding.enabled = False
                    continue

            try:
                self._set_scene_property(binding.object_id, binding.property_path, scene_value)
                binding.last_source_value = source_value
                binding.last_scene_value = scene_value
                self._last_read_time[binding.binding_key] = current_time
            except Exception as exc:
                log(self).error(
                    f"Error applying {binding.binding_key} to "
                    f"{binding.object_id}.{binding.property_path}: {exc}"
                )
                binding.enabled = False

    def _apply_source_value_to_scene(self, binding: SceneBinding, source_value: Any) -> None:
        binding.last_source_value = source_value

        scene_value = source_value
        if binding.transform:
            try:
                scene_value = binding.transform(source_value)
            except Exception as exc:
                log(self).error(f"Transform error for {binding.binding_key}: {exc}")
                return

        try:
            self._set_scene_property(binding.object_id, binding.property_path, scene_value)
            binding.last_scene_value = scene_value
        except Exception as exc:
            log(self).error(
                f"Error setting {binding.object_id}.{binding.property_path} from "
                f"{binding.binding_key}: {exc}"
            )

    def _read_source_value(self, binding: SceneBinding) -> Any:
        return self._get_bound_property(binding.binding_key)

    def _write_source_value(self, binding: SceneBinding, value: Any) -> None:
        self._set_bound_property(binding.binding_key, value)

    def _on_start(self) -> None:
        """Hook for subclass startup behavior."""

    def _on_stop(self) -> None:
        """Hook for subclass teardown behavior."""

    def _on_binding_activated(self, binding: SceneBinding) -> None:
        """Hook for activating source subscriptions/watchers for a binding."""

    def _on_binding_deactivated(self, binding: SceneBinding) -> None:
        """Hook for deactivating source subscriptions/watchers for a binding."""

    def _register_tick_callback(self, callback: Callable[[], None]) -> bool:
        """Hook to register periodic callbacks.

        Return True if callback registration was successful.
        """
        if not self._scene:
            log(self).error("Cannot register tick callback without a scene")
            return False

        if callback not in self._scene.on_scene_updated:
            self._scene.on_scene_updated.append(callback)
            return True

        return False

    def _unregister_tick_callback(self, callback: Callable[[], None]) -> None:
        """Hook to unregister periodic callbacks."""
        if not self._scene:
            return

        if callback in self._scene.on_scene_updated:
            self._scene.on_scene_updated.remove(callback)

    def _get_scene_property(self, object_id: str, property_path: str) -> Any:
        if not self._scene:
            return None

        obj = self._scene.get_scene_object(object_id)
        if not obj:
            return None

        return self._get_nested_value(obj, property_path)

    def _set_scene_property(self, object_id: str, property_path: str, value: Any) -> None:
        if not self._scene:
            raise ValueError("No scene set")

        obj = self._scene.get_scene_object(object_id)
        if not obj:
            raise ValueError(f"Object {object_id} not found in scene")

        self._set_nested_value(obj, property_path, value)

    def _get_bound_property(self, property_path: str) -> Any:
        if self._bound_object is None:
            return None
        return self._get_nested_value(self._bound_object, property_path)

    def _set_bound_property(self, property_path: str, value: Any) -> None:
        if self._bound_object is None:
            raise ValueError("No bound object set")
        self._set_nested_value(self._bound_object, property_path, value)

    def _get_nested_value(self, root: Any, property_path: str) -> Any:
        current = root
        for part in property_path.split("."):
            if isinstance(current, dict):
                if part not in current:
                    return None
                current = current[part]
                continue

            if not hasattr(current, part):
                return None
            current = getattr(current, part)

        return current

    def _set_nested_value(self, root: Any, property_path: str, value: Any) -> None:
        parts = property_path.split(".")
        current = root

        for part in parts[:-1]:
            if isinstance(current, dict):
                if part not in current or current[part] is None:
                    current[part] = {}
                current = current[part]
                continue

            if not hasattr(current, part):
                raise ValueError(f"Property path {property_path} not found")
            current = getattr(current, part)

        final_part = parts[-1]
        if isinstance(current, dict):
            current[final_part] = value
            return

        setattr(current, final_part, value)

    @staticmethod
    def _binding_id(binding_key: str, object_id: str, property_path: str) -> str:
        return f"{binding_key}::{object_id}::{property_path}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "bindings": [
                {
                    "binding_key": binding.binding_key,
                    "object_id": binding.object_id,
                    "property_path": binding.property_path,
                    "direction": binding.direction.value,
                    "enabled": binding.enabled,
                    "description": binding.description,
                    "tags": binding.tags,
                    "metadata": binding.metadata,
                }
                for binding in self._bindings.values()
            ],
            "write_enabled": self._write_enabled,
            "write_throttle_ms": self._write_throttle_ms,
            "read_throttle_ms": self._read_throttle_ms,
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        self.clear_bindings()

        for binding_data in data.get("bindings", []):
            binding_key = binding_data.get("binding_key")
            if not binding_key:
                continue

            self.add_binding(
                binding_key=binding_key,
                object_id=binding_data["object_id"],
                property_path=binding_data["property_path"],
                direction=BindingDirection(binding_data["direction"]),
                description=binding_data.get("description", ""),
                tags=binding_data.get("tags", []),
                metadata=binding_data.get("metadata", {}),
            )

            binding_id = self._binding_id(
                binding_key,
                binding_data["object_id"],
                binding_data["property_path"],
            )
            self._bindings[binding_id].enabled = binding_data.get("enabled", True)

        self._write_enabled = data.get("write_enabled", True)
        self._write_throttle_ms = data.get("write_throttle_ms", 100.0)
        self._read_throttle_ms = data.get("read_throttle_ms", 100.0)
