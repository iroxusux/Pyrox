"""Unit tests for generic SceneBridge."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from pyrox.interfaces import IScene
from pyrox.models.scene.scenebridge import (
    BindingDirection,
    SceneBinding,
    SceneBridge,
)


class _DummyScene:
    def __init__(self):
        self._objects: dict[str, object] = {}

    def add(self, object_id: str, obj: object) -> None:
        self._objects[object_id] = obj

    def get_scene_object(self, object_id: str):
        return self._objects.get(object_id)


class _InstrumentedSceneBridge(SceneBridge):
    def __init__(self, scene=None, bound_object=None):
        self.on_start_calls = 0
        self.on_stop_calls = 0
        self.activated: list[tuple[str, str, str]] = []
        self.deactivated: list[tuple[str, str, str]] = []
        self.registered_callback = None
        self.unregistered_callback = None
        self.writes: list[tuple[str, object]] = []
        super().__init__(scene=scene, bound_object=bound_object)

    def create_default_bound_object(self):
        return {"defaults": {"seed": 1}}

    def _on_start(self) -> None:
        self.on_start_calls += 1

    def _on_stop(self) -> None:
        self.on_stop_calls += 1

    def _on_binding_activated(self, binding: SceneBinding) -> None:
        self.activated.append((binding.binding_key, binding.object_id, binding.property_path))

    def _on_binding_deactivated(self, binding: SceneBinding) -> None:
        self.deactivated.append((binding.binding_key, binding.object_id, binding.property_path))

    def _register_tick_callback(self, callback):
        self.registered_callback = callback
        return True

    def _unregister_tick_callback(self, callback):
        self.unregistered_callback = callback

    def _write_source_value(self, binding: SceneBinding, value):
        self.writes.append((binding.binding_key, value))
        super()._write_source_value(binding, value)


class TestSceneBinding(unittest.TestCase):
    """Tests for the SceneBinding dataclass."""

    def test_defaults(self):
        binding = SceneBinding(
            binding_key="src.x",
            object_id="obj_1",
            property_path="x",
        )
        self.assertEqual(binding.direction, BindingDirection.READ)
        self.assertTrue(binding.enabled)
        self.assertIsNone(binding.last_source_value)
        self.assertIsNone(binding.last_scene_value)
        self.assertEqual(binding.tags, [])
        self.assertEqual(binding.metadata, {})


class TestSceneBridge(unittest.TestCase):

    def setUp(self):
        self.scene = _DummyScene()
        self.scene_obj = SimpleNamespace(
            speed=0,
            status=SimpleNamespace(active=False),
            pose=SimpleNamespace(x=0.0),
        )
        self.scene.add("conveyor_1", self.scene_obj)
        self.bridge = _InstrumentedSceneBridge(scene=cast(IScene, self.scene))

    # ------------------------------------------------------------------
    # Bound-object
    # ------------------------------------------------------------------

    def test_default_bound_object_is_created(self):
        bridge = _InstrumentedSceneBridge(scene=cast(IScene, self.scene), bound_object=None)
        self.assertEqual(bridge.get_bound_object(), {"defaults": {"seed": 1}})

    def test_set_bound_object_none_resets_to_default(self):
        self.bridge.set_bound_object({"custom": {"x": 1}})
        self.assertIn("custom", self.bridge.get_bound_object())
        self.bridge.set_bound_object(None)
        self.assertEqual(self.bridge.get_bound_object(), {"defaults": {"seed": 1}})

    # ------------------------------------------------------------------
    # Binding management
    # ------------------------------------------------------------------

    def test_add_binding_and_query_methods(self):
        binding = self.bridge.add_binding(
            binding_key="source.speed",
            object_id="conveyor_1",
            property_path="speed",
            direction=BindingDirection.READ,
        )
        self.assertEqual(binding.binding_key, "source.speed")
        self.assertEqual(len(self.bridge.get_bindings()), 1)
        self.assertEqual(len(self.bridge.get_bindings_for_object("conveyor_1")), 1)
        self.assertEqual(len(self.bridge.get_bindings_for_key("source.speed")), 1)

    def test_remove_binding_returns_true_when_exists(self):
        self.bridge.add_binding("source.speed", "conveyor_1", "speed")
        removed = self.bridge.remove_binding("source.speed", "conveyor_1", "speed")
        self.assertTrue(removed)
        self.assertEqual(len(self.bridge.get_bindings()), 0)

    def test_remove_binding_returns_false_when_missing(self):
        self.assertFalse(self.bridge.remove_binding("missing", "conveyor_1", "speed"))

    def test_clear_bindings_stops_and_clears_state(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()
        self.bridge.clear_bindings()
        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.get_bindings(), [])

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def test_start_requires_scene(self):
        bridge = _InstrumentedSceneBridge(scene=None)
        bridge.start()
        self.assertFalse(bridge.is_active())
        self.assertEqual(bridge.on_start_calls, 0)

    def test_start_activates_read_and_both_bindings_and_registers_tick(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.both", "conveyor_1", "pose.x", BindingDirection.BOTH)
        self.bridge.add_binding("src.write", "conveyor_1", "status.active", BindingDirection.WRITE)
        self.bridge.start()
        self.assertTrue(self.bridge.is_active())
        self.assertEqual(self.bridge.on_start_calls, 1)
        self.assertEqual(len(self.bridge.activated), 2)
        self.assertIsNotNone(self.bridge.registered_callback)

    def test_start_twice_is_idempotent(self):
        self.bridge.start()
        self.bridge.start()
        self.assertEqual(self.bridge.on_start_calls, 1)

    def test_stop_deactivates_read_and_both_bindings_and_unregisters_tick(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.both", "conveyor_1", "pose.x", BindingDirection.BOTH)
        self.bridge.start()
        self.bridge.stop()
        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.on_stop_calls, 1)
        self.assertEqual(len(self.bridge.deactivated), 2)
        self.assertIsNotNone(self.bridge.unregistered_callback)

    def test_stop_when_inactive_is_safe(self):
        self.bridge.stop()
        self.assertEqual(self.bridge.on_stop_calls, 0)

    def test_set_scene_while_active_stops_bridge(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()
        new_scene = _DummyScene()
        self.bridge.set_scene(cast(IScene, new_scene))
        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.get_scene(), new_scene)

    def test_binding_activated_when_added_after_start(self):
        self.bridge.start()
        self.bridge.add_binding("src.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.assertEqual(len(self.bridge.activated), 1)

    # ------------------------------------------------------------------
    # Write config
    # ------------------------------------------------------------------

    def test_write_enabled_defaults_true(self):
        self.assertTrue(self.bridge.is_write_enabled())

    def test_set_write_enabled(self):
        self.bridge.set_write_enabled(False)
        self.assertFalse(self.bridge.is_write_enabled())

    def test_write_throttle_default_and_setter(self):
        self.assertEqual(self.bridge.get_write_throttle(), 100.0)
        self.bridge.set_write_throttle(500.0)
        self.assertEqual(self.bridge.get_write_throttle(), 500.0)

    # ------------------------------------------------------------------
    # Source → Scene sync
    # ------------------------------------------------------------------

    def test_handle_source_update_applies_to_read_and_both_only(self):
        self.bridge.add_binding("src.value", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.value", "conveyor_1", "pose.x", BindingDirection.BOTH)
        self.bridge.add_binding("src.value", "conveyor_1", "status.active", BindingDirection.WRITE)
        updated = self.bridge.handle_source_update("src.value", 42)
        self.assertEqual(updated, 2)
        self.assertEqual(self.scene_obj.speed, 42)
        self.assertEqual(self.scene_obj.pose.x, 42)
        self.assertFalse(self.scene_obj.status.active)  # WRITE not updated

    def test_handle_source_update_respects_object_and_path_filters(self):
        self.bridge.add_binding("src.value", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.value", "conveyor_1", "pose.x", BindingDirection.READ)
        updated = self.bridge.handle_source_update(
            "src.value", 11,
            object_id="conveyor_1",
            property_path="speed",
        )
        self.assertEqual(updated, 1)
        self.assertEqual(self.scene_obj.speed, 11)
        self.assertEqual(self.scene_obj.pose.x, 0.0)

    def test_handle_source_update_skips_disabled_bindings(self):
        binding = self.bridge.add_binding("src.value", "conveyor_1", "speed", BindingDirection.READ)
        binding.enabled = False
        updated = self.bridge.handle_source_update("src.value", 99)
        self.assertEqual(updated, 0)
        self.assertEqual(self.scene_obj.speed, 0)

    def test_handle_source_update_applies_transform(self):
        self.bridge.add_binding(
            "src.speed", "conveyor_1", "speed",
            direction=BindingDirection.READ,
            transform=lambda v: v / 10.0,
        )
        self.bridge.handle_source_update("src.speed", 100)
        self.assertAlmostEqual(self.scene_obj.speed, 10.0)

    def test_poll_source_to_scene_reads_bound_object(self):
        self.bridge.set_bound_object({"inputs": {"speed": 9, "active": True}})
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("inputs.active", "conveyor_1", "status.active", BindingDirection.BOTH)
        updated = self.bridge.poll_source_to_scene()
        self.assertEqual(updated, 2)
        self.assertEqual(self.scene_obj.speed, 9)
        self.assertTrue(self.scene_obj.status.active)

    # ------------------------------------------------------------------
    # Scene → Source sync
    # ------------------------------------------------------------------

    @patch("time.time", side_effect=[1.0, 1.0, 1.5])
    def test_update_scene_to_source_writes_and_respects_throttle(self, _mock_time):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        self.bridge.set_write_throttle(1000.0)
        self.scene_obj.speed = 77
        self.bridge.start()
        self.bridge.update_scene_to_source()
        self.bridge.update_scene_to_source()   # throttled — should not write again
        self.assertEqual(self.bridge.get_bound_object()["outputs"]["speed"], 77)
        self.assertEqual(self.bridge.writes, [("outputs.speed", 77)])

    def test_update_scene_to_source_applies_inverse_transform(self):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding(
            "outputs.speed", "conveyor_1", "speed",
            BindingDirection.WRITE,
            inverse_transform=lambda v: v * 2,
        )
        self.scene_obj.speed = 5
        self.bridge.start()
        self.bridge.update_scene_to_source()
        self.assertEqual(self.bridge.get_bound_object()["outputs"]["speed"], 10)

    def test_update_scene_to_source_skips_when_write_disabled(self):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        self.bridge.start()
        self.bridge.set_write_enabled(False)
        self.scene_obj.speed = 123
        self.bridge.update_scene_to_source()
        self.assertNotIn("speed", self.bridge.get_bound_object()["outputs"])

    def test_force_write_binding_success(self):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        self.scene_obj.speed = 33
        self.assertTrue(self.bridge.force_write_binding("outputs.speed", "conveyor_1", "speed"))
        self.assertEqual(self.bridge.get_bound_object()["outputs"]["speed"], 33)

    def test_force_write_binding_missing_returns_false(self):
        self.assertFalse(self.bridge.force_write_binding("missing", "conveyor_1", "speed"))

    def test_force_write_binding_read_direction_returns_false(self):
        self.bridge.add_binding("src.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.assertFalse(self.bridge.force_write_binding("src.speed", "conveyor_1", "speed"))

    def test_force_write_binding_disabled_returns_false(self):
        self.bridge.set_bound_object({"outputs": {}})
        b = self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        b.enabled = False
        self.assertFalse(self.bridge.force_write_binding("outputs.speed", "conveyor_1", "speed"))

    # ------------------------------------------------------------------
    # Nested property helpers
    # ------------------------------------------------------------------

    def test_nested_helpers_handle_dict_paths(self):
        bound = {"a": {"b": {"c": 1}}}
        self.bridge.set_bound_object(bound)
        self.assertEqual(self.bridge._get_bound_property("a.b.c"), 1)
        self.bridge._set_bound_property("a.b.d", 2)
        self.assertEqual(bound["a"]["b"]["d"], 2)

    def test_nested_helpers_handle_object_paths(self):
        self.assertEqual(self.bridge._get_scene_property("conveyor_1", "pose.x"), 0.0)
        self.bridge._set_scene_property("conveyor_1", "pose.x", 8.0)
        self.assertEqual(self.scene_obj.pose.x, 8.0)

    def test_get_scene_property_returns_none_for_missing_object(self):
        self.assertIsNone(self.bridge._get_scene_property("no_such_obj", "speed"))

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def test_get_binding_stats_counts_types_and_enabled(self):
        self.bridge.add_binding("a", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("b", "conveyor_1", "pose.x", BindingDirection.WRITE)
        both = self.bridge.add_binding("c", "conveyor_1", "status.active", BindingDirection.BOTH)
        both.enabled = False
        stats = self.bridge.get_binding_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["read"], 1)
        self.assertEqual(stats["write"], 1)
        self.assertEqual(stats["both"], 1)
        self.assertEqual(stats["enabled"], 2)
        self.assertEqual(stats["disabled"], 1)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_to_dict_and_from_dict_roundtrip(self):
        self.bridge.add_binding(
            binding_key="input.speed",
            object_id="conveyor_1",
            property_path="speed",
            direction=BindingDirection.BOTH,
            description="speed binding",
            tags=["runtime", "sync"],
            metadata={"units": "m/s"},
        )
        self.bridge.set_write_enabled(False)
        self.bridge.set_write_throttle(250.0)
        data = self.bridge.to_dict()
        clone = _InstrumentedSceneBridge(scene=cast(IScene, self.scene))
        clone.from_dict(data)
        self.assertEqual(len(clone.get_bindings()), 1)
        b = clone.get_bindings()[0]
        self.assertEqual(b.binding_key, "input.speed")
        self.assertEqual(b.direction, BindingDirection.BOTH)
        self.assertEqual(b.description, "speed binding")
        self.assertEqual(b.tags, ["runtime", "sync"])
        self.assertEqual(b.metadata, {"units": "m/s"})
        self.assertFalse(clone.is_write_enabled())
        self.assertEqual(clone.get_write_throttle(), 250.0)

    def test_from_dict_clears_existing_bindings(self):
        self.bridge.add_binding("old.key", "conveyor_1", "speed")
        self.bridge.from_dict({"bindings": [], "write_enabled": True, "write_throttle_ms": 100.0})
        self.assertEqual(self.bridge.get_bindings(), [])


class TestSceneBridgeIsISceneBridge(unittest.TestCase):
    """Verify that SceneBridge satisfies the ISceneBridge contract."""

    def test_scene_bridge_inherits_iscenebridge(self):
        from pyrox.interfaces.scene.scenebridge import ISceneBridge
        self.assertTrue(issubclass(SceneBridge, ISceneBridge))

    def test_scene_binding_satisfies_iscenebinding_protocol(self):
        from pyrox.interfaces.scene.scenebridge import ISceneBinding
        binding = SceneBinding(
            binding_key="k",
            object_id="o",
            property_path="p",
        )
        self.assertIsInstance(binding, ISceneBinding)


if __name__ == "__main__":
    unittest.main()
