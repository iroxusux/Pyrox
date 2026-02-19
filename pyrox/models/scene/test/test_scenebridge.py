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
from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
from pyrox.interfaces import IScene


class _DummyScene:
    def __init__(self):
        self._objects: dict[str, object] = {}
        self.on_scene_updated: list = []

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
        self.registration_call_count = 0
        self.writes: list[tuple[str, object]] = []
        super().__init__(scene=scene, bound_object=bound_object)

    def create_default_bound_object(self) -> SceneBoundLayer:
        layer = SceneBoundLayer()
        layer.register_source("defaults", SimpleNamespace(seed=1))
        return layer

    def _on_start(self) -> None:
        self.on_start_calls += 1

    def _on_stop(self) -> None:
        self.on_stop_calls += 1

    def _on_binding_activated(self, binding: SceneBinding) -> None:
        self.activated.append((binding.binding_key, binding.object_id, binding.property_path))

    def _on_binding_deactivated(self, binding: SceneBinding) -> None:
        self.deactivated.append((binding.binding_key, binding.object_id, binding.property_path))

    def _register_tick_callback(self, callback) -> bool:
        self.registered_callback = callback
        self.registration_call_count += 1
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
        bound = bridge.get_bound_object()
        self.assertIsInstance(bound, SceneBoundLayer)
        self.assertEqual(bound.get_source("defaults").seed, 1)  # type: ignore

    def test_set_bound_object_none_resets_to_default(self):
        custom = SceneBoundLayer()
        custom.register_source("custom", SimpleNamespace(x=1))
        self.bridge.set_bound_object(custom)
        self.assertIn("custom", self.bridge.get_bound_object())

        self.bridge.set_bound_object(None)
        bound = self.bridge.get_bound_object()
        self.assertIsInstance(bound, SceneBoundLayer)
        self.assertIn("defaults", bound)

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
        self.assertEqual(len(self.bridge.get_bindings_for_key("source.speed")), 1)

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
        self.assertTrue(self.bridge._tick_callback_registered)

    def test_start_twice_is_idempotent(self):
        self.bridge.start()
        self.bridge.start()  # second call should be a no-op
        self.assertTrue(self.bridge.is_active())
        self.assertEqual(self.bridge.on_start_calls, 1)
        self.assertEqual(self.bridge.registration_call_count, 1)

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
        self.assertFalse(self.bridge._tick_callback_registered)

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
        layer = SceneBoundLayer()
        layer.register_source("inputs", SimpleNamespace(speed=9, active=True))
        self.bridge.set_bound_object(layer)
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("inputs.active", "conveyor_1", "status.active", BindingDirection.BOTH)

        updated = self.bridge.poll_source_to_scene()

        self.assertEqual(updated, 2)
        self.assertEqual(self.scene_obj.speed, 9)
        self.assertTrue(self.scene_obj.status.active)

    @patch("time.time", side_effect=[1.0, 1.0, 1.5])
    def test_update_scene_to_source_writes_and_respects_throttle(self, _mock_time):
        outputs = SimpleNamespace(speed=None)
        layer = SceneBoundLayer()
        layer.register_source("outputs", outputs)
        self.bridge.set_bound_object(layer)
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)
        self.bridge.set_write_throttle(1000.0)

        self.scene_obj.speed = 77
        self.bridge.start()
        self.bridge.update_scene_to_source()
        self.bridge.update_scene_to_source()  # throttled

        self.assertEqual(outputs.speed, 77)
        self.assertEqual(self.bridge.writes, [("outputs.speed", 77)])

    def test_update_scene_to_source_applies_inverse_transform(self):
        outputs = SimpleNamespace(speed=None)
        layer = SceneBoundLayer()
        layer.register_source("outputs", outputs)
        self.bridge.set_bound_object(layer)
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

        self.assertEqual(outputs.speed, 10)

    def test_update_scene_to_source_skips_when_write_disabled(self):
        outputs = SimpleNamespace(speed=None)
        layer = SceneBoundLayer()
        layer.register_source("outputs", outputs)
        self.bridge.set_bound_object(layer)
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)

        self.bridge.start()
        self.bridge.set_write_enabled(False)
        self.scene_obj.speed = 123
        self.bridge.update_scene_to_source()

        self.assertIsNone(outputs.speed)

    def test_force_write_binding_success_and_failures(self):
        outputs = SimpleNamespace(speed=None)
        layer = SceneBoundLayer()
        layer.register_source("outputs", outputs)
        self.bridge.set_bound_object(layer)
        self.bridge.add_binding("outputs.speed", "conveyor_1", "speed", BindingDirection.WRITE)

        self.scene_obj.speed = 33
        self.assertTrue(self.bridge.force_write_binding("outputs.speed", "conveyor_1", "speed"))
        self.assertEqual(outputs.speed, 33)
        self.assertFalse(self.bridge.force_write_binding("missing", "conveyor_1", "speed"))

    def test_clear_bindings_stops_and_clears_state(self):
        self.bridge.add_binding("src.read", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()

        self.bridge.clear_bindings()

        self.assertFalse(self.bridge.is_active())
        self.assertEqual(self.bridge.get_bindings(), [])

    def test_nested_helpers_handle_object_paths(self):
        b_ns = SimpleNamespace(c=1)
        a_ns = SimpleNamespace(b=b_ns)
        layer = SceneBoundLayer()
        layer.register_source("a", a_ns)
        self.bridge.set_bound_object(layer)

        self.assertEqual(self.bridge._get_bound_property("a.b.c"), 1)
        self.bridge._set_bound_property("a.b.d", 2)
        self.assertEqual(b_ns.d, 2)

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
        self.bridge.set_read_throttle(75.0)

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
        self.assertEqual(clone.get_read_throttle(), 75.0)

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

    @patch("time.time", return_value=1.0)
    def test_on_tick_drives_both_directions(self, _):
        """_on_tick must push source→scene (READ) and scene→source (WRITE) in one cycle."""
        outputs = SimpleNamespace(speed=None)
        layer = SceneBoundLayer()
        layer.register_source("inputs", SimpleNamespace(speed=42))
        layer.register_source("outputs", outputs)
        self.bridge.set_bound_object(layer)

        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("outputs.speed", "conveyor_1", "pose.x", BindingDirection.WRITE)
        self.scene_obj.pose.x = 9.9

        self.bridge.start()
        self.bridge._on_tick()

        self.assertEqual(self.scene_obj.speed, 42)  # source → scene
        self.assertEqual(outputs.speed, 9.9)         # scene → source


class TestUpdateSourceToScene(unittest.TestCase):
    """Tests for tick-driven source → scene synchronisation."""

    def setUp(self):
        self.scene = _DummyScene()
        self.scene_obj = SimpleNamespace(
            speed=0,
            status=SimpleNamespace(active=False),
            pose=SimpleNamespace(x=0.0),
        )
        self.scene.add("conveyor_1", self.scene_obj)
        self.inputs = SimpleNamespace(speed=0, active=False)
        self.layer = SceneBoundLayer()
        self.layer.register_source("inputs", self.inputs)
        self.bridge = _InstrumentedSceneBridge(
            scene=cast(IScene, self.scene), bound_object=self.layer
        )

    @patch("time.time", return_value=1.0)
    def test_applies_to_read_and_both_only(self, _):
        """READ and BOTH bindings are applied; WRITE bindings are ignored."""
        outputs = SimpleNamespace(pose_x=0.0)
        self.layer.register_source("outputs", outputs)

        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.add_binding("inputs.active", "conveyor_1", "status.active", BindingDirection.BOTH)
        self.bridge.add_binding("outputs.pose_x", "conveyor_1", "pose.x", BindingDirection.WRITE)

        self.inputs.speed = 55
        self.inputs.active = True
        self.bridge.start()
        self.bridge.update_source_to_scene()

        self.assertEqual(self.scene_obj.speed, 55)
        self.assertTrue(self.scene_obj.status.active)
        self.assertEqual(self.scene_obj.pose.x, 0.0)  # WRITE binding left untouched

    def test_skips_when_not_active(self):
        """update_source_to_scene is a no-op when the bridge has not been started."""
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.inputs.speed = 99
        self.bridge.update_source_to_scene()
        self.assertEqual(self.scene_obj.speed, 0)

    @patch("time.time", side_effect=[1.0, 2.0])
    def test_skips_unchanged_values(self, _):
        """Source values equal to last_source_value are not re-applied to the scene."""
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.inputs.speed = 10
        self.bridge.start()

        self.bridge.update_source_to_scene()  # t=1s — applies 10
        self.assertEqual(self.scene_obj.speed, 10)

        self.scene_obj.speed = 999  # tamper with the scene directly

        self.bridge.update_source_to_scene()  # t=2s — same source value; must NOT overwrite
        self.assertEqual(self.scene_obj.speed, 999)

    @patch("time.time", return_value=1.0)
    def test_applies_transform(self, _):
        """The binding transform is applied before writing to the scene."""
        self.bridge.add_binding(
            "inputs.speed",
            "conveyor_1",
            "speed",
            BindingDirection.READ,
            transform=lambda v: v * 10,
        )
        self.inputs.speed = 3
        self.bridge.start()
        self.bridge.update_source_to_scene()
        self.assertEqual(self.scene_obj.speed, 30)

    @patch("time.time", side_effect=[1.0, 1.0])
    def test_respects_read_throttle(self, _):
        """A second call within the read throttle window is suppressed."""
        self.bridge.add_binding("inputs.speed", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.set_read_throttle(1000.0)

        self.inputs.speed = 7
        self.bridge.start()
        self.bridge.update_source_to_scene()  # t=1s — not throttled; applies 7
        self.assertEqual(self.scene_obj.speed, 7)

        self.inputs.speed = 14
        self.bridge.update_source_to_scene()  # t=1s — throttled; scene unchanged
        self.assertEqual(self.scene_obj.speed, 7)

    @patch("time.time", return_value=1.0)
    def test_skips_none_source_values(self, _):
        """Bindings whose source attribute does not exist (returns None) are skipped."""
        self.bridge.add_binding("inputs.missing_attr", "conveyor_1", "speed", BindingDirection.READ)
        self.bridge.start()
        self.bridge.update_source_to_scene()
        self.assertEqual(self.scene_obj.speed, 0)

    def test_set_and_get_read_throttle(self):
        self.bridge.set_read_throttle(250.0)
        self.assertEqual(self.bridge.get_read_throttle(), 250.0)


class _RealTickBridge(SceneBridge):
    """Bridge that does NOT override _register_tick_callback — exercises the real impl."""

    def create_default_bound_object(self):
        from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
        return SceneBoundLayer()


class TestTickCallbackRegistration(unittest.TestCase):
    """Tests for the real _register_tick_callback / _unregister_tick_callback logic.

    These tests use _RealTickBridge so the actual on_scene_updated list logic runs,
    not the instrumented mock.
    """

    def _make_bridge(self) -> tuple[_RealTickBridge, _DummyScene]:
        scene = _DummyScene()
        bridge = _RealTickBridge(scene=cast(IScene, scene))
        return bridge, scene

    def test_register_adds_callback_and_returns_true(self):
        bridge, scene = self._make_bridge()
        result = bridge._register_tick_callback(bridge._on_tick)
        self.assertTrue(result)
        self.assertIn(bridge._on_tick, scene.on_scene_updated)
        self.assertEqual(len(scene.on_scene_updated), 1)

    def test_register_duplicate_returns_false_no_duplicate_entry(self):
        bridge, scene = self._make_bridge()
        bridge._register_tick_callback(bridge._on_tick)
        result = bridge._register_tick_callback(bridge._on_tick)
        self.assertFalse(result)
        self.assertEqual(len(scene.on_scene_updated), 1)

    def test_register_without_scene_returns_false(self):
        bridge = _RealTickBridge(scene=None)
        result = bridge._register_tick_callback(bridge._on_tick)
        self.assertFalse(result)

    def test_unregister_removes_callback(self):
        bridge, scene = self._make_bridge()
        bridge._register_tick_callback(bridge._on_tick)
        bridge._unregister_tick_callback(bridge._on_tick)
        self.assertNotIn(bridge._on_tick, scene.on_scene_updated)

    def test_unregister_without_scene_is_safe(self):
        bridge = _RealTickBridge(scene=None)
        bridge._unregister_tick_callback(bridge._on_tick)  # must not raise

    def test_unregister_callback_not_present_is_safe(self):
        bridge, _ = self._make_bridge()
        bridge._unregister_tick_callback(bridge._on_tick)  # never registered — must not raise

    def test_start_sets_tick_callback_registered_true_and_adds_to_list(self):
        bridge, scene = self._make_bridge()
        bridge.start()
        self.assertTrue(bridge._tick_callback_registered)
        self.assertIn(bridge._on_tick, scene.on_scene_updated)

    def test_stop_sets_tick_callback_registered_false_and_removes_from_list(self):
        bridge, scene = self._make_bridge()
        bridge.start()
        bridge.stop()
        self.assertFalse(bridge._tick_callback_registered)
        self.assertNotIn(bridge._on_tick, scene.on_scene_updated)

    def test_start_stop_start_re_registers_callback(self):
        bridge, scene = self._make_bridge()
        bridge.start()
        bridge.stop()
        bridge.start()
        self.assertTrue(bridge._tick_callback_registered)
        self.assertIn(bridge._on_tick, scene.on_scene_updated)
        self.assertEqual(len(scene.on_scene_updated), 1)

    def test_only_one_entry_in_on_scene_updated_after_start(self):
        """start() must not add the callback more than once even if called via hooks."""
        bridge, scene = self._make_bridge()
        bridge.start()
        self.assertEqual(len(scene.on_scene_updated), 1)


if __name__ == "__main__":
    unittest.main()
