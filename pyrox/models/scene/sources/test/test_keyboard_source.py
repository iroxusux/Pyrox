"""Unit tests for KeyboardSource."""
from __future__ import annotations

import unittest

from pyrox.models.scene.sources.keyboard import KeyboardSource, _DECLARED_KEYS
from pyrox.models.scene.sceneboundlayer import SceneBoundLayer


class TestKeyboardSourceDeclaredKeys(unittest.TestCase):
    """Declared keys appear as False bool instance attributes on construction."""

    def setUp(self):
        self.kb = KeyboardSource()

    def test_declared_keys_are_instance_attributes(self):
        for key in _DECLARED_KEYS:
            self.assertTrue(hasattr(self.kb, key), f"Missing attribute for key '{key}'")

    def test_declared_keys_are_false_by_default(self):
        for key in _DECLARED_KEYS:
            self.assertFalse(getattr(self.kb, key), f"Key '{key}' should default to False")

    def test_declared_keys_class_method(self):
        self.assertEqual(KeyboardSource.declared_keys(), _DECLARED_KEYS)


class TestKeyboardSourcePressRelease(unittest.TestCase):
    """press / release update the attribute and internal set."""

    def setUp(self):
        self.kb = KeyboardSource()

    def test_press_declared_key_sets_attribute_true(self):
        self.kb.press("w")
        self.assertTrue(getattr(self.kb, "w"))

    def test_release_declared_key_sets_attribute_false(self):
        self.kb.press("w")
        self.kb.release("w")
        self.assertFalse(getattr(self.kb, "w"))

    def test_is_pressed_declared(self):
        self.kb.press("space")
        self.assertTrue(self.kb.is_pressed("space"))
        self.kb.release("space")
        self.assertFalse(self.kb.is_pressed("space"))

    def test_is_pressed_undeclared_key(self):
        """Undeclared keys still tracked in internal set."""
        self.kb.press("F5")
        self.assertTrue(self.kb.is_pressed("F5"))
        self.assertFalse(hasattr(self.kb, "F5"), "Undeclared key should not create an attribute")

    def test_release_undeclared_noop_on_attribute(self):
        self.kb.press("F5")
        self.kb.release("F5")
        self.assertFalse(self.kb.is_pressed("F5"))

    def test_release_not_pressed_is_safe(self):
        """Releasing an un-pressed key must not raise."""
        self.kb.release("w")
        self.assertFalse(getattr(self.kb, "w"))

    def test_release_all_clears_all_held_keys(self):
        self.kb.press("w")
        self.kb.press("a")
        self.kb.press("F12")  # undeclared
        self.kb.release_all()
        self.assertFalse(getattr(self.kb, "w"))
        self.assertFalse(getattr(self.kb, "a"))
        self.assertFalse(self.kb.is_pressed("F12"))
        self.assertEqual(len(self.kb.currently_pressed()), 0)

    def test_currently_pressed_snapshot(self):
        self.kb.press("d")
        self.kb.press("shift_l")
        snap = self.kb.currently_pressed()
        self.assertIn("d", snap)
        self.assertIn("shift_l", snap)
        # Mutating the snapshot does not affect the source
        self.assertNotIn("x", self.kb.currently_pressed())

    def test_repr_shows_held_keys(self):
        self.kb.press("w")
        r = repr(self.kb)
        self.assertIn("w", r)
        self.assertIn("KeyboardSource", r)


