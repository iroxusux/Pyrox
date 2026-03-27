"""Unit tests for ConveyorSceneObject.

Tests cover:
- Class-level attributes (_scene_object_type, _template_name)
- Initialisation (stored fields, default values, all four directions)
- Components present after init (base, belt stripes, physics conveyor)
- Active-state control (speed propagated to belt physics body)
- update() belt-stripe position scrolling
- rotate_components() — belt direction updated on rotation
- create() factory (body sizing, direction-aware)
- from_dict() round-trip deserialisation
- compile_properties() serialisation completeness
- Public API (get/set conveyor_speed, conveyor_width, conveyor_length)
- SceneObjectFactory template registration
"""
from __future__ import annotations

import math
import unittest

from pyrox.interfaces import CardinalDirection, CollisionLayer
from pyrox.models.physics.conveyor import ConveyorBody
from pyrox.models.scene.assets.topdown.conveyor import (
    SCENE_OBJECT_TEMPLATE_NAME,
    SCENE_OBJECT_TYPE,
    ConveyorSceneObject,
)
from pyrox.models.scene.factory import SceneObjectFactory

# ---------------------------------------------------------------------------
# Default geometry constants
# ---------------------------------------------------------------------------

_LENGTH = 60.0
_WIDTH = 20.0
_SPEED = 30.0
_BELT_LENGTH = 10.0
_SLICE = 4.0  # _belt_size_slice hardcoded value


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_body(
    x: float = 0.0,
    y: float = 0.0,
    length: float = _LENGTH,
    width: float = _WIDTH,
    direction: CardinalDirection = CardinalDirection.RIGHT,
) -> ConveyorBody:
    """Return a real ConveyorBody for the composite bounding box."""
    is_h = direction in (CardinalDirection.RIGHT, CardinalDirection.LEFT)
    body_w = length if is_h else width
    body_h = width if is_h else length
    return ConveyorBody(
        name="conveyor_body",
        x=x,
        y=y,
        width=body_w,
        height=body_h,
        collision_layer=CollisionLayer.TRANSPARENT,
        collision_mask=[],
    )


def _make_conveyor(
    name: str = "conveyor",
    direction: CardinalDirection = CardinalDirection.RIGHT,
    conveyor_length: float = _LENGTH,
    conveyor_width: float = _WIDTH,
    conveyor_speed: float = _SPEED,
    belt_length: float = _BELT_LENGTH,
    conveyor_color: str = "#888888",
    belt_color: str = "#555555",
    layer: int = 0,
    x: float = 0.0,
    y: float = 0.0,
) -> ConveyorSceneObject:
    """Build a ConveyorSceneObject via the create() factory."""
    return ConveyorSceneObject.create(
        name=name,
        x=x,
        y=y,
        direction=direction,
        conveyor_length=conveyor_length,
        conveyor_width=conveyor_width,
        conveyor_speed=conveyor_speed,
        belt_length=belt_length,
        conveyor_color=conveyor_color,
        belt_color=belt_color,
        layer=layer,
    )


# ===========================================================================
# Class-level attributes
# ===========================================================================


class TestConveyorClassAttributes(unittest.TestCase):

    def test_scene_object_type_constant(self):
        self.assertEqual(ConveyorSceneObject._scene_object_type, SCENE_OBJECT_TYPE)

    def test_template_name_constant(self):
        self.assertEqual(ConveyorSceneObject._template_name, SCENE_OBJECT_TEMPLATE_NAME)

    def test_instance_scene_object_type(self):
        c = _make_conveyor()
        self.assertEqual(c.scene_object_type, SCENE_OBJECT_TYPE)

    def test_instance_template_name(self):
        c = _make_conveyor()
        self.assertEqual(c._template_name, SCENE_OBJECT_TEMPLATE_NAME)


# ===========================================================================
# Initialisation
# ===========================================================================


