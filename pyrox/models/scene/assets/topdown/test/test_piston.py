"""Unit tests for PistonSceneObject.

Tests cover:
- Initialisation (class attributes, stored fields, default values)
- Component creation (rod and head geometry per direction)
- Parent-offset helpers (_rod_offset / _head_offset) for all four directions
- Animation clips (activate / deactivate)
- update() propagation (rod length, head position follows rod tip)
- Y-value stability regression — horizontal pistons must never drift in Y
- X-value stability regression — vertical pistons must never drift in X
- create() factory (body sizing, positioning per direction)
- from_dict() round-trip deserialisation
- compile_properties() serialisation completeness
- SceneObjectFactory template registration
"""
from __future__ import annotations

import unittest

from pyrox.interfaces import CardinalDirection, CollisionLayer
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.scene.assets.topdown.piston import (
    SCENE_OBJECT_TEMPLATE_NAME_PISTON,
    SCENE_OBJECT_TYPE_PISTON,
    PistonSceneObject,
)
from pyrox.models.scene.factory import SceneObjectFactory

# ---------------------------------------------------------------------------
# Default geometry constants used across tests
# ---------------------------------------------------------------------------

_RETRACTED = 20.0
_EXTENDED = 60.0
_ROD_THICK = 8.0
_HEAD_SIZE = 14.0
_PERP = (_HEAD_SIZE - _ROD_THICK) / 2.0  # 3.0


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_body(
    x: float = 0.0,
    y: float = 0.0,
    width: float = 74.0,
    height: float = 14.0,
) -> BasePhysicsBody:
    """Return a real BasePhysicsBody for the composite bounding box."""
    return BasePhysicsBody(
        name="piston_body",
        x=x,
        y=y,
        width=width,
        height=height,
        collision_layer=CollisionLayer.TRANSPARENT,
        collision_mask=[],
    )


def _make_piston(
    name: str = "piston",
    direction: CardinalDirection = CardinalDirection.RIGHT,
    retracted_length: float = _RETRACTED,
    extended_length: float = _EXTENDED,
    rod_thickness: float = _ROD_THICK,
    head_size: float = _HEAD_SIZE,
    animation_duration: float = 0.5,
    rod_color: str = "#888888",
    head_color: str = "#555555",
    layer: int = 0,
    body: BasePhysicsBody | None = None,
    x: float = 0.0,
    y: float = 0.0,
) -> PistonSceneObject:
    """Build a PistonSceneObject using the ``create`` factory."""
    return PistonSceneObject.create(
        name=name,
        x=x,
        y=y,
        direction=direction,
        retracted_length=retracted_length,
        extended_length=extended_length,
        rod_thickness=rod_thickness,
        head_size=head_size,
        animation_duration=animation_duration,
        rod_color=rod_color,
        head_color=head_color,
        layer=layer,
        body=body.to_dict() if body else None,
    )


# ===========================================================================
# PistonSceneObject – class-level attributes
# ===========================================================================


class TestPistonClassAttributes(unittest.TestCase):

    def test_scene_object_type_is_piston(self):
        self.assertEqual(PistonSceneObject._scene_object_type, SCENE_OBJECT_TYPE_PISTON)

    def test_template_name_is_piston(self):
        self.assertEqual(PistonSceneObject._template_name, SCENE_OBJECT_TEMPLATE_NAME_PISTON)

    def test_instance_scene_object_type(self):
        p = _make_piston()
        self.assertEqual(p.scene_object_type, SCENE_OBJECT_TYPE_PISTON)

    def test_instance_template_name(self):
        p = _make_piston()
        self.assertEqual(p._template_name, SCENE_OBJECT_TEMPLATE_NAME_PISTON)


# ===========================================================================
# PistonSceneObject – initialisation
# ===========================================================================


