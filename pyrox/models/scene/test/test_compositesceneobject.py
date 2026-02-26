"""Unit tests for CompositeSceneObject (Type 2 grouping)."""
import unittest

from pyrox.interfaces import (
    BodyType,
    ColliderType,
    CollisionLayer,
)
from pyrox.models import (
    Scene,
    SceneObject,
    BasePhysicsBody,
)
from pyrox.models.scene.compositesceneobject import (
    CompositeSceneObject,
    SCENE_OBJECT_TYPE_COMPOSITE,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

class _TestPhysicsBody(BasePhysicsBody):
    """Minimal concrete physics body for testing."""

    def __init__(
        self,
        name: str = "TestBody",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 80.0,
    ):
        super().__init__(
            name=name,
            template_name="Base Physics Body",
            x=x,
            y=y,
            width=width,
            height=height,
            mass=1.0,
            body_type=BodyType.DYNAMIC,
            collider_type=ColliderType.RECTANGLE,
            collision_layer=CollisionLayer.DEFAULT,
        )


def _make_obj(name: str = "Child", x: float = 0.0, y: float = 0.0,
              width: float = 20.0, height: float = 20.0) -> SceneObject:
    return SceneObject(
        name=name,
        scene_object_type="test",
        physics_body=_TestPhysicsBody(name=name, x=x, y=y, width=width, height=height),
    )


def _make_composite(name: str = "Panel", x: float = 0.0, y: float = 0.0,
                    width: float = 100.0, height: float = 80.0) -> CompositeSceneObject:
    return CompositeSceneObject(
        name=name,
        physics_body=_TestPhysicsBody(name=name, x=x, y=y, width=width, height=height),
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestCompositeSceneObjectInit(unittest.TestCase):

    def test_default_scene_object_type(self):
        comp = _make_composite()
        self.assertEqual(comp.scene_object_type, SCENE_OBJECT_TYPE_COMPOSITE)

    def test_custom_scene_object_type(self):
        comp = CompositeSceneObject(
            name="Panel",
            physics_body=_TestPhysicsBody(),
            scene_object_type="panel",
        )
        self.assertEqual(comp.scene_object_type, "panel")

    def test_no_components_initially(self):
        comp = _make_composite()
        self.assertEqual(len(comp.get_components()), 0)

    def test_has_valid_id(self):
        comp = _make_composite()
        self.assertIsNotNone(comp.id)
        self.assertNotEqual(comp.id, "")


# ---------------------------------------------------------------------------
# add_component / get_component / remove_component
# ---------------------------------------------------------------------------

class TestCompositeComponentManagement(unittest.TestCase):

    def setUp(self):
        self.comp = _make_composite(x=50, y=50)

    def test_add_component(self):
        child = _make_obj("btn")
        self.comp.add_component("btn", child, offset_x=10, offset_y=20)
        self.assertIsNotNone(self.comp.get_component("btn"))

    def test_add_duplicate_name_raises(self):
        child = _make_obj("btn")
        self.comp.add_component("btn", child)
        with self.assertRaises(ValueError):
            self.comp.add_component("btn", _make_obj("btn2"))

    def test_get_component_returns_correct_object(self):
        child = _make_obj("btn")
        self.comp.add_component("btn", child)
        self.assertIs(self.comp.get_component("btn"), child)

    def test_get_component_missing_returns_none(self):
        self.assertIsNone(self.comp.get_component("nonexistent"))

    def test_remove_component(self):
        child = _make_obj("btn")
        self.comp.add_component("btn", child)
        self.comp.remove_component("btn")
        self.assertIsNone(self.comp.get_component("btn"))

    def test_remove_nonexistent_is_noop(self):
        # Should not raise
        self.comp.remove_component("missing")

    def test_has_component_true(self):
        self.comp.add_component("btn", _make_obj())
        self.assertTrue(self.comp.has_component("btn"))

    def test_has_component_false(self):
        self.assertFalse(self.comp.has_component("btn"))

    def test_get_component_names(self):
        self.comp.add_component("e_stop", _make_obj("e"))
        self.comp.add_component("run",    _make_obj("r"))
        names = self.comp.get_component_names()
        self.assertIn("e_stop", names)
        self.assertIn("run",    names)
        self.assertEqual(len(names), 2)

    def test_get_components_returns_copy(self):
        self.comp.add_component("btn", _make_obj())
        c = self.comp.get_components()
        c.clear()
        self.assertEqual(len(self.comp.get_components()), 1)

    def test_offsets_stored_correctly(self):
        child = _make_obj()
        self.comp.add_component("btn", child, offset_x=15.0, offset_y=25.0)
        components = self.comp.get_components()
        _, ox, oy = components["btn"]
        self.assertAlmostEqual(ox, 15.0)
        self.assertAlmostEqual(oy, 25.0)


# ---------------------------------------------------------------------------
# World position
# ---------------------------------------------------------------------------

class TestCompositeWorldPosition(unittest.TestCase):

    def test_world_position_correct(self):
        comp = _make_composite(x=100, y=50)
        child = _make_obj()
        comp.add_component("btn", child, offset_x=10, offset_y=20)
        wx, wy = comp.get_component_world_position("btn")  # type: ignore
        self.assertAlmostEqual(wx, 110.0)
        self.assertAlmostEqual(wy, 70.0)

    def test_world_position_missing_returns_none(self):
        comp = _make_composite()
        self.assertIsNone(comp.get_component_world_position("nonexistent"))

    def test_world_position_zero_offset(self):
        comp = _make_composite(x=30, y=40)
        child = _make_obj()
        comp.add_component("btn", child, offset_x=0, offset_y=0)
        wx, wy = comp.get_component_world_position("btn")  # type: ignore
        self.assertAlmostEqual(wx, 30.0)
        self.assertAlmostEqual(wy, 40.0)


# ---------------------------------------------------------------------------
# contains_point
# ---------------------------------------------------------------------------

class TestCompositeContainsPoint(unittest.TestCase):

    def test_point_in_composite_body(self):
        comp = _make_composite(x=0, y=0, width=100, height=80)
        # Point strictly inside the composite's own bounds
        self.assertTrue(comp.contains_point(50, 40))

    def test_point_outside_composite_and_components(self):
        comp = _make_composite(x=0, y=0, width=100, height=80)
        self.assertFalse(comp.contains_point(200, 200))


# ---------------------------------------------------------------------------
# get_component_at_point
# ---------------------------------------------------------------------------

class TestCompositeHitTest(unittest.TestCase):

    def test_hit_test_returns_correct_component(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        btn = _make_obj("btn", width=20, height=20)
        comp.add_component("btn", btn, offset_x=10, offset_y=10)

        # Click precisely on the button world area: x=10..30, y=10..30
        result = comp.get_component_at_point(20, 20)
        self.assertIs(result, btn)

    def test_hit_test_outside_all_components_returns_none(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        btn = _make_obj("btn", width=20, height=20)
        comp.add_component("btn", btn, offset_x=10, offset_y=10)

        # Well outside any component
        result = comp.get_component_at_point(190, 190)
        self.assertIsNone(result)

    def test_hit_test_prefers_higher_layer(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        bg = _make_obj("bg", width=100, height=100)
        fg = _make_obj("fg", width=100, height=100)
        bg.set_layer(0)
        fg.set_layer(10)
        comp.add_component("bg", bg, offset_x=0, offset_y=0)
        comp.add_component("fg", fg, offset_x=0, offset_y=0)
        # Both overlap at (50, 50); foreground should win
        result = comp.get_component_at_point(50, 50)
        self.assertIs(result, fg)


# ---------------------------------------------------------------------------
# trigger_click routing
# ---------------------------------------------------------------------------

class TestCompositeClickRouting(unittest.TestCase):

    def test_click_routes_to_matching_component(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        comp.set_clickable(True)

        clicked = []
        btn = _make_obj("btn", width=20, height=20)
        btn.set_clickable(True)
        btn.add_on_click_handler(lambda obj, x, y: clicked.append(obj.name))
        comp.add_component("btn", btn, offset_x=10, offset_y=10)

        # Click within the button's world bounds (10..30, 10..30)
        comp.trigger_click(15, 15)
        self.assertIn("btn", clicked)

    def test_click_routes_to_composite_when_no_component_matches(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        comp.set_clickable(True)

        clicked = []
        comp.add_on_click_handler(lambda obj, x, y: clicked.append("composite"))

        btn = _make_obj("btn", width=20, height=20)
        btn.set_clickable(True)
        comp.add_component("btn", btn, offset_x=10, offset_y=10)

        # Click far away from component
        comp.trigger_click(180, 180)
        self.assertIn("composite", clicked)


# ---------------------------------------------------------------------------
# update delegation
# ---------------------------------------------------------------------------

class TestCompositeUpdate(unittest.TestCase):

    def test_update_called_on_components(self):
        comp = _make_composite()
        updated_dts = []

        class TrackingObj(SceneObject):
            def update(self, dt: float) -> None:
                updated_dts.append(dt)

        child = TrackingObj(
            name="tracker",
            scene_object_type="test",
            physics_body=_TestPhysicsBody(),
        )
        comp.add_component("tracker", child, offset_x=0, offset_y=0)
        comp.update(0.033)
        self.assertIn(0.033, updated_dts)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestCompositeSerializtion(unittest.TestCase):

    def _make_populated(self):
        comp = _make_composite(name="Panel", x=50, y=50)
        btn_a = _make_obj("BtnA")
        btn_b = _make_obj("BtnB")
        comp.add_component("btn_a", btn_a, offset_x=5,  offset_y=10)
        comp.add_component("btn_b", btn_b, offset_x=5,  offset_y=40)
        return comp, btn_a, btn_b

    def test_to_dict_contains_components_key(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        self.assertIn("components", d)

    def test_to_dict_components_count(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        self.assertEqual(len(d["components"]), 2)

    def test_to_dict_component_has_offsets(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        names = {c["name"]: c for c in d["components"]}
        self.assertAlmostEqual(names["btn_a"]["offset_x"], 5.0)
        self.assertAlmostEqual(names["btn_a"]["offset_y"], 10.0)

    def test_to_dict_component_embeds_object(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        names = {c["name"]: c for c in d["components"]}
        self.assertIn("object", names["btn_a"])

    def test_to_dict_scene_object_type(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        self.assertEqual(d["scene_object_type"], SCENE_OBJECT_TYPE_COMPOSITE)

    def test_from_dict_roundtrip(self):
        comp, btn_a, btn_b = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)

        self.assertEqual(restored.name, "Panel")
        self.assertTrue(restored.has_component("btn_a"))
        self.assertTrue(restored.has_component("btn_b"))

    def test_from_dict_offsets_preserved(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        components = restored.get_components()
        _, ox, oy = components["btn_a"]
        self.assertAlmostEqual(ox, 5.0)
        self.assertAlmostEqual(oy, 10.0)

    def test_from_dict_component_names_correct(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertIn("btn_a", restored.get_component_names())
        self.assertIn("btn_b", restored.get_component_names())

    def test_scene_from_dict_loads_composite(self):
        """Full end-to-end: Scene.from_dict should recognise and restore a composite."""
        comp = _make_composite(name="MyPanel", x=0, y=0, width=100, height=100)
        comp.add_component("led", _make_obj("LED"), offset_x=10, offset_y=10)
        scene = Scene()
        scene.add_scene_object(comp)
        d = scene.to_dict()

        restored_scene = Scene.from_dict(d)
        restored_comp = restored_scene.get_scene_object(comp.id)
        self.assertIsInstance(restored_comp, CompositeSceneObject)
        self.assertTrue(restored_comp.has_component("led"))  # type: ignore


if __name__ == "__main__":
    unittest.main()