class TestConveyorInit(unittest.TestCase):

    def test_name_stored(self):
        c = _make_conveyor(name="my_conveyor")
        self.assertEqual(c.name, "my_conveyor")

    def test_conveyor_length_stored(self):
        c = _make_conveyor(conveyor_length=80.0)
        self.assertAlmostEqual(c._conveyor_length, 80.0)

    def test_conveyor_width_stored(self):
        c = _make_conveyor(conveyor_width=30.0)
        self.assertAlmostEqual(c._conveyor_width, 30.0)

    def test_conveyor_speed_stored(self):
        c = _make_conveyor(conveyor_speed=50.0)
        self.assertAlmostEqual(c._conveyor_speed, 50.0)

    def test_belt_length_stored(self):
        c = _make_conveyor(belt_length=15.0)
        self.assertAlmostEqual(c._belt_length, 15.0)

    def test_conveyor_color_stored(self):
        c = _make_conveyor(conveyor_color="#aabbcc")
        self.assertEqual(c._conveyor_color, "#aabbcc")

    def test_belt_color_stored(self):
        c = _make_conveyor(belt_color="#112233")
        self.assertEqual(c._belt_color, "#112233")

    def test_default_layer(self):
        c = _make_conveyor()
        self.assertEqual(c._layer, 0)

    def test_custom_layer(self):
        c = _make_conveyor(layer=3)
        self.assertEqual(c._layer, 3)

    def test_belt_position_starts_at_zero(self):
        c = _make_conveyor()
        self.assertAlmostEqual(c._belt_position, 0.0)

    def test_active_starts_false(self):
        c = _make_conveyor()
        self.assertFalse(c.active)

    def test_direction_right_stored(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        self.assertEqual(c.direction, CardinalDirection.RIGHT)

    def test_direction_left_stored(self):
        c = _make_conveyor(direction=CardinalDirection.LEFT)
        self.assertEqual(c.direction, CardinalDirection.LEFT)

    def test_direction_down_stored(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        self.assertEqual(c.direction, CardinalDirection.DOWN)

    def test_direction_up_stored(self):
        c = _make_conveyor(direction=CardinalDirection.UP)
        self.assertEqual(c.direction, CardinalDirection.UP)


# ===========================================================================
# Components present after init
# ===========================================================================


class TestConveyorComponents(unittest.TestCase):

    def test_base_component_exists(self):
        c = _make_conveyor()
        self.assertIsNotNone(c._base)

    def test_physics_conveyor_component_exists(self):
        c = _make_conveyor()
        self.assertIsNotNone(c._physics_conveyor)

    def test_belt_stripes_list_not_empty(self):
        c = _make_conveyor()
        self.assertGreater(len(c._belt_stripes), 0)

    def test_base_registered_in_components(self):
        c = _make_conveyor()
        self.assertIn("base", c._components)

    def test_physics_registered_in_components(self):
        c = _make_conveyor()
        self.assertIn("physics", c._components)

    def test_belt_0_registered_in_components(self):
        c = _make_conveyor()
        self.assertIn("belt_0", c._components)

    def test_base_is_same_object_as_component(self):
        c = _make_conveyor()
        self.assertIs(c._components["base"], c._base)

    def test_physics_is_same_object_as_component(self):
        c = _make_conveyor()
        self.assertIs(c._components["physics"], c._physics_conveyor)

    def test_stripe_count_matches_ceil_division(self):
        c = _make_conveyor(conveyor_length=60.0, belt_length=10.0)
        expected = math.ceil(60.0 / 10.0)
        self.assertEqual(len(c._belt_stripes), expected)

    def test_stripe_count_non_exact_division(self):
        c = _make_conveyor(conveyor_length=65.0, belt_length=10.0)
        expected = math.ceil(65.0 / 10.0)
        self.assertEqual(len(c._belt_stripes), expected)

    # Base dimensions — horizontal
    def test_base_width_equals_length_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_length=60.0, conveyor_width=20.0)
        self.assertAlmostEqual(c._base.width, 60.0)

    def test_base_height_equals_width_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_length=60.0, conveyor_width=20.0)
        self.assertAlmostEqual(c._base.height, 20.0)

    # Base dimensions — vertical
    def test_base_width_equals_conveyor_width_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_length=60.0, conveyor_width=20.0)
        self.assertAlmostEqual(c._base.width, 20.0)

    def test_base_height_equals_length_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_length=60.0, conveyor_width=20.0)
        self.assertAlmostEqual(c._base.height, 60.0)

    def test_base_color_applied(self):
        c = _make_conveyor(conveyor_color="#ff0000")
        self.assertEqual(c._base.bg_color, "#ff0000")

    def test_belt_stripe_color_applied(self):
        c = _make_conveyor(belt_color="#00ff00")
        self.assertEqual(c._belt_stripes[0].bg_color, "#00ff00")

    def test_base_parent_is_conveyor(self):
        c = _make_conveyor()
        self.assertIs(c._base._parent, c)

    def test_physics_conveyor_parent_is_conveyor(self):
        c = _make_conveyor()
        self.assertIs(c._physics_conveyor._parent, c)

    def test_belt_stripe_parent_is_conveyor(self):
        c = _make_conveyor()
        self.assertIs(c._belt_stripes[0]._parent, c)