class TestPistonSceneObjectInit(unittest.TestCase):

    def test_name_stored(self):
        p = _make_piston(name="my_piston")
        self.assertEqual(p.name, "my_piston")

    def test_retracted_length_stored(self):
        p = _make_piston(retracted_length=15.0)
        self.assertAlmostEqual(p._retracted_length, 15.0)

    def test_extended_length_stored(self):
        p = _make_piston(extended_length=80.0)
        self.assertAlmostEqual(p._extended_length, 80.0)

    def test_rod_thickness_stored(self):
        p = _make_piston(rod_thickness=6.0)
        self.assertAlmostEqual(p._rod_thickness, 6.0)

    def test_head_size_stored(self):
        p = _make_piston(head_size=12.0)
        self.assertAlmostEqual(p._head_size, 12.0)

    def test_animation_duration_stored(self):
        p = _make_piston(animation_duration=1.5)
        self.assertAlmostEqual(p._animation_duration, 1.5)

    def test_rod_color_stored(self):
        p = _make_piston(rod_color="#aabbcc")
        self.assertEqual(p._rod_color, "#aabbcc")

    def test_head_color_stored(self):
        p = _make_piston(head_color="#112233")
        self.assertEqual(p._head_color, "#112233")

    def test_default_layer(self):
        p = _make_piston()
        self.assertEqual(p._layer, 0)

    def test_custom_layer(self):
        p = _make_piston(layer=5)
        self.assertEqual(p._layer, 5)

    def test_tracking_rod_length_starts_at_retracted(self):
        p = _make_piston(retracted_length=25.0)
        self.assertAlmostEqual(p._tracking_rod_length, 25.0)

    def test_active_starts_false(self):
        p = _make_piston()
        self.assertFalse(p.active)

    def test_prev_head_world_pos_starts_none(self):
        p = _make_piston()
        self.assertIsNone(p._prev_head_world_pos)

    def test_direction_right_stored(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        self.assertEqual(p.direction, CardinalDirection.RIGHT)

    def test_direction_left_stored(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        self.assertEqual(p.direction, CardinalDirection.LEFT)

    def test_direction_down_stored(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        self.assertEqual(p.direction, CardinalDirection.DOWN)

    def test_direction_up_stored(self):
        p = _make_piston(direction=CardinalDirection.UP)
        self.assertEqual(p.direction, CardinalDirection.UP)


# ===========================================================================
# PistonSceneObject – components present after init
# ===========================================================================


class TestPistonComponents(unittest.TestCase):

    def test_rod_component_exists(self):
        p = _make_piston()
        self.assertIsNotNone(p._rod)

    def test_head_component_exists(self):
        p = _make_piston()
        self.assertIsNotNone(p._head)

    def test_rod_registered_in_components(self):
        p = _make_piston()
        self.assertIn("rod", p._components)

    def test_head_registered_in_components(self):
        p = _make_piston()
        self.assertIn("head", p._components)

    def test_rod_is_same_object_as_component(self):
        p = _make_piston()
        self.assertIs(p._components["rod"], p._rod)

    def test_head_is_same_object_as_component(self):
        p = _make_piston()
        self.assertIs(p._components["head"], p._head)

    def test_rod_has_parent_set_to_piston(self):
        p = _make_piston()
        self.assertIs(p._rod._parent, p)

    def test_head_has_parent_set_to_piston(self):
        p = _make_piston()
        self.assertIs(p._head._parent, p)

    # HEAD – always square regardless of direction
    def test_head_width_equals_head_size(self):
        for d in (CardinalDirection.RIGHT, CardinalDirection.LEFT,
                  CardinalDirection.DOWN, CardinalDirection.UP):
            with self.subTest(direction=d):
                p = _make_piston(direction=d)
                self.assertAlmostEqual(p._head.width, _HEAD_SIZE)

    def test_head_height_equals_head_size(self):
        for d in (CardinalDirection.RIGHT, CardinalDirection.LEFT,
                  CardinalDirection.DOWN, CardinalDirection.UP):
            with self.subTest(direction=d):
                p = _make_piston(direction=d)
                self.assertAlmostEqual(p._head.height, _HEAD_SIZE)

    # ROD – horizontal: width=retracted, height=thickness
    def test_rod_dimensions_horizontal_right(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        self.assertAlmostEqual(p._rod.width, _RETRACTED)
        self.assertAlmostEqual(p._rod.height, _ROD_THICK)

    def test_rod_dimensions_horizontal_left(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        self.assertAlmostEqual(p._rod.width, _RETRACTED)
        self.assertAlmostEqual(p._rod.height, _ROD_THICK)

    # ROD – vertical: width=thickness, height=retracted
    def test_rod_dimensions_vertical_down(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        self.assertAlmostEqual(p._rod.width, _ROD_THICK)
        self.assertAlmostEqual(p._rod.height, _RETRACTED)

    def test_rod_dimensions_vertical_up(self):
        p = _make_piston(direction=CardinalDirection.UP)
        self.assertAlmostEqual(p._rod.width, _ROD_THICK)
        self.assertAlmostEqual(p._rod.height, _RETRACTED)

    def test_rod_color_applied(self):
        p = _make_piston(rod_color="#ff0000")
        self.assertEqual(p._rod.bg_color, "#ff0000")

    def test_head_color_applied(self):
        p = _make_piston(head_color="#00ff00")
        self.assertEqual(p._head.bg_color, "#00ff00")


# ===========================================================================
# Orientation helpers
# ===========================================================================


class TestPistonOrientationHelpers(unittest.TestCase):

    def test_is_horizontal_right(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        self.assertTrue(p.is_horizontal)

    def test_is_horizontal_left(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        self.assertTrue(p.is_horizontal)

    def test_is_horizontal_down_is_false(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        self.assertFalse(p.is_horizontal)

    def test_is_horizontal_up_is_false(self):
        p = _make_piston(direction=CardinalDirection.UP)
        self.assertFalse(p.is_horizontal)

    def test_is_vertical_down(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        self.assertTrue(p.is_vertical)

    def test_is_vertical_up(self):
        p = _make_piston(direction=CardinalDirection.UP)
        self.assertTrue(p.is_vertical)


# ===========================================================================
# Parent-offset helpers – all four directions
# ===========================================================================


class TestPistonOffsets(unittest.TestCase):
    """Verify _rod_offset and _head_offset return correct values for all
    four directions at both the retracted and extended lengths."""

    # ------------------------------------------------------------------
    # RIGHT
    # ------------------------------------------------------------------

    def test_rod_offset_right_retracted(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._rod_offset(_RETRACTED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _PERP)

    def test_rod_offset_right_extended(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._rod_offset(_EXTENDED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _PERP)  # X-axis perp offset is constant

    def test_head_offset_right_retracted(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._head_offset(_RETRACTED)
        self.assertAlmostEqual(ox, _RETRACTED)
        self.assertAlmostEqual(oy, 0.0)

    def test_head_offset_right_extended(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._head_offset(_EXTENDED)
        self.assertAlmostEqual(ox, _EXTENDED)
        self.assertAlmostEqual(oy, 0.0)

    # ------------------------------------------------------------------
    # LEFT
    # ------------------------------------------------------------------

    def test_rod_offset_left_retracted(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        ox, oy = p._rod_offset(_RETRACTED)
        expected_ox = _EXTENDED + _HEAD_SIZE - _RETRACTED  # 54.0
        self.assertAlmostEqual(ox, expected_ox)
        self.assertAlmostEqual(oy, _PERP)

    def test_rod_offset_left_extended(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        ox, oy = p._rod_offset(_EXTENDED)
        expected_ox = _EXTENDED + _HEAD_SIZE - _EXTENDED  # 14.0 = head_size
        self.assertAlmostEqual(ox, expected_ox)
        self.assertAlmostEqual(oy, _PERP)

    def test_head_offset_left_retracted(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        ox, oy = p._head_offset(_RETRACTED)
        self.assertAlmostEqual(ox, _EXTENDED - _RETRACTED)  # 40.0
        self.assertAlmostEqual(oy, 0.0)

    def test_head_offset_left_extended(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        ox, oy = p._head_offset(_EXTENDED)
        self.assertAlmostEqual(ox, 0.0)  # head at far-left edge
        self.assertAlmostEqual(oy, 0.0)

    # ------------------------------------------------------------------
    # DOWN
    # ------------------------------------------------------------------

    def test_rod_offset_down_retracted(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._rod_offset(_RETRACTED)
        self.assertAlmostEqual(ox, _PERP)
        self.assertAlmostEqual(oy, 0.0)

    def test_rod_offset_down_extended(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._rod_offset(_EXTENDED)
        self.assertAlmostEqual(ox, _PERP)  # Y-axis perp offset is constant
        self.assertAlmostEqual(oy, 0.0)

    def test_head_offset_down_retracted(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._head_offset(_RETRACTED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _RETRACTED)

    def test_head_offset_down_extended(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._head_offset(_EXTENDED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _EXTENDED)

    # ------------------------------------------------------------------
    # UP
    # ------------------------------------------------------------------

    def test_rod_offset_up_retracted(self):
        p = _make_piston(direction=CardinalDirection.UP)
        ox, oy = p._rod_offset(_RETRACTED)
        expected_oy = _EXTENDED + _HEAD_SIZE - _RETRACTED  # 54.0
        self.assertAlmostEqual(ox, _PERP)
        self.assertAlmostEqual(oy, expected_oy)

    def test_rod_offset_up_extended(self):
        p = _make_piston(direction=CardinalDirection.UP)
        ox, oy = p._rod_offset(_EXTENDED)
        expected_oy = _EXTENDED + _HEAD_SIZE - _EXTENDED  # 14.0 = head_size
        self.assertAlmostEqual(ox, _PERP)
        self.assertAlmostEqual(oy, expected_oy)

    def test_head_offset_up_retracted(self):
        p = _make_piston(direction=CardinalDirection.UP)
        ox, oy = p._head_offset(_RETRACTED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _EXTENDED - _RETRACTED)  # 40.0

    def test_head_offset_up_extended(self):
        p = _make_piston(direction=CardinalDirection.UP)
        ox, oy = p._head_offset(_EXTENDED)
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, 0.0)  # head at top edge when extended


# ===========================================================================
# Initial parent offsets stored on components at retracted position
# ===========================================================================


class TestPistonInitialParentOffsets(unittest.TestCase):

    def test_rod_initial_parent_offset_right(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._rod.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _PERP)

    def test_head_initial_parent_offset_right(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        ox, oy = p._head.parent_offset
        self.assertAlmostEqual(ox, _RETRACTED)
        self.assertAlmostEqual(oy, 0.0)

    def test_rod_initial_parent_offset_down(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._rod.parent_offset
        self.assertAlmostEqual(ox, _PERP)
        self.assertAlmostEqual(oy, 0.0)

    def test_head_initial_parent_offset_down(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        ox, oy = p._head.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _RETRACTED)


# ===========================================================================
# Animation clips
# ===========================================================================


class TestPistonAnimationClips(unittest.TestCase):

    def test_activate_clip_registered(self):
        p = _make_piston()
        clip = p.animator.get_clip(PistonSceneObject.CLIP_ACTIVATE)
        self.assertIsNotNone(clip)

    def test_deactivate_clip_registered(self):
        p = _make_piston()
        clip = p.animator.get_clip(PistonSceneObject.CLIP_DEACTIVATE)
        self.assertIsNotNone(clip)

    def test_activate_sets_active_true(self):
        p = _make_piston()
        p.activate()
        self.assertTrue(p.active)

    def test_deactivate_sets_active_false(self):
        p = _make_piston()
        p.activate()
        p.deactivate()
        self.assertFalse(p.active)

    def test_toggle_activates_when_inactive(self):
        p = _make_piston()
        p.toggle()
        self.assertTrue(p.active)

    def test_toggle_deactivates_when_active(self):
        p = _make_piston()
        p.activate()
        p.toggle()
        self.assertFalse(p.active)

    def test_activate_starts_clip_playing(self):
        p = _make_piston()
        p.activate()
        self.assertTrue(p.animator.is_playing)

    def test_current_animator_position_returns_rod_length(self):
        p = _make_piston(retracted_length=25.0)
        self.assertAlmostEqual(p.current_animator_position(), 25.0)


# ===========================================================================
# update() – rod length grows, head follows rod tip
# ===========================================================================


class TestPistonUpdate(unittest.TestCase):

    def test_update_without_animation_changes_nothing(self):
        p = _make_piston(x=0.0, y=0.0, direction=CardinalDirection.RIGHT)
        p.update(0.1)
        self.assertAlmostEqual(p._tracking_rod_length, _RETRACTED)

    def test_update_after_activate_grows_rod_length(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        p.activate()
        p.update(0.1)
        self.assertGreater(p._tracking_rod_length, _RETRACTED)

    def test_rod_width_matches_tracking_rod_length_horizontal(self):
        p = _make_piston(x=0.0, y=0.0, direction=CardinalDirection.RIGHT)
        p.activate()
        p.update(0.1)
        self.assertAlmostEqual(p._rod.width, p._tracking_rod_length)

    def test_rod_height_matches_tracking_rod_length_vertical(self):
        p = _make_piston(x=0.0, y=0.0, direction=CardinalDirection.DOWN)
        p.activate()
        p.update(0.1)
        self.assertAlmostEqual(p._rod.height, p._tracking_rod_length)

    def test_parent_offsets_updated_after_activation(self):
        """Parent offsets must change when the rod grows."""
        p = _make_piston(x=0.0, y=0.0, direction=CardinalDirection.RIGHT)
        _, oy_before = p._head.parent_offset
        p.activate()
        p.update(0.1)  # head's ox should now be > _RETRACTED
        ox_after, _ = p._head.parent_offset
        self.assertGreater(ox_after, _RETRACTED)

    def test_head_world_x_advances_as_rod_extends_right(self):
        p = _make_piston(x=100.0, y=50.0, direction=CardinalDirection.RIGHT)
        p.update(0.0)
        head_x_before = p._head.x
        p.activate()
        p.update(0.1)
        self.assertGreater(p._head.x, head_x_before)

    def test_head_world_y_advances_as_rod_extends_down(self):
        p = _make_piston(x=100.0, y=50.0, direction=CardinalDirection.DOWN)
        p.update(0.0)
        head_y_before = p._head.y
        p.activate()
        p.update(0.1)
        self.assertGreater(p._head.y, head_y_before)

    def test_prev_head_world_pos_recorded_after_first_update(self):
        p = _make_piston(x=0.0, y=0.0)
        p.update(0.1)
        self.assertIsNotNone(p._prev_head_world_pos)

    def test_multiple_updates_without_activity_idempotent(self):
        p = _make_piston(x=50.0, y=30.0, direction=CardinalDirection.RIGHT)
        for _ in range(10):
            p.update(0.05)
        self.assertAlmostEqual(p._tracking_rod_length, _RETRACTED)


# ===========================================================================
# Y-value stability – REGRESSION TEST
# Horizontal pistons must never drift in the Y axis during animation.
# ===========================================================================


class TestPistonYValueStability(unittest.TestCase):
    """Regression: when a piston fires horizontally (RIGHT/LEFT), neither the
    rod nor the head should ever change their Y world-coordinate."""

    DT = 0.05
    STEPS = 15  # enough to cover a full extend stroke

    def _run_and_collect_y(
        self,
        direction: CardinalDirection,
        x: float = 200.0,
        y: float = 150.0,
    ) -> tuple[list[float], list[float]]:
        p = _make_piston(x=x, y=y, direction=direction)
        p.update(self.DT)               # prime world position
        rod_ys, head_ys = [], []
        p.activate()
        for _ in range(self.STEPS):
            p.update(self.DT)
            rod_ys.append(p._rod.y)
            head_ys.append(p._head.y)
        return rod_ys, head_ys

    def test_rod_y_constant_during_right_activation(self):
        rod_ys, _ = self._run_and_collect_y(CardinalDirection.RIGHT, y=150.0)
        self.assertTrue(
            all(abs(v - rod_ys[0]) < 1e-9 for v in rod_ys),
            f"rod.y changed during RIGHT activation: {rod_ys}",
        )

    def test_head_y_constant_during_right_activation(self):
        _, head_ys = self._run_and_collect_y(CardinalDirection.RIGHT, y=150.0)
        self.assertTrue(
            all(abs(v - head_ys[0]) < 1e-9 for v in head_ys),
            f"head.y changed during RIGHT activation: {head_ys}",
        )

    def test_rod_y_constant_during_left_activation(self):
        rod_ys, _ = self._run_and_collect_y(CardinalDirection.LEFT, y=150.0)
        self.assertTrue(
            all(abs(v - rod_ys[0]) < 1e-9 for v in rod_ys),
            f"rod.y changed during LEFT activation: {rod_ys}",
        )

    def test_head_y_constant_during_left_activation(self):
        _, head_ys = self._run_and_collect_y(CardinalDirection.LEFT, y=150.0)
        self.assertTrue(
            all(abs(v - head_ys[0]) < 1e-9 for v in head_ys),
            f"head.y changed during LEFT activation: {head_ys}",
        )

    def test_rod_y_constant_during_right_deactivation(self):
        p = _make_piston(x=200.0, y=150.0, direction=CardinalDirection.RIGHT)
        p.activate()
        for _ in range(self.STEPS):
            p.update(self.DT)
        p.deactivate()
        rod_ys = []
        for _ in range(self.STEPS):
            p.update(self.DT)
            rod_ys.append(p._rod.y)
        self.assertTrue(
            all(abs(v - rod_ys[0]) < 1e-9 for v in rod_ys),
            f"rod.y changed during RIGHT deactivation: {rod_ys}",
        )


# ===========================================================================
# X-value stability – REGRESSION TEST
# Vertical pistons must never drift in the X axis during animation.
# ===========================================================================


class TestPistonXValueStability(unittest.TestCase):
    """Regression: when a piston fires vertically (DOWN/UP), neither the rod
    nor the head should ever change their X world-coordinate."""

    DT = 0.05
    STEPS = 15

    def _run_and_collect_x(
        self,
        direction: CardinalDirection,
        x: float = 100.0,
        y: float = 80.0,
    ) -> tuple[list[float], list[float]]:
        p = _make_piston(x=x, y=y, direction=direction)
        p.update(self.DT)
        rod_xs, head_xs = [], []
        p.activate()
        for _ in range(self.STEPS):
            p.update(self.DT)
            rod_xs.append(p._rod.x)
            head_xs.append(p._head.x)
        return rod_xs, head_xs

    def test_rod_x_constant_during_down_activation(self):
        rod_xs, _ = self._run_and_collect_x(CardinalDirection.DOWN, x=100.0)
        self.assertTrue(
            all(abs(v - rod_xs[0]) < 1e-9 for v in rod_xs),
            f"rod.x changed during DOWN activation: {rod_xs}",
        )

    def test_head_x_constant_during_down_activation(self):
        _, head_xs = self._run_and_collect_x(CardinalDirection.DOWN, x=100.0)
        self.assertTrue(
            all(abs(v - head_xs[0]) < 1e-9 for v in head_xs),
            f"head.x changed during DOWN activation: {head_xs}",
        )

    def test_rod_x_constant_during_up_activation(self):
        rod_xs, _ = self._run_and_collect_x(CardinalDirection.UP, x=100.0)
        self.assertTrue(
            all(abs(v - rod_xs[0]) < 1e-9 for v in rod_xs),
            f"rod.x changed during UP activation: {rod_xs}",
        )

    def test_head_x_constant_during_up_activation(self):
        _, head_xs = self._run_and_collect_x(CardinalDirection.UP, x=100.0)
        self.assertTrue(
            all(abs(v - head_xs[0]) < 1e-9 for v in head_xs),
            f"head.x changed during UP activation: {head_xs}",
        )


# ===========================================================================
# create() factory
# ===========================================================================


class TestPistonCreate(unittest.TestCase):

    def test_create_returns_piston_instance(self):
        p = PistonSceneObject.create(name="p")
        self.assertIsInstance(p, PistonSceneObject)

    def test_create_stores_name(self):
        p = PistonSceneObject.create(name="my_piston")
        self.assertEqual(p.name, "my_piston")

    def test_create_direction_right(self):
        p = PistonSceneObject.create(name="p", direction=CardinalDirection.RIGHT)
        self.assertEqual(p.direction, CardinalDirection.RIGHT)

    def test_create_direction_left(self):
        p = PistonSceneObject.create(name="p", direction=CardinalDirection.LEFT)
        self.assertEqual(p.direction, CardinalDirection.LEFT)

    def test_create_direction_down(self):
        p = PistonSceneObject.create(name="p", direction=CardinalDirection.DOWN)
        self.assertEqual(p.direction, CardinalDirection.DOWN)

    def test_create_direction_up(self):
        p = PistonSceneObject.create(name="p", direction=CardinalDirection.UP)
        self.assertEqual(p.direction, CardinalDirection.UP)

    def test_create_right_body_width(self):
        p = PistonSceneObject.create(
            name="p", direction=CardinalDirection.RIGHT,
            extended_length=60.0, head_size=14.0,
        )
        self.assertAlmostEqual(p.width, 60.0 + 14.0)

    def test_create_right_body_height(self):
        p = PistonSceneObject.create(
            name="p", direction=CardinalDirection.RIGHT, head_size=14.0,
        )
        self.assertAlmostEqual(p.height, 14.0)

    def test_create_down_body_width(self):
        p = PistonSceneObject.create(
            name="p", direction=CardinalDirection.DOWN, head_size=14.0,
        )
        self.assertAlmostEqual(p.width, 14.0)

    def test_create_down_body_height(self):
        p = PistonSceneObject.create(
            name="p", direction=CardinalDirection.DOWN,
            extended_length=60.0, head_size=14.0,
        )
        self.assertAlmostEqual(p.height, 60.0 + 14.0)

    def test_create_right_origin_at_x_y(self):
        p = PistonSceneObject.create(name="p", x=100.0, y=50.0, direction=CardinalDirection.RIGHT)
        self.assertAlmostEqual(p.x, 100.0)
        self.assertAlmostEqual(p.y, 50.0)

    def test_create_left_shifts_body_origin(self):
        """LEFT piston: body origin must be left of x so the mount point stays at x."""
        extended = 60.0
        head = 14.0
        p = PistonSceneObject.create(
            name="p", x=200.0, y=50.0,
            direction=CardinalDirection.LEFT,
            extended_length=extended, head_size=head,
        )
        self.assertAlmostEqual(p.x, 200.0 - (extended + head))

    def test_create_up_shifts_body_origin(self):
        """UP piston: body origin must be above y so the mount point stays at y."""
        extended = 60.0
        head = 14.0
        p = PistonSceneObject.create(
            name="p", x=50.0, y=200.0,
            direction=CardinalDirection.UP,
            extended_length=extended, head_size=head,
        )
        self.assertAlmostEqual(p.y, 200.0 - (extended + head))

    def test_create_retracted_and_extended_lengths_stored(self):
        p = PistonSceneObject.create(name="p", retracted_length=10.0, extended_length=50.0)
        self.assertAlmostEqual(p._retracted_length, 10.0)
        self.assertAlmostEqual(p._extended_length, 50.0)


# ===========================================================================
# extended_length property setter
# ===========================================================================


class TestPistonExtendedLengthSetter(unittest.TestCase):

    def test_setter_updates_extended_length(self):
        p = _make_piston()
        p.extended_length = 100.0
        self.assertAlmostEqual(p._extended_length, 100.0)

    def test_getter_returns_updated_value(self):
        p = _make_piston()
        p.extended_length = 80.0
        self.assertAlmostEqual(p.extended_length, 80.0)


# ===========================================================================
# compile_properties()
# ===========================================================================


class TestPistonCompileProperties(unittest.TestCase):

    def _compiled(self, **kwargs) -> dict:
        p = _make_piston(**kwargs)
        p.compile_properties()
        return p._properties

    def test_direction_in_properties(self):
        props = self._compiled(direction=CardinalDirection.RIGHT)
        self.assertIn("direction", props)

    def test_direction_value(self):
        props = self._compiled(direction=CardinalDirection.DOWN)
        self.assertEqual(props["direction"], "SOUTH")

    def test_retracted_length_in_properties(self):
        props = self._compiled(retracted_length=25.0)
        self.assertAlmostEqual(props["retracted_length"], 25.0)

    def test_extended_length_in_properties(self):
        props = self._compiled(extended_length=80.0)
        self.assertAlmostEqual(props["extended_length"], 80.0)

    def test_rod_thickness_in_properties(self):
        props = self._compiled(rod_thickness=6.0)
        self.assertAlmostEqual(props["rod_thickness"], 6.0)

    def test_head_size_in_properties(self):
        props = self._compiled(head_size=10.0)
        self.assertAlmostEqual(props["head_size"], 10.0)

    def test_animation_duration_in_properties(self):
        props = self._compiled(animation_duration=1.2)
        self.assertAlmostEqual(props["animation_duration"], 1.2)

    def test_rod_color_in_properties(self):
        props = self._compiled(rod_color="#aabb00")
        self.assertEqual(props["rod_color"], "#aabb00")

    def test_head_color_in_properties(self):
        props = self._compiled(head_color="#001122")
        self.assertEqual(props["head_color"], "#001122")

    def test_active_in_properties(self):
        props = self._compiled()
        self.assertIn("active", props)
        self.assertFalse(props["active"])

    def test_name_in_properties(self):
        props = self._compiled(name="clamp")
        self.assertEqual(props["name"], "clamp")


# ===========================================================================
# from_dict() round-trip
# ===========================================================================


class TestPistonFromDict(unittest.TestCase):

    def _roundtrip(self, **kwargs) -> PistonSceneObject:
        original = _make_piston(**kwargs)
        original.compile_properties()
        data = original.to_dict()
        return PistonSceneObject.from_dict(data)

    def test_roundtrip_name(self):
        p = self._roundtrip(name="pipe")
        self.assertEqual(p.name, "pipe")

    def test_roundtrip_direction_right(self):
        p = self._roundtrip(direction=CardinalDirection.RIGHT)
        self.assertEqual(p.direction, CardinalDirection.RIGHT)

    def test_roundtrip_direction_left(self):
        p = self._roundtrip(direction=CardinalDirection.LEFT)
        self.assertEqual(p.direction, CardinalDirection.LEFT)

    def test_roundtrip_direction_down(self):
        p = self._roundtrip(direction=CardinalDirection.DOWN)
        self.assertEqual(p.direction, CardinalDirection.DOWN)

    def test_roundtrip_direction_up(self):
        p = self._roundtrip(direction=CardinalDirection.UP)
        self.assertEqual(p.direction, CardinalDirection.UP)

    def test_roundtrip_retracted_length(self):
        p = self._roundtrip(retracted_length=15.0)
        self.assertAlmostEqual(p._retracted_length, 15.0)

    def test_roundtrip_extended_length(self):
        p = self._roundtrip(extended_length=90.0)
        self.assertAlmostEqual(p._extended_length, 90.0)

    def test_roundtrip_rod_thickness(self):
        p = self._roundtrip(rod_thickness=5.0)
        self.assertAlmostEqual(p._rod_thickness, 5.0)

    def test_roundtrip_head_size(self):
        p = self._roundtrip(head_size=16.0)
        self.assertAlmostEqual(p._head_size, 16.0)

    def test_roundtrip_animation_duration(self):
        p = self._roundtrip(animation_duration=2.0)
        self.assertAlmostEqual(p._animation_duration, 2.0)

    def test_roundtrip_rod_color(self):
        p = self._roundtrip(rod_color="#ff8800")
        self.assertEqual(p._rod_color, "#ff8800")

    def test_roundtrip_head_color(self):
        p = self._roundtrip(head_color="#0088ff")
        self.assertEqual(p._head_color, "#0088ff")

    def test_roundtrip_layer(self):
        p = self._roundtrip(layer=4)
        self.assertEqual(p._layer, 4)

    def test_from_dict_missing_body_raises(self):
        p = _make_piston()
        p.compile_properties()
        data = p.to_dict()
        data.pop("body", None)
        with self.assertRaises((ValueError, KeyError)):
            PistonSceneObject.from_dict(data)


# ===========================================================================
# SceneObjectFactory template
# ===========================================================================


class TestPistonFactoryTemplate(unittest.TestCase):

    def test_template_registered(self):
        tmpl = SceneObjectFactory.get_template(SCENE_OBJECT_TEMPLATE_NAME_PISTON)
        self.assertIsNotNone(tmpl)

    def test_template_class_is_piston(self):
        tmpl = SceneObjectFactory.get_template(SCENE_OBJECT_TEMPLATE_NAME_PISTON)
        self.assertIs(tmpl.scene_object_class, PistonSceneObject)

    def test_from_dict_produces_piston_instance(self):
        p = _make_piston(name="factory_test")
        p.compile_properties()
        restored = PistonSceneObject.from_dict(p.to_dict())
        self.assertIsInstance(restored, PistonSceneObject)


# ===========================================================================
# Rotation – component dimension stability
# REGRESSION: rotating the SceneObject must not distort rod or head sizes.
# The rod width inflates to _RETRACTED when it should stay at _ROD_THICK
# after a horizontal→vertical rotation.
# ===========================================================================


class TestPistonRotationDimensionStability(unittest.TestCase):
    """After any 90° rotation (CW or CCW) the component dimensions must
    reflect the *new* orientation, and must remain stable after a
    subsequent ``update()`` tick."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_rod_horizontal(self, p: PistonSceneObject, msg: str = "") -> None:
        """Rod must be wide (retracted length) × thin (rod thickness)."""
        self.assertAlmostEqual(p._rod.width, _RETRACTED, msg=f"rod.width {msg}")
        self.assertAlmostEqual(p._rod.height, _ROD_THICK, msg=f"rod.height {msg}")

    def _assert_rod_vertical(self, p: PistonSceneObject, msg: str = "") -> None:
        """Rod must be thin (rod thickness) × tall (retracted length)."""
        self.assertAlmostEqual(p._rod.width, _ROD_THICK, msg=f"rod.width {msg}")
        self.assertAlmostEqual(p._rod.height, _RETRACTED, msg=f"rod.height {msg}")

    def _assert_head_square(self, p: PistonSceneObject, msg: str = "") -> None:
        """Head is always a square with side == head_size."""
        self.assertAlmostEqual(p._head.width, _HEAD_SIZE, msg=f"head.width {msg}")
        self.assertAlmostEqual(p._head.height, _HEAD_SIZE, msg=f"head.height {msg}")

    # ------------------------------------------------------------------
    # Clockwise rotations – immediately after rotate_clockwise()
    # ------------------------------------------------------------------

    def test_cw_right_to_down_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        p.rotate_clockwise()
        self._assert_rod_vertical(p, "after CW RIGHT→DOWN")

    def test_cw_down_to_left_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        p.rotate_clockwise()
        self._assert_rod_horizontal(p, "after CW DOWN→LEFT")

    def test_cw_left_to_up_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        p.rotate_clockwise()
        self._assert_rod_vertical(p, "after CW LEFT→UP")

    def test_cw_up_to_right_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.UP)
        p.rotate_clockwise()
        self._assert_rod_horizontal(p, "after CW UP→RIGHT")

    # ------------------------------------------------------------------
    # Counter-clockwise rotations – immediately after rotate_counterclockwise()
    # ------------------------------------------------------------------

    def test_ccw_right_to_up_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        p.rotate_counterclockwise()
        self._assert_rod_vertical(p, "after CCW RIGHT→UP")

    def test_ccw_up_to_left_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.UP)
        p.rotate_counterclockwise()
        self._assert_rod_horizontal(p, "after CCW UP→LEFT")

    def test_ccw_left_to_down_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.LEFT)
        p.rotate_counterclockwise()
        self._assert_rod_vertical(p, "after CCW LEFT→DOWN")

    def test_ccw_down_to_right_rod_dimensions_immediate(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        p.rotate_counterclockwise()
        self._assert_rod_horizontal(p, "after CCW DOWN→RIGHT")

    # ------------------------------------------------------------------
    # Head remains square after all rotations
    # ------------------------------------------------------------------

    def test_cw_rotation_head_stays_square(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                p = _make_piston(direction=start)
                p.rotate_clockwise()
                self._assert_head_square(p, f"after CW from {start}")

    def test_ccw_rotation_head_stays_square(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                p = _make_piston(direction=start)
                p.rotate_counterclockwise()
                self._assert_head_square(p, f"after CCW from {start}")

    # ------------------------------------------------------------------
    # Dimensions remain correct AFTER update() is called post-rotation
    # (regression: rod.width inflating to _RETRACTED on the update tick)
    # ------------------------------------------------------------------

    def test_cw_right_to_down_rod_dimensions_after_update(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        p.rotate_clockwise()
        p.update(0.016)
        self._assert_rod_vertical(p, "after CW RIGHT→DOWN + update")

    def test_cw_down_to_left_rod_dimensions_after_update(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        p.rotate_clockwise()
        p.update(0.016)
        self._assert_rod_horizontal(p, "after CW DOWN→LEFT + update")

    def test_ccw_right_to_up_rod_dimensions_after_update(self):
        p = _make_piston(direction=CardinalDirection.RIGHT)
        p.rotate_counterclockwise()
        p.update(0.016)
        self._assert_rod_vertical(p, "after CCW RIGHT→UP + update")

    def test_ccw_down_to_right_rod_dimensions_after_update(self):
        p = _make_piston(direction=CardinalDirection.DOWN)
        p.rotate_counterclockwise()
        p.update(0.016)
        self._assert_rod_horizontal(p, "after CCW DOWN→RIGHT + update")

    def test_head_stays_square_after_rotation_and_update(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                p = _make_piston(direction=start)
                p.rotate_clockwise()
                p.update(0.016)
                self._assert_head_square(p, f"after CW from {start} + update")

    # ------------------------------------------------------------------
    # Full circle: four CW rotations return to original dimensions
    # ------------------------------------------------------------------

    def test_four_cw_rotations_restore_rod_dimensions(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                p = _make_piston(direction=start)
                w0, h0 = p._rod.width, p._rod.height
                for _ in range(4):
                    p.rotate_clockwise()
                p.update(0.016)
                self.assertAlmostEqual(p._rod.width, w0,
                                       msg=f"rod.width after 4×CW from {start}")
                self.assertAlmostEqual(p._rod.height, h0,
                                       msg=f"rod.height after 4×CW from {start}")

    def test_four_ccw_rotations_restore_rod_dimensions(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                p = _make_piston(direction=start)
                w0, h0 = p._rod.width, p._rod.height
                for _ in range(4):
                    p.rotate_counterclockwise()
                p.update(0.016)
                self.assertAlmostEqual(p._rod.width, w0,
                                       msg=f"rod.width after 4×CCW from {start}")
                self.assertAlmostEqual(p._rod.height, h0,
                                       msg=f"rod.height after 4×CCW from {start}")


if __name__ == "__main__":
    unittest.main()
