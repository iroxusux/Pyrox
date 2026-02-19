"""Unit tests for SceneBoundLayer."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
from pyrox.interfaces.scene.sceneboundlayer import ISceneBoundLayer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_layer(*names: str) -> SceneBoundLayer:
    """Return a layer pre-populated with SimpleNamespace sources."""
    layer = SceneBoundLayer()
    for name in names:
        layer.register_source(name, SimpleNamespace())
    return layer


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------

class TestISceneBoundLayerProtocol(unittest.TestCase):
    """Verify SceneBoundLayer satisfies the ISceneBoundLayer Protocol at runtime."""

    def test_isinstance_check(self):
        layer = SceneBoundLayer()
        self.assertIsInstance(layer, ISceneBoundLayer)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration(unittest.TestCase):
    def test_register_and_has_source(self):
        layer = SceneBoundLayer()
        src = SimpleNamespace(x=1)
        layer.register_source("ctrl", src)
        self.assertTrue(layer.has_source("ctrl"))

    def test_register_duplicate_raises(self):
        layer = _make_layer("ctrl")
        with self.assertRaises(KeyError):
            layer.register_source("ctrl", SimpleNamespace())

    def test_register_empty_name_raises(self):
        layer = SceneBoundLayer()
        with self.assertRaises(ValueError):
            layer.register_source("", SimpleNamespace())

    def test_register_invalid_identifier_raises(self):
        layer = SceneBoundLayer()
        with self.assertRaises(ValueError):
            layer.register_source("bad name", SimpleNamespace())

    def test_unregister_removes_source(self):
        layer = _make_layer("ctrl")
        layer.unregister_source("ctrl")
        self.assertFalse(layer.has_source("ctrl"))

    def test_unregister_missing_is_noop(self):
        layer = SceneBoundLayer()
        layer.unregister_source("does_not_exist")  # must not raise


# ---------------------------------------------------------------------------
# Access patterns
# ---------------------------------------------------------------------------

class TestSourceAccess(unittest.TestCase):
    def setUp(self):
        self.src = SimpleNamespace(speed=5.0, active=True)
        self.layer = SceneBoundLayer()
        self.layer.register_source("plc", self.src)

    def test_get_source_returns_object(self):
        self.assertIs(self.layer.get_source("plc"), self.src)

    def test_get_source_missing_returns_none(self):
        self.assertIsNone(self.layer.get_source("missing"))

    def test_getattr_routing(self):
        self.assertIs(self.layer.plc, self.src)

    def test_getattr_missing_raises_attribute_error(self):
        with self.assertRaises(AttributeError):
            _ = self.layer.missing

    def test_getitem_routing(self):
        self.assertIs(self.layer["plc"], self.src)

    def test_getitem_missing_raises_key_error(self):
        with self.assertRaises(KeyError):
            _ = self.layer["missing"]

    def test_setitem_replaces_source(self):
        new_src = SimpleNamespace(speed=99.0)
        self.layer["plc"] = new_src
        self.assertIs(self.layer.get_source("plc"), new_src)

    def test_list_sources(self):
        layer = _make_layer("a", "b", "c")
        self.assertEqual(layer.list_sources(), ["a", "b", "c"])

    def test_contains(self):
        self.assertIn("plc", self.layer)
        self.assertNotIn("missing", self.layer)

    def test_len(self):
        layer = _make_layer("a", "b")
        self.assertEqual(len(layer), 2)

    def test_iter_yields_names(self):
        layer = _make_layer("x", "y", "z")
        self.assertEqual(list(layer), ["x", "y", "z"])

    def test_repr(self):
        r = repr(self.layer)
        self.assertIn("plc", r)
        self.assertIn("SceneBoundLayer", r)


# ---------------------------------------------------------------------------
# Bridge integration — nested property traversal
# ---------------------------------------------------------------------------

class TestBridgePropertyTraversal(unittest.TestCase):
    """Verify that SceneBoundLayer works transparently with SceneBridge's
    _get_nested_value / _set_nested_value helpers."""

    def setUp(self):
        from pyrox.models.scene.scenebridge import SceneBridge

        class _BridgeUnderTest(SceneBridge):
            def create_default_bound_object(self):
                return {}

        self._bridge_class = _BridgeUnderTest

    def _get_nested(self, root, path: str):
        bridge = self._bridge_class()
        return bridge._get_nested_value(root, path)

    def _set_nested(self, root, path: str, value):
        bridge = self._bridge_class()
        bridge._set_nested_value(root, path, value)

    def test_read_one_level_via_getattr(self):
        layer = SceneBoundLayer()
        src = SimpleNamespace(speed=42.0)
        layer.register_source("plc", src)
        result = self._get_nested(layer, "plc.speed")
        self.assertEqual(result, 42.0)

    def test_read_two_levels_via_getattr(self):
        layer = SceneBoundLayer()
        inner = SimpleNamespace(active=True)
        src = SimpleNamespace(status=inner)
        layer.register_source("ctrl", src)
        result = self._get_nested(layer, "ctrl.status.active")
        self.assertTrue(result)

    def test_write_one_level_via_setattr(self):
        layer = SceneBoundLayer()
        src = SimpleNamespace(speed=0.0)
        layer.register_source("plc", src)
        self._set_nested(layer, "plc.speed", 99.0)
        self.assertEqual(src.speed, 99.0)

    def test_read_missing_source_returns_none(self):
        layer = SceneBoundLayer()
        result = self._get_nested(layer, "missing.speed")
        self.assertIsNone(result)

    def test_multiple_sources_coexist(self):
        layer = SceneBoundLayer()
        kb = SimpleNamespace(key_a=False)
        plc = SimpleNamespace(speed=5.0)
        layer.register_source("keyboard", kb)
        layer.register_source("plc", plc)

        self.assertFalse(self._get_nested(layer, "keyboard.key_a"))
        self.assertEqual(self._get_nested(layer, "plc.speed"), 5.0)


# ---------------------------------------------------------------------------
# Full end-to-end with SceneBridge
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Property introspection
# ---------------------------------------------------------------------------

class TestPropertyIntrospection(unittest.TestCase):
    """enumerate_source_properties and list_binding_keys."""

    def test_enumerate_namespace(self):
        layer = SceneBoundLayer()
        layer.register_source("plc", SimpleNamespace(speed=5.0, active=True))
        props = layer.enumerate_source_properties("plc")
        self.assertIn("speed", props)
        self.assertIn("active", props)

    def test_enumerate_dict_source(self):
        layer = SceneBoundLayer()
        layer.register_source("data", {"value": 1, "flag": True})
        props = layer.enumerate_source_properties("data")
        self.assertIn("value", props)
        self.assertIn("flag", props)

    def test_enumerate_excludes_private_and_callables(self):
        class _Src:
            x = 10
            _hidden = "no"
            def method(self): ...

        layer = SceneBoundLayer()
        layer.register_source("src", _Src())
        props = layer.enumerate_source_properties("src")
        self.assertIn("x", props)
        self.assertNotIn("_hidden", props)
        self.assertNotIn("method", props)

    def test_enumerate_missing_source_returns_empty(self):
        layer = SceneBoundLayer()
        self.assertEqual(layer.enumerate_source_properties("missing"), [])

    def test_list_binding_keys_flat(self):
        layer = SceneBoundLayer()
        layer.register_source("plc", SimpleNamespace(speed=0.0, active=False))
        layer.register_source("kb", SimpleNamespace(key_a=False))
        keys = layer.list_binding_keys()
        self.assertIn("plc.speed", keys)
        self.assertIn("plc.active", keys)
        self.assertIn("kb.key_a", keys)

    def test_list_binding_keys_sorted(self):
        layer = SceneBoundLayer()
        layer.register_source("z_src", SimpleNamespace(b=0, a=0))
        layer.register_source("a_src", SimpleNamespace(x=0))
        keys = layer.list_binding_keys()
        self.assertEqual(keys, sorted(keys))

    def test_list_binding_keys_empty_layer(self):
        layer = SceneBoundLayer()
        self.assertEqual(layer.list_binding_keys(), [])


# ---------------------------------------------------------------------------

class TestEndToEnd(unittest.TestCase):
    """Full round-trip: layer as bound_object, bridge reads from named source."""

    def setUp(self):
        from types import SimpleNamespace
        from unittest.mock import MagicMock
        from pyrox.models.scene.scenebridge import SceneBridge, BindingDirection

        class _Bridge(SceneBridge):
            def create_default_bound_object(self):
                return {}

        # Scene stub
        self.scene_obj = SimpleNamespace(speed=0.0)
        scene = MagicMock()
        scene.get_scene_object.return_value = self.scene_obj

        # Layer with one PLC source
        self.plc = SimpleNamespace(conveyor_speed=12.5)
        self.layer = SceneBoundLayer()
        self.layer.register_source("plc", self.plc)

        self.bridge = _Bridge(scene=scene, bound_object=self.layer)
        self.bridge.add_binding(
            binding_key="plc.conveyor_speed",
            object_id="belt_1",
            property_path="speed",
            direction=BindingDirection.READ,
        )

    def test_poll_source_to_scene_reads_from_layer(self):
        self.bridge.poll_source_to_scene()
        self.assertEqual(self.scene_obj.speed, 12.5)

    def test_swap_source_updates_subsequent_poll(self):
        new_plc = SimpleNamespace(conveyor_speed=99.0)
        self.layer.unregister_source("plc")
        self.layer.register_source("plc", new_plc)

        self.bridge.poll_source_to_scene()
        self.assertEqual(self.scene_obj.speed, 99.0)


if __name__ == "__main__":
    unittest.main()