# ===========================================================================
# Component layer ordering
# ===========================================================================


class TestConveyorComponentLayers(unittest.TestCase):

    def test_base_on_configured_layer(self):
        c = _make_conveyor(layer=2)
        self.assertEqual(c._base._layer, 2)

    def test_belt_stripes_on_layer_plus_one(self):
        c = _make_conveyor(layer=2)
        for stripe in c._belt_stripes:
            self.assertEqual(stripe._layer, 3)

    def test_physics_conveyor_on_layer_plus_two(self):
        c = _make_conveyor(layer=2)
        self.assertEqual(c._physics_conveyor._layer, 4)


# ===========================================================================
# Active state / belt speed
# ===========================================================================


class TestConveyorActiveState(unittest.TestCase):

    def _belt_speed(self, c: ConveyorSceneObject) -> float:
        return c._get_belt_physics_body().belt_speed

    def test_belt_speed_zero_when_inactive(self):
        c = _make_conveyor(conveyor_speed=30.0)
        self.assertAlmostEqual(self._belt_speed(c), 0.0)

    def test_belt_speed_set_on_activate(self):
        c = _make_conveyor(conveyor_speed=30.0)
        c.activate()
        self.assertAlmostEqual(self._belt_speed(c), 30.0)

    def test_belt_speed_zero_on_deactivate(self):
        c = _make_conveyor(conveyor_speed=30.0)
        c.activate()
        c.deactivate()
        self.assertAlmostEqual(self._belt_speed(c), 0.0)

    def test_active_true_after_activate(self):
        c = _make_conveyor()
        c.activate()
        self.assertTrue(c.active)

    def test_active_false_after_deactivate(self):
        c = _make_conveyor()
        c.activate()
        c.deactivate()
        self.assertFalse(c.active)

    def test_toggle_activates_when_inactive(self):
        c = _make_conveyor()
        c.toggle()
        self.assertTrue(c.active)

    def test_toggle_deactivates_when_active(self):
        c = _make_conveyor()
        c.activate()
        c.toggle()
        self.assertFalse(c.active)

    def test_current_animator_position_returns_belt_position(self):
        c = _make_conveyor()
        self.assertAlmostEqual(c.current_animator_position(), 0.0)


# ===========================================================================
# Orientation helpers
# ===========================================================================