class TestKeyboardSourceIntrospection(unittest.TestCase):
    """SceneBoundLayer can enumerate KeyboardSource properties."""

    def test_enumerate_finds_declared_keys(self):
        kb = KeyboardSource()
        layer = SceneBoundLayer()
        layer.register_source("keyboard", kb)

        props = layer.enumerate_source_properties("keyboard")
        for key in ["w", "a", "s", "d", "space"]:
            self.assertIn(key, props, f"'{key}' should appear in enumerated properties")

    def test_list_binding_keys_includes_keyboard_keys(self):
        kb = KeyboardSource()
        layer = SceneBoundLayer()
        layer.register_source("keyboard", kb)

        keys = layer.list_binding_keys()
        self.assertIn("keyboard.w", keys)
        self.assertIn("keyboard.space", keys)
        self.assertIn("keyboard.Up", keys)

    def test_live_value_visible_through_layer(self):
        """Bridge-style nested property read reflects press state."""
        from pyrox.models.scene.scenebridge import SceneBridge

        class _B(SceneBridge):
            def create_default_bound_object(self) -> SceneBoundLayer: return SceneBoundLayer()

        kb = KeyboardSource()
        layer = SceneBoundLayer()
        layer.register_source("keyboard", kb)
        bridge = _B(bound_object=layer)

        kb.press("w")
        val = bridge._get_nested_value(layer, "keyboard.w")
        self.assertTrue(val)

        kb.release("w")
        val = bridge._get_nested_value(layer, "keyboard.w")
        self.assertFalse(val)


class TestSceneBridgeServiceFactoryRegistry(unittest.TestCase):
    """SceneBridgeService.register_source_factory auto-populates the bound layer."""

    def setUp(self):
        from pyrox.services.scene import SceneBridgeService, SceneEventBus
        SceneBridgeService.reset()
        SceneEventBus.clear()
        self.service = SceneBridgeService

    def tearDown(self):
        from pyrox.services.scene import SceneBridgeService, SceneEventBus
        SceneBridgeService.reset()
        SceneEventBus.clear()

    def test_register_and_list_factory(self):
        self.service.initialize()
        self.service.register_source_factory("keyboard", KeyboardSource)
        self.assertIn("keyboard", self.service.list_source_factories())

    def test_duplicate_factory_raises(self):
        self.service.initialize()
        self.service.register_source_factory("keyboard", KeyboardSource)
        with self.assertRaises(KeyError):
            self.service.register_source_factory("keyboard", KeyboardSource)

    def test_unregister_factory(self):
        self.service.initialize()
        self.service.register_source_factory("keyboard", KeyboardSource)
        self.service.unregister_source_factory("keyboard")
        self.assertNotIn("keyboard", self.service.list_source_factories())

    def test_unregister_missing_is_noop(self):
        self.service.initialize()
        self.service.unregister_source_factory("nonexistent")  # must not raise

    def test_factory_populates_bound_layer_on_scene_load(self):
        from unittest.mock import MagicMock
        from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
        from pyrox.services.scene import SceneEventBus, SceneEvent, SceneEventType

        self.service.initialize()
        self.service.register_source_factory("keyboard", KeyboardSource)

        # Simulate a SCENE_LOADED event
        scene_mock = MagicMock()
        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_LOADED,
            scene=scene_mock,
        ))

        bridge = self.service.get_bridge()
        self.assertIsNotNone(bridge)
        assert bridge is not None
        bound = bridge.get_bound_object()
        self.assertIsInstance(bound, SceneBoundLayer)
        self.assertTrue(bound.has_source("keyboard"))
        self.assertIsInstance(bound.get_source("keyboard"), KeyboardSource)

    def test_factory_added_to_live_bridge(self):
        """Registering after a scene is loaded still adds source immediately."""
        from unittest.mock import MagicMock
        from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
        from pyrox.services.scene import SceneEventBus, SceneEvent, SceneEventType

        self.service.initialize()

        # Load scene first (no factories yet)
        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_LOADED,
            scene=MagicMock(),
        ))

        # Register factory after the scene is already loaded
        self.service.register_source_factory("keyboard", KeyboardSource)

        bridge = self.service.get_bridge()
        self.assertIsNotNone(bridge)
        assert bridge is not None
        bound = bridge.get_bound_object()
        self.assertIsInstance(bound, SceneBoundLayer)
        self.assertTrue(bound.has_source("keyboard"))


if __name__ == "__main__":
    unittest.main()
