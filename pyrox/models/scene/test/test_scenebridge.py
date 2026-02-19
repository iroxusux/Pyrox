"""Unit tests for generic SceneBridge."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import patch

from pyrox.models.scene.scenebridge import (
    BindingDirection,
    SceneBinding,
    SceneBridge,
)
from pyrox.interfaces import IScene


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

    def test_default_bound_object_is_created(self):
        bridge = _InstrumentedSceneBridge(scene=cast(IScene, self.scene), bound_object=None)
        self.assertEqual(bridge.get_bound_object(), {"defaults": {"seed": 1}})

    def test_set_bound_object_none_resets_to_default(self):
        self.bridge.set_bound_object({"custom": {"x": 1}})
        self.assertIn("custom", self.bridge.get_bound_object())

        self.bridge.set_bound_object(None)
        self.assertEqual(self.bridge.get_bound_object(), {"defaults": {"seed": 1}})

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
        self.assertEqual(len(self.bridge.get_bindings_for_tag("source.speed")), 1)

    def test_remove_binding_returns_true_when_exists(self):
        self.bridge.add_binding("source.speed", "conveyor_1", "speed")

        removed = self.bridge.remove_binding("source.speed", "conveyor_1", "speed")
        self.assertTrue(removed)
        self.assertEqual(len(self.bridge.get_bindings()), 0)

    def test_remove_binding_returns_false_when_missing(self):
        removed = self.bridge.remove_binding("missing", "conveyor_1", "speed")
        self.assertFalse(removed)

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
        self.bridge.start()  # second call should be a no-op
        self.assertTrue(self.bridge.is_active())
        self.assertEqual(self.bridge.on_start_calls, 1)

    def test_stop_twice_is_safe(self):
        self.bridge.start()
        self.bridge.stop()
        self.bridge.stop()  # second stop must not raise or call _on_stop again
        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.on_stop_calls, 1)

    def test_stop_deactivates_read_and_both_bindings_and_unregisters_tick(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.both", "conveyor_1", "pose.x", BindingDirection.BOTH)
        self.bridge.start()

        self.bridge.stop()

        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.on_stop_calls, 1)
        self.assertEqual(len(self.bridge.deactivated), 2)
        self.assertIsNotNone(self.bridge.unregistered_callback)

    def test_set_scene_while_active_stops_bridge(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()

        new_scene = _DummyScene()
        self.bridge.set_scene(cast(IScene, new_scene))

        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.get_scene(), new_scene)

    def test_handle_source_update_applies_to_read_and_both_only(self):
        self.bridge.add_binding("src.value", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.value", "conveyor_1", "pose.x", BindingDirection.BOTH)
        self.bridge.add_binding("src.value", "conveyor_1", "status.active", BindingDirection.WRITE)

        updated = self.bridge.handle_source_update("src.value", 42)

        self.assertEqual(updated, 2)
        self.assertEqual(self.scene_obj.speed, 42)
        self.assertEqual(self.scene_obj.pose.x, 42)
        self.assertFalse(self.scene_obj.status.active)

    def test_handle_source_update_respects_filters(self):
        self.bridge.add_binding("src.value", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("src.value", "conveyor_1", "pose.x", BindingDirection.READ)

        updated = self.bridge.handle_source_update(
            "src.value",
            11,
            object_id="conveyor_1",
            property_path="speed",
        )

        self.assertEqual(updated, 1)
        self.assertEqual(self.scene_obj.speed, 11)
        self.assertEqual(self.scene_obj.pose.x, 0.0)

    def test_poll_source_to_scene_reads_bound_object(self):
        self.bridge.set_bound_object({"inputs": {"speed": 9, "active": True}})
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("inputs.active", "conveyor_1", "status.active", BindingDirection.BOTH)

        updated = self.bridge.poll_source_to_scene()

        self.assertEqual(updated, 2)
        self.assertEqual(self.scene_obj.speed, 9)
        self.assertTrue(self.scene_obj.status.active)

    @patch("time.time", side_effect=[1.0, 1.0, 1.5])
    def test_update_scene_to_source_writes_and_respects_throttle(self, _mock_time):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        self.bridge.set_write_throttle(1000.0)

        self.scene_obj.speed = 77
        self.bridge.start()
        self.bridge.update_scene_to_source()
        self.bridge.update_scene_to_source()  # throttled

        self.assertEqual(self.bridge.get_bound_object()["outputs"]["speed"], 77)
        self.assertEqual(self.bridge.writes, [("outputs.speed", 77)])

    def test_update_scene_to_source_applies_inverse_transform(self):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding(
            "outputs.speed",
            "conveyor_1",
            "speed",
            BindingDirection.WRITE,
            inverse_transform=lambda value: value * 2,
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

    def test_force_write_binding_success_and_failures(self):
        self.bridge.set_bound_object({"outputs": {}})
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)

        self.scene_obj.speed = 33
        self.assertTrue(self.bridge.force_write_binding("outputs.speed", "conveyor_1", "speed"))
        self.assertFalse(self.bridge.force_write_binding("missing", "conveyor_1", "speed"))

    def test_clear_bindings_stops_and_clears_state(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()

        self.bridge.clear_bindings()

        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.get_bindings(), [])

    def test_nested_helpers_handle_dict_and_object_paths(self):
        bound = {"a": {"b": {"c": 1}}}
        self.bridge.set_bound_object(bound)

        self.assertEqual(self.bridge._get_bound_property("a.b.c"), 1)
        self.bridge._set_bound_property("a.b.d", 2)
        self.assertEqual(bound["a"]["b"]["d"], 2)

        self.assertEqual(self.bridge._get_scene_property("conveyor_1", "pose.x"), 0.0)
        self.bridge._set_scene_property("conveyor_1", "pose.x", 8.0)
        self.assertEqual(self.scene_obj.pose.x, 8.0)

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
        cloned_binding = clone.get_bindings()[0]
        self.assertEqual(cloned_binding.binding_key, "input.speed")
        self.assertEqual(cloned_binding.direction, BindingDirection.BOTH)
        self.assertEqual(cloned_binding.description, "speed binding")
        self.assertEqual(cloned_binding.tags, ["runtime", "sync"])
        self.assertEqual(cloned_binding.metadata, {"units": "m/s"})
        self.assertFalse(clone.is_write_enabled())
        self.assertEqual(clone.get_write_throttle(), 250.0)

    def test_from_dict_accepts_legacy_tag_name(self):
        data = {
            "bindings": [
                {
                    "tag_name": "legacy.key",
                    "object_id": "conveyor_1",
                    "property_path": "speed",
                    "direction": "read",
                    "enabled": False,
                }
            ],
            "write_enabled": True,
            "write_throttle_ms": 50.0,
        }

        self.bridge.from_dict(data)

        self.assertEqual(len(self.bridge.get_bindings()), 1)
        binding = self.bridge.get_bindings()[0]
        self.assertEqual(binding.binding_key, "legacy.key")
        self.assertFalse(binding.enabled)
        self.assertEqual(self.bridge.get_write_throttle(), 50.0)

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


if __name__ == "__main__":
    unittest.main()