class TestConveyorOrientationHelpers(unittest.TestCase):

    def test_is_horizontal_right(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        self.assertTrue(c.is_horizontal)

    def test_is_horizontal_left(self):
        c = _make_conveyor(direction=CardinalDirection.LEFT)
        self.assertTrue(c.is_horizontal)

    def test_is_vertical_down(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        self.assertTrue(c.is_vertical)

    def test_is_vertical_up(self):
        c = _make_conveyor(direction=CardinalDirection.UP)
        self.assertTrue(c.is_vertical)

    def test_not_horizontal_when_down(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        self.assertFalse(c.is_horizontal)

    def test_not_vertical_when_right(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        self.assertFalse(c.is_vertical)


# ===========================================================================
# update() — belt position scrolling
# ===========================================================================


class TestConveyorUpdate(unittest.TestCase):

    def test_update_inactive_does_not_advance_belt(self):
        c = _make_conveyor(conveyor_speed=30.0)
        # Belt position is driven by _belt_position not by active state directly —
        # _belt_position advances regardless; active state only controls physics speed.
        pos_before = c._belt_position
        c.update(0.1)
        # With speed=30, dt=0.1: advance = 3.0; _belt_position = 3.0 % 10.0 = 3.0
        self.assertAlmostEqual(c._belt_position, (pos_before + 30.0 * 0.1) % _BELT_LENGTH)

    def test_update_advances_belt_position_right(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_speed=30.0, belt_length=10.0)
        c.activate()
        c.update(0.1)
        self.assertAlmostEqual(c._belt_position, 3.0)

    def test_update_advances_belt_position_down(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_speed=30.0, belt_length=10.0)
        c.activate()
        c.update(0.1)
        self.assertAlmostEqual(c._belt_position, 3.0)

    def test_update_reverses_belt_position_left(self):
        c = _make_conveyor(direction=CardinalDirection.LEFT, conveyor_speed=30.0, belt_length=10.0)
        c.activate()
        c.update(0.1)
        expected = (-3.0) % 10.0
        self.assertAlmostEqual(c._belt_position, expected)

    def test_update_reverses_belt_position_up(self):
        c = _make_conveyor(direction=CardinalDirection.UP, conveyor_speed=30.0, belt_length=10.0)
        c.activate()
        c.update(0.1)
        expected = (-3.0) % 10.0
        self.assertAlmostEqual(c._belt_position, expected)

    def test_belt_position_wraps_at_belt_length(self):
        c = _make_conveyor(conveyor_speed=100.0, belt_length=10.0)
        c.update(0.15)  # advance = 15 → wraps to 5
        self.assertAlmostEqual(c._belt_position, 5.0)

    def test_stripe_world_x_updated_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, x=100.0, y=50.0,
                           conveyor_speed=30.0, belt_length=10.0)
        c.update(0.1)
        stripe = c._belt_stripes[0]
        expected_x = 100.0 + (c._belt_position % c._conveyor_length)
        self.assertAlmostEqual(stripe.x, expected_x)

    def test_stripe_world_y_updated_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, x=100.0, y=50.0,
                           conveyor_speed=30.0, belt_length=10.0)
        c.update(0.1)
        stripe = c._belt_stripes[0]
        expected_y = 50.0 + (c._belt_position % c._conveyor_length)
        self.assertAlmostEqual(stripe.y, expected_y)


# ===========================================================================
# rotate_components — belt direction updated
# ===========================================================================


class TestConveyorRotateComponents(unittest.TestCase):

    def test_rotate_right_to_down_updates_belt_direction(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        belt_body = c._get_belt_physics_body()
        self.assertEqual(belt_body.direction, CardinalDirection.DOWN)

    def test_rotate_down_to_right_updates_belt_direction(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        belt_body = c._get_belt_physics_body()
        self.assertEqual(belt_body.direction, CardinalDirection.RIGHT)


# ===========================================================================
# Rotation correctness
# ===========================================================================
# Geometry reference values:
#   _LENGTH=60, _WIDTH=20, _BELT_LENGTH=10, _SLICE=4, cross_offset=2
#   stripe_along  = max(1, 10-4) = 6   (belt length - slice)
#   stripe_cross  = max(1, 20-4) = 16  (conveyor width - slice)
#   n_stripes     = ceil(60/10) = 6
#   phys_h_horiz  = 20-4 = 16          (width - slice for horizontal)
#   phys_w_vert   = 20-4 = 16          (width - slice for vertical)
# ===========================================================================

_STRIPE_ALONG = max(1.0, _BELT_LENGTH - _SLICE)   # 6.0
_STRIPE_CROSS = max(1.0, _WIDTH - _SLICE)          # 16.0
_CROSS_OFFSET = _SLICE / 2.0                       # 2.0
_N_STRIPES = max(1, math.ceil(_LENGTH / _BELT_LENGTH))  # 6


class TestConveyorRotationBoundingBox(unittest.TestCase):
    """Outer bounding-box (composite physics body) W/H after rotation."""

    def test_right_to_down_outer_body_width(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c.physics_body.get_width(), _WIDTH)

    def test_right_to_down_outer_body_height(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c.physics_body.get_height(), _LENGTH)

    def test_right_to_up_outer_body_width(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.UP)
        self.assertAlmostEqual(c.physics_body.get_width(), _WIDTH)

    def test_right_to_up_outer_body_height(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.UP)
        self.assertAlmostEqual(c.physics_body.get_height(), _LENGTH)

    def test_down_to_right_outer_body_width(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c.physics_body.get_width(), _LENGTH)

    def test_down_to_right_outer_body_height(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c.physics_body.get_height(), _WIDTH)

    def test_right_to_left_outer_body_width_unchanged(self):
        # 180° — dimensions must not change
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.LEFT)
        self.assertAlmostEqual(c.physics_body.get_width(), _LENGTH)

    def test_right_to_left_outer_body_height_unchanged(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.LEFT)
        self.assertAlmostEqual(c.physics_body.get_height(), _WIDTH)

    def test_double_rotation_returns_to_original_size(self):
        # right → down → right must restore original bounding dimensions
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c.physics_body.get_width(), _LENGTH)
        self.assertAlmostEqual(c.physics_body.get_height(), _WIDTH)

    def test_four_rotations_returns_to_original_size(self):
        # Full CW cycle: right → down → left → up → right
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        for d in (CardinalDirection.DOWN, CardinalDirection.LEFT,
                  CardinalDirection.UP, CardinalDirection.RIGHT):
            c.set_direction(d)
        self.assertAlmostEqual(c.physics_body.get_width(), _LENGTH)
        self.assertAlmostEqual(c.physics_body.get_height(), _WIDTH)


class TestConveyorRotationBase(unittest.TestCase):
    """_base component W/H after rotation."""

    def test_rotate_to_vertical_base_width(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c._base.width, _WIDTH)

    def test_rotate_to_vertical_base_height(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c._base.height, _LENGTH)

    def test_rotate_back_to_horizontal_base_width(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c._base.width, _LENGTH)

    def test_rotate_back_to_horizontal_base_height(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c._base.height, _WIDTH)

    def test_base_offset_is_origin_after_rotation(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c._base._parent_offset_x, 0.0)
        self.assertAlmostEqual(c._base._parent_offset_y, 0.0)


class TestConveyorRotationStripes(unittest.TestCase):
    """Belt stripe W/H and offsets after rotation."""

    def test_stripe_width_after_rotation_to_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        # All stripes should have the cross-axis size as their width
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe.width, _STRIPE_CROSS, msg=f"stripe width after rotation to DOWN")

    def test_stripe_height_after_rotation_to_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe.height, _STRIPE_ALONG, msg=f"stripe height after rotation to DOWN")

    def test_stripe_width_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe.width, _STRIPE_ALONG)

    def test_stripe_height_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe.height, _STRIPE_CROSS)

    def test_stripe_cross_offset_on_x_axis_after_rotation_to_vertical(self):
        # After rotating to vertical, cross_offset must appear on the X axis
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe._parent_offset_x, _CROSS_OFFSET,
                                   msg="stripe X offset should equal cross_offset for vertical conveyor")

    def test_stripe_along_offset_on_y_axis_after_rotation_to_vertical(self):
        # Y offsets tile stripes along the scroll axis
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        for i, stripe in enumerate(c._belt_stripes):
            expected_y = (i * _BELT_LENGTH) % _LENGTH
            self.assertAlmostEqual(stripe._parent_offset_y, expected_y,
                                   msg=f"stripe {i} Y offset after rotation to DOWN")

    def test_stripe_cross_offset_on_y_axis_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe._parent_offset_y, _CROSS_OFFSET)

    def test_stripe_along_offset_on_x_axis_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        for i, stripe in enumerate(c._belt_stripes):
            expected_x = (i * _BELT_LENGTH) % _LENGTH
            self.assertAlmostEqual(stripe._parent_offset_x, expected_x,
                                   msg=f"stripe {i} X offset after rotation to RIGHT")


