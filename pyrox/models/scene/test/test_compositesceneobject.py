"""Unit tests for CompositeSceneObject (Type 2 grouping)."""
import unittest
from unittest.mock import patch

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


def _make_obj(parent=None, name: str = "Child", x: float = 0.0, y: float = 0.0,
              width: float = 20.0, height: float = 20.0,
              parent_offset_x=0.0, parent_offset_y=0.0) -> SceneObject:
    return SceneObject(
        name=name,
        physics_body=_TestPhysicsBody(name=name, x=x, y=y, width=width, height=height),
        parent=parent,
        parent_offset_x=parent_offset_x, parent_offset_y=parent_offset_y,
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
        self.assertEqual(comp.scene_object_type, CompositeSceneObject._scene_object_type)

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
        self.comp.add_component("btn", child)
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
        child = _make_obj(parent_offset_x=15.0, parent_offset_y=25.0)
        self.comp.add_component("btn", child)
        components = self.comp.get_components()
        btn = components["btn"]
        self.assertAlmostEqual(btn._parent_offset_x, 15.0)
        self.assertAlmostEqual(btn._parent_offset_y, 25.0)


# ---------------------------------------------------------------------------
# World position
# ---------------------------------------------------------------------------

class TestCompositeWorldPosition(unittest.TestCase):

    def test_world_position_correct(self):
        comp = _make_composite(x=100, y=50)
        child = _make_obj(parent=comp, parent_offset_x=10, parent_offset_y=20)
        comp.add_component("btn", child)
        wx, wy = comp.get_component_world_position("btn")  # type: ignore
        self.assertAlmostEqual(wx, 110.0)
        self.assertAlmostEqual(wy, 70.0)

    def test_world_position_missing_returns_none(self):
        comp = _make_composite()
        self.assertIsNone(comp.get_component_world_position("nonexistent"))

    def test_world_position_zero_offset(self):
        comp = _make_composite(x=30, y=40)
        child = _make_obj(parent=comp, parent_offset_x=0.0, parent_offset_y=0.0)
        comp.add_component("btn", child)
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
        btn = _make_obj(comp, "btn", width=20, height=20, parent_offset_x=10, parent_offset_y=10)
        comp.add_component("btn", btn)

        # Click precisely on the button world area: x=10..30, y=10..30
        result = comp.get_component_at_point(20, 20)
        self.assertIs(result, btn)

    def test_hit_test_outside_all_components_returns_none(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        btn = _make_obj(comp, "btn", width=20, height=20, parent_offset_x=10, parent_offset_y=10)
        comp.add_component("btn", btn)

        # Well outside any component
        result = comp.get_component_at_point(190, 190)
        self.assertIsNone(result)

    def test_hit_test_prefers_higher_layer(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        bg = _make_obj("bg", width=100, height=100)
        fg = _make_obj("fg", width=100, height=100)
        bg.set_layer(0)
        fg.set_layer(10)
        comp.add_component("bg", bg)
        comp.add_component("fg", fg)
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
        btn = _make_obj(comp, "btn", width=20, height=20, parent_offset_x=10, parent_offset_y=10)
        btn.set_clickable(True)
        btn.add_on_click_handler(lambda obj, x, y: clicked.append(obj.name))
        comp.add_component("btn", btn)

        # Click within the button's world bounds (10..30, 10..30)
        comp.trigger_click(15, 15)
        self.assertIn("btn", clicked)

    def test_click_routes_to_composite_when_no_component_matches(self):
        comp = _make_composite(x=0, y=0, width=200, height=200)
        comp.set_clickable(True)

        clicked = []
        comp.add_on_click_handler(lambda obj, x, y: clicked.append("composite"))

        btn = _make_obj(comp, "btn", width=20, height=20, parent_offset_x=10, parent_offset_y=10)
        btn.set_clickable(True)
        comp.add_component("btn", btn)

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
            parent=comp,
            physics_body=_TestPhysicsBody(),
        )
        comp.add_component("tracker", child)
        comp.update(0.033)
        self.assertIn(0.033, updated_dts)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

class TestCompositeSerializtion(unittest.TestCase):

    def _make_populated(self):
        comp = _make_composite(name="Panel", x=50, y=50)
        btn_a = _make_obj(comp, "BtnA", parent_offset_x=5, parent_offset_y=10)
        btn_b = _make_obj(comp, "BtnB", parent_offset_x=5, parent_offset_y=40)
        comp.add_component("btn_a", btn_a)
        comp.add_component("btn_b", btn_b)
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
        self.assertAlmostEqual(names["btn_a"]['object']["parent_offset_x"], 5.0)
        self.assertAlmostEqual(names["btn_a"]['object']["parent_offset_y"], 10.0)

    def test_to_dict_component_embeds_object(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        names = {c["name"]: c for c in d["components"]}
        self.assertIn("object", names["btn_a"])

    def test_to_dict_scene_object_type(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        self.assertEqual(d["scene_object_type"], CompositeSceneObject._scene_object_type)

    def test_from_dict_roundtrip(self):
        comp, btn_a, btn_b = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)

        self.assertEqual(restored.name, "Panel")
        self.assertTrue(restored.has_component("btn_a"))
        self.assertTrue(restored.has_component("btn_b"))

    def test_id_preserved_through_serialization(self):
        comp, _, _ = self._make_populated()
        original_id = comp.id
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertEqual(restored.id, original_id)

    def test_from_dict_offsets_preserved(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        components = restored.get_components()
        btn = components["btn_a"]
        self.assertAlmostEqual(btn.parent_offset[0], 5.0)
        self.assertAlmostEqual(btn.parent_offset[1], 10.0)

    def test_from_dict_component_names_correct(self):
        comp, _, _ = self._make_populated()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertIn("btn_a", restored.get_component_names())
        self.assertIn("btn_b", restored.get_component_names())

    def test_scene_from_dict_loads_composite(self):
        """Full end-to-end: Scene.from_dict should recognise and restore a composite."""
        comp = _make_composite(name="MyPanel", x=0, y=0, width=100, height=100)
        comp.add_component("led", _make_obj("LED", parent_offset_x=10, parent_offset_y=10))
        scene = Scene()
        scene.add_scene_object(comp)
        d = scene.to_dict()

        restored_scene = Scene.from_dict(d)
        restored_comp = restored_scene.get_scene_object(comp.id)
        self.assertIsInstance(restored_comp, CompositeSceneObject)
        self.assertTrue(restored_comp.has_component("led"))  # type: ignore

    def test_from_dict_restores_tags(self):
        """Tags set on the composite survive a to_dict / from_dict round-trip."""
        comp = _make_composite()
        comp.set_tags(["machine", "active"])
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertEqual(sorted(restored.get_tags()), ["active", "machine"])

    def test_from_dict_restores_group_id(self):
        """group_id set on the composite survives a to_dict / from_dict round-trip."""
        comp = _make_composite()
        comp.set_group_id("group-abc123")
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertEqual(restored.get_group_id(), "group-abc123")

    def test_from_dict_group_id_none_when_absent(self):
        """group_id is None when not set."""
        comp = _make_composite()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertIsNone(restored.get_group_id())

    def test_from_dict_tags_empty_list_when_absent(self):
        """Tags default to an empty list when not set."""
        comp = _make_composite()
        d = comp.to_dict()
        restored = CompositeSceneObject.from_dict(d)
        self.assertEqual(restored.get_tags(), [])


# ---------------------------------------------------------------------------
# Rotation
# ---------------------------------------------------------------------------

class TestCompositeRotation(unittest.TestCase):
    """Tests for direction changes and the component rotation maths."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_rotatable_composite(self) -> CompositeSceneObject:
        """100×80 composite facing NORTH with one 20×10 component at (10, 20)."""
        comp = CompositeSceneObject(
            name="Panel",
            physics_body=_TestPhysicsBody(width=100.0, height=80.0),
        )
        btn = _make_obj("btn", width=20.0, height=10.0, parent_offset_x=10.0, parent_offset_y=20.0)
        comp.add_component("btn", btn)
        return comp

    # ------------------------------------------------------------------
    # Direction-change basics
    # ------------------------------------------------------------------

    def test_rotate_clockwise_changes_direction(self):
        from pyrox.interfaces import CardinalDirection
        comp = self._make_rotatable_composite()
        comp.rotate_clockwise()
        self.assertEqual(comp.direction, CardinalDirection.EAST)

    def test_rotate_counterclockwise_changes_direction(self):
        from pyrox.interfaces import CardinalDirection
        comp = self._make_rotatable_composite()
        comp.rotate_counterclockwise()
        self.assertEqual(comp.direction, CardinalDirection.WEST)

    def test_same_direction_is_noop(self):
        from pyrox.interfaces import CardinalDirection
        comp = self._make_rotatable_composite()
        # Set a second component so we can detect any unexpected mutation
        comp.add_component("fixed", _make_obj("fixed", width=5.0, height=5.0, parent_offset_x=50.0, parent_offset_y=50.0))
        comp.set_direction(CardinalDirection.NORTH)  # already NORTH
        self.assertEqual(comp.direction, CardinalDirection.NORTH)
        self.assertEqual(comp.width, 100.0)
        self.assertEqual(comp.height, 80.0)
        btn = comp.get_components()["btn"]
        self.assertAlmostEqual(btn._parent_offset_x, 10.0)
        self.assertAlmostEqual(btn._parent_offset_y, 20.0)

    def test_same_direction_string_is_noop(self):
        """String 'NORTH' must compare equal to the current CardinalDirection.NORTH."""
        comp = self._make_rotatable_composite()
        comp.set_direction("NORTH")
        self.assertEqual(comp.width, 100.0)
        self.assertEqual(comp.height, 80.0)
        comp = comp.get_components()["btn"]
        self.assertAlmostEqual(comp.parent_offset[0], 10.0)
        self.assertAlmostEqual(comp.parent_offset[1], 20.0)

    # ------------------------------------------------------------------
    # Composite dimension swaps
    # ------------------------------------------------------------------

    def test_cw_rotation_swaps_composite_dimensions(self):
        comp = self._make_rotatable_composite()
        comp.rotate_clockwise()  # NORTH → EAST (perpendicular)
        self.assertAlmostEqual(comp.width, 80.0)
        self.assertAlmostEqual(comp.height, 100.0)

    def test_ccw_rotation_swaps_composite_dimensions(self):
        comp = self._make_rotatable_composite()
        comp.rotate_counterclockwise()  # NORTH → WEST (perpendicular)
        self.assertAlmostEqual(comp.width, 80.0)
        self.assertAlmostEqual(comp.height, 100.0)

    # ------------------------------------------------------------------
    # Component offset rotation
    # ------------------------------------------------------------------

    def test_cw_rotation_rotates_component_offsets(self):
        """CW 90°: new_off_x = old_off_y, new_off_y = old_W - old_off_x - old_cw."""
        comp = self._make_rotatable_composite()
        comp.rotate_clockwise()
        obj = comp.get_components()["btn"]
        new_ox, new_oy = obj.parent_offset
        # old_off_y=20, old_W=100, old_off_x=10, old_cw=20  → (20, 70)
        self.assertAlmostEqual(new_ox, 20.0)
        self.assertAlmostEqual(new_oy, 70.0)

    def test_ccw_rotation_rotates_component_offsets(self):
        """CCW 90°: new_off_x = old_H - old_off_y - old_ch, new_off_y = old_off_x."""
        comp = self._make_rotatable_composite()
        comp.rotate_counterclockwise()
        btn = comp.get_components()["btn"]
        new_ox, new_oy = btn.parent_offset
        # old_H=80, old_off_y=20, old_ch=10  → new_off_x=50; new_off_y = old_off_x = 10
        self.assertAlmostEqual(new_ox, 50.0)
        self.assertAlmostEqual(new_oy, 10.0)

    # ------------------------------------------------------------------
    # Component dimension swaps
    # ------------------------------------------------------------------

    def test_cw_rotation_swaps_component_dimensions(self):
        comp = self._make_rotatable_composite()
        comp.rotate_clockwise()
        btn = comp.get_component("btn")
        # Original 20×10 → becomes 10×20
        self.assertAlmostEqual(btn.width, 10.0)
        self.assertAlmostEqual(btn.height, 20.0)

    def test_ccw_rotation_swaps_component_dimensions(self):
        comp = self._make_rotatable_composite()
        comp.rotate_counterclockwise()
        btn = comp.get_component("btn")
        # Original 20×10 → becomes 10×20
        self.assertAlmostEqual(btn.width, 10.0)
        self.assertAlmostEqual(btn.height, 20.0)

    # ------------------------------------------------------------------
    # Full-cycle tests (invariant: 4 × 90° CW restores everything)
    # ------------------------------------------------------------------

    def test_four_cw_rotations_restore_composite_dimensions(self):
        comp = self._make_rotatable_composite()
        for _ in range(4):
            comp.rotate_clockwise()
        self.assertAlmostEqual(comp.width, 100.0)
        self.assertAlmostEqual(comp.height, 80.0)

    def test_four_cw_rotations_restore_composite_direction(self):
        from pyrox.interfaces import CardinalDirection
        comp = self._make_rotatable_composite()
        for _ in range(4):
            comp.rotate_clockwise()
        self.assertEqual(comp.direction, CardinalDirection.NORTH)

    def test_four_cw_rotations_restore_component_offsets(self):
        """4 × CW must return the component to its original (10, 20) offset."""
        comp = self._make_rotatable_composite()
        for _ in range(4):
            comp.rotate_clockwise()
        btn = comp.get_components()["btn"]
        ox, oy = btn.parent_offset
        self.assertAlmostEqual(ox, 10.0)
        self.assertAlmostEqual(oy, 20.0)

    def test_four_cw_rotations_restore_component_dimensions(self):
        comp = self._make_rotatable_composite()
        for _ in range(4):
            comp.rotate_clockwise()
        btn = comp.get_component("btn")
        self.assertAlmostEqual(btn.width, 20.0)
        self.assertAlmostEqual(btn.height, 10.0)

    def test_four_ccw_rotations_restore_layout(self):
        comp = self._make_rotatable_composite()
        for _ in range(4):
            comp.rotate_counterclockwise()
        btn = comp.get_components()["btn"]
        ox, oy = btn.parent_offset
        self.assertAlmostEqual(comp.width, 100.0)
        self.assertAlmostEqual(comp.height, 80.0)
        self.assertAlmostEqual(ox, 10.0)
        self.assertAlmostEqual(oy, 20.0)

    # ------------------------------------------------------------------
    # Multiple components
    # ------------------------------------------------------------------

    def test_cw_rotation_applies_to_all_components(self):
        """Every registered component must have its offset and dimensions updated."""
        from pyrox.interfaces import CardinalDirection
        comp = CompositeSceneObject(
            name="Panel",
            physics_body=_TestPhysicsBody(width=100.0, height=80.0),
            direction=CardinalDirection.NORTH,
        )
        a = _make_obj("a", width=20.0, height=10.0, parent_offset_x=5.0, parent_offset_y=10.0)
        b = _make_obj("b", width=30.0, height=15.0, parent_offset_x=5.0, parent_offset_y=40.0)
        comp.add_component("a", a)
        comp.add_component("b", b)

        comp.rotate_clockwise()

        comps = comp.get_components()
        # Component "a": new_off_x=10, new_off_y=100-5-20=75
        ax, ay = comps["a"].parent_offset
        self.assertAlmostEqual(ax, 10.0)
        self.assertAlmostEqual(ay, 75.0)
        # Component "b": new_off_x=40, new_off_y=100-5-30=65
        bx, by = comps["b"].parent_offset
        self.assertAlmostEqual(bx, 40.0)
        self.assertAlmostEqual(by, 65.0)

    # ------------------------------------------------------------------
    # update() syncs world positions after rotation
    # ------------------------------------------------------------------

    def test_update_uses_rotated_offsets(self):
        """After a CW rotation, update() must position components using the new offsets."""
        comp = self._make_rotatable_composite()
        comp.x = 50.0
        comp.y = 50.0
        comp.rotate_clockwise()   # offsets become (20, 70)
        comp.update(0.1)  # should sync world positions based on new offsets

        btn = comp.get_component("btn")
        self.assertAlmostEqual(btn.x, 50.0 + 20.0)
        self.assertAlmostEqual(btn.y, 50.0 + 70.0)


if __name__ == "__main__":
    unittest.main()