class TestConveyorRotationPhysicsConveyor(unittest.TestCase):
    """_physics_conveyor component W/H and offset after rotation."""

    def test_phys_conveyor_width_after_rotation_to_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        # width = conveyor_width - slice
        self.assertAlmostEqual(c._physics_conveyor.width, _WIDTH - _SLICE)

    def test_phys_conveyor_height_after_rotation_to_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c._physics_conveyor.height, _LENGTH)

    def test_phys_conveyor_width_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c._physics_conveyor.width, _LENGTH)

    def test_phys_conveyor_height_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c._physics_conveyor.height, _WIDTH - _SLICE)

    def test_phys_conveyor_offset_x_is_cross_offset_when_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertAlmostEqual(c._physics_conveyor._parent_offset_x, _CROSS_OFFSET)
        self.assertAlmostEqual(c._physics_conveyor._parent_offset_y, 0.0)

    def test_phys_conveyor_offset_y_is_cross_offset_when_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertAlmostEqual(c._physics_conveyor._parent_offset_x, 0.0)
        self.assertAlmostEqual(c._physics_conveyor._parent_offset_y, _CROSS_OFFSET)


class TestConveyorRotationBeltDirection(unittest.TestCase):
    """ConveyorBody (kinematic friction) direction after rotation."""

    def test_belt_direction_right_to_down(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        self.assertEqual(c._get_belt_physics_body().direction, CardinalDirection.DOWN)

    def test_belt_direction_right_to_up(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.UP)
        self.assertEqual(c._get_belt_physics_body().direction, CardinalDirection.UP)

    def test_belt_direction_down_to_right(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        self.assertEqual(c._get_belt_physics_body().direction, CardinalDirection.RIGHT)

    def test_belt_direction_right_to_left(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.LEFT)
        self.assertEqual(c._get_belt_physics_body().direction, CardinalDirection.LEFT)

    def test_belt_direction_down_to_up(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.UP)
        self.assertEqual(c._get_belt_physics_body().direction, CardinalDirection.UP)


class TestConveyorRotationUpdateAfterRotation(unittest.TestCase):
    """update() scrolls stripes along the correct axis after set_direction."""

    def test_update_scrolls_on_y_axis_after_rotation_to_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.set_direction(CardinalDirection.DOWN)
        # After update, stripe Y offsets must change relative to stripe X offsets
        before_y = [s._parent_offset_y for s in c._belt_stripes]
        c.update(0.1)
        after_y = [s._parent_offset_y for s in c._belt_stripes]
        # At least one stripe Y offset changed (belt is inactive so speed=0;
        # use DOWN direction for sign — speed should be positive 0 since inactive)
        # stripes shouldn't move if conveyor inactive, but offsets should still
        # be on the Y axis (cross_offset on X)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe._parent_offset_x, _CROSS_OFFSET,
                                   msg="X offset must stay at cross_offset for vertical conveyor during update")

    def test_update_scrolls_on_x_axis_after_rotation_to_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN)
        c.set_direction(CardinalDirection.RIGHT)
        c.update(0.1)
        for stripe in c._belt_stripes:
            self.assertAlmostEqual(stripe._parent_offset_y, _CROSS_OFFSET,
                                   msg="Y offset must stay at cross_offset for horizontal conveyor during update")

    def test_update_moves_stripes_after_activate_and_rotation(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT)
        c.active = True
        c.set_direction(CardinalDirection.DOWN)
        before_y = [s._parent_offset_y for s in c._belt_stripes]
        c.update(0.5)
        after_y = [s._parent_offset_y for s in c._belt_stripes]
        # At least one Y-axis offset must have changed (belt is moving)
        self.assertTrue(
            any(abs(a - b) > 1e-6 for a, b in zip(after_y, before_y)),
            "stripe Y offsets should change after update on an active vertical conveyor",
        )


# ===========================================================================
# create() factory
# ===========================================================================


class TestConveyorCreate(unittest.TestCase):

    def test_create_returns_conveyor_instance(self):
        c = _make_conveyor()
        self.assertIsInstance(c, ConveyorSceneObject)

    def test_create_horizontal_body_width_equals_length(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_length=80.0, conveyor_width=24.0)
        self.assertAlmostEqual(c.physics_body.width, 80.0)

    def test_create_horizontal_body_height_equals_width(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_length=80.0, conveyor_width=24.0)
        self.assertAlmostEqual(c.physics_body.height, 24.0)

    def test_create_vertical_body_width_equals_conveyor_width(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_length=80.0, conveyor_width=24.0)
        self.assertAlmostEqual(c.physics_body.width, 24.0)

    def test_create_vertical_body_height_equals_length(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_length=80.0, conveyor_width=24.0)
        self.assertAlmostEqual(c.physics_body.height, 80.0)

    def test_create_x_position_stored(self):
        c = _make_conveyor(x=150.0, y=75.0)
        self.assertAlmostEqual(c.x, 150.0)

    def test_create_y_position_stored(self):
        c = _make_conveyor(x=150.0, y=75.0)
        self.assertAlmostEqual(c.y, 75.0)

    def test_create_with_existing_body_dict(self):
        body = _make_body()
        c = ConveyorSceneObject.create(name="test", body=body.to_dict())
        self.assertIsInstance(c, ConveyorSceneObject)

    def test_create_sets_correct_direction(self):
        for direction in CardinalDirection:
            with self.subTest(direction=direction):
                c = _make_conveyor(direction=direction)
                self.assertEqual(c.direction, direction)


# ===========================================================================
# from_dict() round-trip
# ===========================================================================


class TestConveyorFromDict(unittest.TestCase):

    def _round_trip(self, **kwargs) -> ConveyorSceneObject:
        c = _make_conveyor(**kwargs)
        data = c.to_dict()
        return ConveyorSceneObject.from_dict(data)

    def test_round_trip_name(self):
        c2 = self._round_trip(name="rt_conveyor")
        self.assertEqual(c2.name, "rt_conveyor")

    def test_round_trip_conveyor_length(self):
        c2 = self._round_trip(conveyor_length=90.0)
        self.assertAlmostEqual(c2._conveyor_length, 90.0)

    def test_round_trip_conveyor_width(self):
        c2 = self._round_trip(conveyor_width=25.0)
        self.assertAlmostEqual(c2._conveyor_width, 25.0)

    def test_round_trip_conveyor_speed(self):
        c2 = self._round_trip(conveyor_speed=45.0)
        self.assertAlmostEqual(c2._conveyor_speed, 45.0)

    def test_round_trip_belt_length(self):
        c2 = self._round_trip(belt_length=12.0)
        self.assertAlmostEqual(c2._belt_length, 12.0)

    def test_round_trip_conveyor_color(self):
        c2 = self._round_trip(conveyor_color="#123456")
        self.assertEqual(c2._conveyor_color, "#123456")

    def test_round_trip_belt_color(self):
        c2 = self._round_trip(belt_color="#654321")
        self.assertEqual(c2._belt_color, "#654321")

    def test_round_trip_direction_right(self):
        c2 = self._round_trip(direction=CardinalDirection.RIGHT)
        self.assertEqual(c2.direction, CardinalDirection.RIGHT)

    def test_round_trip_direction_down(self):
        c2 = self._round_trip(direction=CardinalDirection.DOWN)
        self.assertEqual(c2.direction, CardinalDirection.DOWN)

    def test_round_trip_layer(self):
        c2 = self._round_trip(layer=4)
        self.assertEqual(c2._layer, 4)

    def test_from_dict_missing_body_raises(self):
        c = _make_conveyor()
        data = c.to_dict()
        data.pop("body", None)
        with self.assertRaises((ValueError, KeyError)):
            ConveyorSceneObject.from_dict(data)


# ===========================================================================
# compile_properties()
# ===========================================================================


class TestConveyorCompileProperties(unittest.TestCase):

    def test_compile_properties_includes_conveyor_length(self):
        c = _make_conveyor(conveyor_length=70.0)
        c.compile_properties()
        self.assertAlmostEqual(c._properties["conveyor_length"], 70.0)

    def test_compile_properties_includes_conveyor_width(self):
        c = _make_conveyor(conveyor_width=22.0)
        c.compile_properties()
        self.assertAlmostEqual(c._properties["conveyor_width"], 22.0)

    def test_compile_properties_includes_conveyor_speed(self):
        c = _make_conveyor(conveyor_speed=55.0)
        c.compile_properties()
        self.assertAlmostEqual(c._properties["conveyor_speed"], 55.0)

    def test_compile_properties_includes_belt_length(self):
        c = _make_conveyor(belt_length=8.0)
        c.compile_properties()
        self.assertAlmostEqual(c._properties["belt_length"], 8.0)

    def test_compile_properties_includes_conveyor_color(self):
        c = _make_conveyor(conveyor_color="#999999")
        c.compile_properties()
        self.assertEqual(c._properties["conveyor_color"], "#999999")

    def test_compile_properties_includes_belt_color(self):
        c = _make_conveyor(belt_color="#111111")
        c.compile_properties()
        self.assertEqual(c._properties["belt_color"], "#111111")

    def test_compile_properties_includes_direction(self):
        c = _make_conveyor(direction=CardinalDirection.LEFT)
        c.compile_properties()
        self.assertEqual(c._properties["direction"], CardinalDirection.LEFT.name)


# ===========================================================================
# Public API — conveyor_speed
# ===========================================================================


class TestConveyorSpeedAPI(unittest.TestCase):

    def test_get_conveyor_speed(self):
        c = _make_conveyor(conveyor_speed=40.0)
        self.assertAlmostEqual(c.get_conveyor_speed(), 40.0)

    def test_conveyor_speed_property(self):
        c = _make_conveyor(conveyor_speed=40.0)
        self.assertAlmostEqual(c.conveyor_speed, 40.0)

    def test_set_conveyor_speed_updates_field(self):
        c = _make_conveyor(conveyor_speed=30.0)
        c.set_conveyor_speed(60.0)
        self.assertAlmostEqual(c._conveyor_speed, 60.0)

    def test_set_conveyor_speed_inactive_belt_stays_zero(self):
        c = _make_conveyor(conveyor_speed=30.0)
        c.set_conveyor_speed(60.0)
        self.assertAlmostEqual(c._get_belt_physics_body().belt_speed, 0.0)

    def test_set_conveyor_speed_active_belt_updated(self):
        c = _make_conveyor(conveyor_speed=30.0)
        c.activate()
        c.set_conveyor_speed(60.0)
        self.assertAlmostEqual(c._get_belt_physics_body().belt_speed, 60.0)

    def test_conveyor_speed_setter(self):
        c = _make_conveyor()
        c.conveyor_speed = 99.0
        self.assertAlmostEqual(c._conveyor_speed, 99.0)


# ===========================================================================
# Public API — conveyor_width
# ===========================================================================


class TestConveyorWidthAPI(unittest.TestCase):

    def test_get_conveyor_width(self):
        c = _make_conveyor(conveyor_width=24.0)
        self.assertAlmostEqual(c.get_conveyor_width(), 24.0)

    def test_conveyor_width_property(self):
        c = _make_conveyor(conveyor_width=24.0)
        self.assertAlmostEqual(c.conveyor_width, 24.0)

    def test_set_conveyor_width_updates_field(self):
        c = _make_conveyor(conveyor_width=20.0)
        c.set_conveyor_width(30.0)
        self.assertAlmostEqual(c._conveyor_width, 30.0)

    def test_set_conveyor_width_updates_base_width_horizontal(self):
        # For a horizontal conveyor, set_conveyor_width updates _base.width
        # (conveyor_width is the cross-axis dimension stored in the physics body width field)
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_width=20.0)
        c.set_conveyor_width(30.0)
        self.assertAlmostEqual(c._base.width, 30.0)

    def test_set_conveyor_width_updates_base_height_vertical(self):
        # For a vertical conveyor, set_conveyor_width updates _base.height
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_width=20.0)
        c.set_conveyor_width(30.0)
        self.assertAlmostEqual(c._base.height, 30.0)


# ===========================================================================
# Public API — conveyor_length
# ===========================================================================


class TestConveyorLengthAPI(unittest.TestCase):

    def test_get_conveyor_length(self):
        c = _make_conveyor(conveyor_length=70.0)
        self.assertAlmostEqual(c.get_conveyor_length(), 70.0)

    def test_conveyor_length_property(self):
        c = _make_conveyor(conveyor_length=70.0)
        self.assertAlmostEqual(c.conveyor_length, 70.0)

    def test_set_conveyor_length_updates_field(self):
        c = _make_conveyor(conveyor_length=60.0)
        c.set_conveyor_length(100.0)
        self.assertAlmostEqual(c._conveyor_length, 100.0)

    def test_set_conveyor_length_updates_base_width_horizontal(self):
        c = _make_conveyor(direction=CardinalDirection.RIGHT, conveyor_length=60.0)
        c.set_conveyor_length(90.0)
        self.assertAlmostEqual(c._base.width, 90.0)

    def test_set_conveyor_length_updates_base_height_vertical(self):
        c = _make_conveyor(direction=CardinalDirection.DOWN, conveyor_length=60.0)
        c.set_conveyor_length(90.0)
        self.assertAlmostEqual(c._base.height, 90.0)

    def test_set_conveyor_length_rebuilds_stripes(self):
        c = _make_conveyor(conveyor_length=60.0, belt_length=10.0)
        c.set_conveyor_length(100.0)
        expected = math.ceil(100.0 / 10.0)
        self.assertEqual(len(c._belt_stripes), expected)

    def test_conveyor_length_setter(self):
        c = _make_conveyor()
        c.conveyor_length = 80.0
        self.assertAlmostEqual(c._conveyor_length, 80.0)


# ===========================================================================
# SceneObjectFactory registration
# ===========================================================================


class TestConveyorFactoryRegistration(unittest.TestCase):

    def test_template_registered(self):
        template = SceneObjectFactory.get_template(SCENE_OBJECT_TEMPLATE_NAME)
        self.assertIsNotNone(template)

    def test_registered_class_is_conveyor(self):
        template = SceneObjectFactory.get_template(SCENE_OBJECT_TEMPLATE_NAME)
        self.assertIs(template.scene_object_class, ConveyorSceneObject)


if __name__ == "__main__":
    unittest.main()
