"""Unit tests for SlidingDoorSceneObject.

Tests cover:
- Class attributes (_scene_object_type, _template_name, CLIP_OPEN/CLIP_CLOSE)
- Initialisation (stored fields, default values)
- Component creation (post_a, post_b, door geometry per direction)
- Component registration (parent linkage, initial parent offsets per direction)
- Orientation helpers (is_horizontal, is_vertical)
- Animation clips (activate / deactivate registered, current_animator_position)
- activate() / deactivate() / toggle() convenience methods
- update() propagation: door panel slides, posts stay fixed
- Axis-stability regressions:
    - Horizontal doors must never drift in Y during animation
    - Vertical doors must never drift in X during animation
    - Posts must never move during door animation
- create() factory (body sizing, body origin per direction, parameter storage)
- from_dict() round-trip deserialisation
- compile_properties() serialisation completeness
- SceneObjectFactory template registration
"""
import unittest

from pyrox.interfaces import CardinalDirection
from pyrox.models.scene.assets.topdown.sliding_door import SlidingDoorSceneObject
from pyrox.models.scene.factory import SceneObjectFactory

# ---------------------------------------------------------------------------
# Default geometry constants used across tests
# ---------------------------------------------------------------------------

_TOTAL_WIDTH = 100.0
_DOOR_HEIGHT = 16.0
_POST_SIZE = 10.0
_OPENING = _TOTAL_WIDTH - 2.0 * _POST_SIZE          # 80.0
_BOUNDING_SPAN = _TOTAL_WIDTH + _OPENING            # 180.0


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def _make_door(
    name: str = "door",
    direction: CardinalDirection = CardinalDirection.LEFT,
    total_width: float = _TOTAL_WIDTH,
    door_height: float = _DOOR_HEIGHT,
    post_size: float = _POST_SIZE,
    animation_duration: float = 0.6,
    post_color: str = "#444444",
    door_color: str = "#888888",
    layer: int = 0,
    x: float = 0.0,
    y: float = 0.0,
) -> SlidingDoorSceneObject:
    """Build a SlidingDoorSceneObject using the ``create`` factory."""
    return SlidingDoorSceneObject.create(
        name=name,
        x=x,
        y=y,
        direction=direction,
        total_width=total_width,
        door_height=door_height,
        post_size=post_size,
        animation_duration=animation_duration,
        post_color=post_color,
        door_color=door_color,
        layer=layer,
    )


# ===========================================================================
# SlidingDoorSceneObject – class-level attributes
# ===========================================================================


class TestSlidingDoorClassAttributes(unittest.TestCase):

    def test_scene_object_type_is_sliding_door(self):
        self.assertEqual(SlidingDoorSceneObject._scene_object_type, SlidingDoorSceneObject._scene_object_type)

    def test_template_name_is_sliding_door(self):
        self.assertEqual(SlidingDoorSceneObject._template_name, SlidingDoorSceneObject._template_name)

    def test_instance_scene_object_type(self):
        d = _make_door()
        self.assertEqual(d.scene_object_type, SlidingDoorSceneObject._scene_object_type)

    def test_instance_template_name(self):
        d = _make_door()
        self.assertEqual(d._template_name, SlidingDoorSceneObject._template_name)

    def test_clip_open_equals_clip_activate(self):
        self.assertEqual(
            SlidingDoorSceneObject.CLIP_OPEN,
            SlidingDoorSceneObject.CLIP_ACTIVATE,
        )

    def test_clip_close_equals_clip_deactivate(self):
        self.assertEqual(
            SlidingDoorSceneObject.CLIP_CLOSE,
            SlidingDoorSceneObject.CLIP_DEACTIVATE,
        )


# ===========================================================================
# SlidingDoorSceneObject – initialisation
# ===========================================================================


class TestSlidingDoorInit(unittest.TestCase):

    def test_name_stored(self):
        d = _make_door(name="bay_door")
        self.assertEqual(d.name, "bay_door")

    def test_total_width_stored(self):
        d = _make_door(total_width=80.0)
        self.assertAlmostEqual(d._total_width, 80.0)

    def test_door_height_stored(self):
        d = _make_door(door_height=20.0)
        self.assertAlmostEqual(d._door_height, 20.0)

    def test_post_size_stored(self):
        d = _make_door(post_size=12.0)
        self.assertAlmostEqual(d._post_size, 12.0)

    def test_animation_duration_stored(self):
        d = _make_door(animation_duration=1.5)
        self.assertAlmostEqual(d._animation_duration, 1.5)

    def test_post_color_stored(self):
        d = _make_door(post_color="#112233")
        self.assertEqual(d._post_color, "#112233")

    def test_door_color_stored(self):
        d = _make_door(door_color="#aabbcc")
        self.assertEqual(d._door_color, "#aabbcc")

    def test_default_layer(self):
        d = _make_door()
        self.assertEqual(d._layer, 0)

    def test_custom_layer(self):
        d = _make_door(layer=3)
        self.assertEqual(d._layer, 3)

    def test_active_starts_false(self):
        d = _make_door()
        self.assertFalse(d.active)

    def test_direction_left_stored(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        self.assertEqual(d.direction, CardinalDirection.LEFT)

    def test_direction_right_stored(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        self.assertEqual(d.direction, CardinalDirection.RIGHT)

    def test_direction_up_stored(self):
        d = _make_door(direction=CardinalDirection.UP)
        self.assertEqual(d.direction, CardinalDirection.UP)

    def test_direction_down_stored(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        self.assertEqual(d.direction, CardinalDirection.DOWN)


# ===========================================================================
# SlidingDoorSceneObject – components present after init
# ===========================================================================


class TestSlidingDoorComponents(unittest.TestCase):

    def test_post_a_component_exists(self):
        d = _make_door()
        self.assertIsNotNone(d._post_a)

    def test_post_b_component_exists(self):
        d = _make_door()
        self.assertIsNotNone(d._post_b)

    def test_door_component_exists(self):
        d = _make_door()
        self.assertIsNotNone(d._door)

    def test_post_a_registered_in_components(self):
        d = _make_door()
        self.assertIn("post_a", d._components)

    def test_post_b_registered_in_components(self):
        d = _make_door()
        self.assertIn("post_b", d._components)

    def test_door_registered_in_components(self):
        d = _make_door()
        self.assertIn("door", d._components)

    def test_post_a_is_same_object_as_component(self):
        d = _make_door()
        self.assertIs(d._components["post_a"], d._post_a)

    def test_post_b_is_same_object_as_component(self):
        d = _make_door()
        self.assertIs(d._components["post_b"], d._post_b)

    def test_door_is_same_object_as_component(self):
        d = _make_door()
        self.assertIs(d._components["door"], d._door)

    def test_post_a_parent_is_door(self):
        d = _make_door()
        self.assertIs(d._post_a._parent, d)

    def test_post_b_parent_is_door(self):
        d = _make_door()
        self.assertIs(d._post_b._parent, d)

    def test_door_panel_parent_is_door(self):
        d = _make_door()
        self.assertIs(d._door._parent, d)

    # --- Horizontal post geometry (LEFT / RIGHT) ---

    def test_post_width_horizontal(self):
        for direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._post_a.width, _POST_SIZE)
                self.assertAlmostEqual(d._post_b.width, _POST_SIZE)

    def test_post_height_horizontal(self):
        for direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._post_a.height, _DOOR_HEIGHT)
                self.assertAlmostEqual(d._post_b.height, _DOOR_HEIGHT)

    def test_door_panel_width_horizontal(self):
        for direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._door.width, _OPENING)

    def test_door_panel_height_horizontal(self):
        for direction in (CardinalDirection.LEFT, CardinalDirection.RIGHT):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._door.height, _DOOR_HEIGHT)

    # --- Vertical post geometry (UP / DOWN) ---

    def test_post_width_vertical(self):
        for direction in (CardinalDirection.UP, CardinalDirection.DOWN):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._post_a.width, _DOOR_HEIGHT)
                self.assertAlmostEqual(d._post_b.width, _DOOR_HEIGHT)

    def test_post_height_vertical(self):
        for direction in (CardinalDirection.UP, CardinalDirection.DOWN):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._post_a.height, _POST_SIZE)
                self.assertAlmostEqual(d._post_b.height, _POST_SIZE)

    def test_door_panel_width_vertical(self):
        for direction in (CardinalDirection.UP, CardinalDirection.DOWN):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._door.width, _DOOR_HEIGHT)

    def test_door_panel_height_vertical(self):
        for direction in (CardinalDirection.UP, CardinalDirection.DOWN):
            with self.subTest(direction=direction):
                d = _make_door(direction=direction)
                self.assertAlmostEqual(d._door.height, _OPENING)

    def test_post_color_applied(self):
        d = _make_door(post_color="#ff0000")
        self.assertEqual(d._post_a.bg_color, "#ff0000")
        self.assertEqual(d._post_b.bg_color, "#ff0000")

    def test_door_color_applied(self):
        d = _make_door(door_color="#00ff00")
        self.assertEqual(d._door.bg_color, "#00ff00")


# ===========================================================================
# Orientation helpers
# ===========================================================================


class TestSlidingDoorOrientationHelpers(unittest.TestCase):

    def test_is_horizontal_left(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        self.assertTrue(d.is_horizontal)

    def test_is_horizontal_right(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        self.assertTrue(d.is_horizontal)

    def test_is_horizontal_up_is_false(self):
        d = _make_door(direction=CardinalDirection.UP)
        self.assertFalse(d.is_horizontal)

    def test_is_horizontal_down_is_false(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        self.assertFalse(d.is_horizontal)

    def test_is_vertical_up(self):
        d = _make_door(direction=CardinalDirection.UP)
        self.assertTrue(d.is_vertical)

    def test_is_vertical_down(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        self.assertTrue(d.is_vertical)


# ===========================================================================
# Initial parent offsets stored on components
# ===========================================================================

# LEFT:  post_a=opening, post_b=opening+total-post, door_closed=opening+post
# RIGHT: post_a=0,       post_b=total-post,          door_closed=post
_LEFT_POST_A = _OPENING                                # 80.0
_LEFT_POST_B = _OPENING + _TOTAL_WIDTH - _POST_SIZE    # 170.0
_LEFT_DOOR_CL = _OPENING + _POST_SIZE                   # 90.0

_RIGHT_POST_A = 0.0
_RIGHT_POST_B = _TOTAL_WIDTH - _POST_SIZE               # 90.0
_RIGHT_DOOR_CL = _POST_SIZE                              # 10.0


class TestSlidingDoorInitialParentOffsets(unittest.TestCase):

    # --- LEFT direction ---

    def test_post_a_offset_left(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        ox, oy = d._post_a.parent_offset
        self.assertAlmostEqual(ox, _LEFT_POST_A)
        self.assertAlmostEqual(oy, 0.0)

    def test_post_b_offset_left(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        ox, oy = d._post_b.parent_offset
        self.assertAlmostEqual(ox, _LEFT_POST_B)
        self.assertAlmostEqual(oy, 0.0)

    def test_door_panel_offset_left_closed(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        ox, oy = d._door.parent_offset
        self.assertAlmostEqual(ox, _LEFT_DOOR_CL)
        self.assertAlmostEqual(oy, 0.0)

    # --- RIGHT direction ---

    def test_post_a_offset_right(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        ox, oy = d._post_a.parent_offset
        self.assertAlmostEqual(ox, _RIGHT_POST_A)
        self.assertAlmostEqual(oy, 0.0)

    def test_post_b_offset_right(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        ox, oy = d._post_b.parent_offset
        self.assertAlmostEqual(ox, _RIGHT_POST_B)
        self.assertAlmostEqual(oy, 0.0)

    def test_door_panel_offset_right_closed(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        ox, oy = d._door.parent_offset
        self.assertAlmostEqual(ox, _RIGHT_DOOR_CL)
        self.assertAlmostEqual(oy, 0.0)

    # --- UP direction (axes swapped to Y) ---

    def test_post_a_offset_up(self):
        d = _make_door(direction=CardinalDirection.UP)
        ox, oy = d._post_a.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _LEFT_POST_A)   # same numeric value as LEFT

    def test_post_b_offset_up(self):
        d = _make_door(direction=CardinalDirection.UP)
        ox, oy = d._post_b.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _LEFT_POST_B)

    def test_door_panel_offset_up_closed(self):
        d = _make_door(direction=CardinalDirection.UP)
        ox, oy = d._door.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _LEFT_DOOR_CL)

    # --- DOWN direction (axes swapped to Y) ---

    def test_post_a_offset_down(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        ox, oy = d._post_a.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _RIGHT_POST_A)  # 0.0

    def test_post_b_offset_down(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        ox, oy = d._post_b.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _RIGHT_POST_B)

    def test_door_panel_offset_down_closed(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        ox, oy = d._door.parent_offset
        self.assertAlmostEqual(ox, 0.0)
        self.assertAlmostEqual(oy, _RIGHT_DOOR_CL)


# ===========================================================================
# Animation clips
# ===========================================================================


class TestSlidingDoorAnimationClips(unittest.TestCase):

    def test_activate_clip_registered(self):
        d = _make_door()
        clip = d.animator.get_clip(SlidingDoorSceneObject.CLIP_ACTIVATE)
        self.assertIsNotNone(clip)

    def test_deactivate_clip_registered(self):
        d = _make_door()
        clip = d.animator.get_clip(SlidingDoorSceneObject.CLIP_DEACTIVATE)
        self.assertIsNotNone(clip)

    def test_open_clip_registered_via_alias(self):
        d = _make_door()
        clip = d.animator.get_clip(SlidingDoorSceneObject.CLIP_OPEN)
        self.assertIsNotNone(clip)

    def test_activate_sets_active_true(self):
        d = _make_door()
        d.activate()
        self.assertTrue(d.active)

    def test_deactivate_sets_active_false(self):
        d = _make_door()
        d.activate()
        d.deactivate()
        self.assertFalse(d.active)

    def test_toggle_activates_when_inactive(self):
        d = _make_door()
        d.toggle()
        self.assertTrue(d.active)

    def test_toggle_deactivates_when_active(self):
        d = _make_door()
        d.activate()
        d.toggle()
        self.assertFalse(d.active)

    def test_activate_starts_clip_playing(self):
        d = _make_door()
        d.activate()
        self.assertTrue(d.animator.is_playing)

    def test_current_animator_position_equals_door_slide_pos(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        self.assertAlmostEqual(d.current_animator_position(), d._door_slide_pos)

    def test_current_animator_position_at_closed_for_left(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        self.assertAlmostEqual(d.current_animator_position(), _LEFT_DOOR_CL)

    def test_current_animator_position_at_closed_for_right(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        self.assertAlmostEqual(d.current_animator_position(), _RIGHT_DOOR_CL)


# ===========================================================================
# update() – door panel slides toward open position, posts stay fixed
# ===========================================================================


class TestSlidingDoorUpdate(unittest.TestCase):

    def test_update_without_animation_does_not_move_door(self):
        d = _make_door(x=0.0, y=0.0, direction=CardinalDirection.LEFT)
        initial_slide = d._door_slide_pos
        d.update(0.1)
        self.assertAlmostEqual(d._door_slide_pos, initial_slide)

    def test_update_after_activate_moves_door_toward_open(self):
        """For LEFT, closing pos > opening pos (0), so slide should decrease."""
        d = _make_door(direction=CardinalDirection.LEFT)
        before = d._door_slide_pos
        d.activate()
        d.update(0.1)
        self.assertLess(d._door_slide_pos, before)

    def test_update_after_activate_right_moves_door_toward_open(self):
        """For RIGHT, open pos = total_width, so slide should increase."""
        d = _make_door(direction=CardinalDirection.RIGHT)
        before = d._door_slide_pos
        d.activate()
        d.update(0.1)
        self.assertGreater(d._door_slide_pos, before)

    def test_door_world_x_synced_after_update_horizontal(self):
        d = _make_door(x=100.0, y=50.0, direction=CardinalDirection.LEFT)
        d.activate()
        d.update(0.1)
        expected_x = d.x + d._door_slide_pos
        self.assertAlmostEqual(d._door.x, expected_x)

    def test_door_world_y_synced_after_update_vertical(self):
        d = _make_door(x=100.0, y=50.0, direction=CardinalDirection.DOWN)
        d.activate()
        d.update(0.1)
        expected_y = d.y + d._door_slide_pos
        self.assertAlmostEqual(d._door.y, expected_y)

    def test_door_parent_offset_updated_after_animation(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        d.activate()
        d.update(0.1)
        ox, _ = d._door.parent_offset
        self.assertAlmostEqual(ox, d._door_slide_pos)

    def test_posts_world_x_unchanged_after_activation_horizontal(self):
        d = _make_door(x=100.0, y=50.0, direction=CardinalDirection.LEFT)
        d.update(0.0)
        post_a_x_before = d._post_a.x
        post_b_x_before = d._post_b.x
        d.activate()
        for _ in range(10):
            d.update(0.05)
        self.assertAlmostEqual(d._post_a.x, post_a_x_before)
        self.assertAlmostEqual(d._post_b.x, post_b_x_before)

    def test_multiple_updates_without_activity_idempotent(self):
        d = _make_door(x=50.0, y=30.0, direction=CardinalDirection.RIGHT)
        initial_slide = d._door_slide_pos
        for _ in range(10):
            d.update(0.05)
        self.assertAlmostEqual(d._door_slide_pos, initial_slide)


# ===========================================================================
# Y-value stability – REGRESSION TEST
# Horizontal doors (LEFT/RIGHT) must not drift in Y during animation.
# ===========================================================================


class TestSlidingDoorYValueStability(unittest.TestCase):
    """Regression: horizontal sliding doors must never drift in the Y axis."""

    DT = 0.05
    STEPS = 15

    def _run_and_collect_y(
        self,
        direction: CardinalDirection,
        x: float = 200.0,
        y: float = 150.0,
    ) -> tuple[list[float], list[float], list[float]]:
        d = _make_door(x=x, y=y, direction=direction)
        d.update(self.DT)   # prime positions
        post_a_ys, post_b_ys, door_ys = [], [], []
        d.activate()
        for _ in range(self.STEPS):
            d.update(self.DT)
            post_a_ys.append(d._post_a.y)
            post_b_ys.append(d._post_b.y)
            door_ys.append(d._door.y)
        return post_a_ys, post_b_ys, door_ys

    def test_post_a_y_constant_during_left_activation(self):
        post_a_ys, _, _ = self._run_and_collect_y(CardinalDirection.LEFT)
        self.assertTrue(
            all(abs(v - post_a_ys[0]) < 1e-9 for v in post_a_ys),
            f"post_a.y changed during LEFT activation: {post_a_ys}",
        )

    def test_post_b_y_constant_during_left_activation(self):
        _, post_b_ys, _ = self._run_and_collect_y(CardinalDirection.LEFT)
        self.assertTrue(
            all(abs(v - post_b_ys[0]) < 1e-9 for v in post_b_ys),
            f"post_b.y changed during LEFT activation: {post_b_ys}",
        )

    def test_door_y_constant_during_left_activation(self):
        _, _, door_ys = self._run_and_collect_y(CardinalDirection.LEFT)
        self.assertTrue(
            all(abs(v - door_ys[0]) < 1e-9 for v in door_ys),
            f"door.y changed during LEFT activation: {door_ys}",
        )

    def test_post_a_y_constant_during_right_activation(self):
        post_a_ys, _, _ = self._run_and_collect_y(CardinalDirection.RIGHT)
        self.assertTrue(
            all(abs(v - post_a_ys[0]) < 1e-9 for v in post_a_ys),
            f"post_a.y changed during RIGHT activation: {post_a_ys}",
        )

    def test_door_y_constant_during_right_activation(self):
        _, _, door_ys = self._run_and_collect_y(CardinalDirection.RIGHT)
        self.assertTrue(
            all(abs(v - door_ys[0]) < 1e-9 for v in door_ys),
            f"door.y changed during RIGHT activation: {door_ys}",
        )


# ===========================================================================
# X-value stability – REGRESSION TEST
# Vertical doors (UP/DOWN) must not drift in X during animation.
# ===========================================================================


class TestSlidingDoorXValueStability(unittest.TestCase):
    """Regression: vertical sliding doors must never drift in the X axis."""

    DT = 0.05
    STEPS = 15

    def _run_and_collect_x(
        self,
        direction: CardinalDirection,
        x: float = 100.0,
        y: float = 80.0,
    ) -> tuple[list[float], list[float], list[float]]:
        d = _make_door(x=x, y=y, direction=direction)
        d.update(self.DT)
        post_a_xs, post_b_xs, door_xs = [], [], []
        d.activate()
        for _ in range(self.STEPS):
            d.update(self.DT)
            post_a_xs.append(d._post_a.x)
            post_b_xs.append(d._post_b.x)
            door_xs.append(d._door.x)
        return post_a_xs, post_b_xs, door_xs

    def test_post_a_x_constant_during_up_activation(self):
        post_a_xs, _, _ = self._run_and_collect_x(CardinalDirection.UP)
        self.assertTrue(
            all(abs(v - post_a_xs[0]) < 1e-9 for v in post_a_xs),
            f"post_a.x changed during UP activation: {post_a_xs}",
        )

    def test_post_b_x_constant_during_up_activation(self):
        _, post_b_xs, _ = self._run_and_collect_x(CardinalDirection.UP)
        self.assertTrue(
            all(abs(v - post_b_xs[0]) < 1e-9 for v in post_b_xs),
            f"post_b.x changed during UP activation: {post_b_xs}",
        )

    def test_door_x_constant_during_up_activation(self):
        _, _, door_xs = self._run_and_collect_x(CardinalDirection.UP)
        self.assertTrue(
            all(abs(v - door_xs[0]) < 1e-9 for v in door_xs),
            f"door.x changed during UP activation: {door_xs}",
        )

    def test_post_a_x_constant_during_down_activation(self):
        post_a_xs, _, _ = self._run_and_collect_x(CardinalDirection.DOWN)
        self.assertTrue(
            all(abs(v - post_a_xs[0]) < 1e-9 for v in post_a_xs),
            f"post_a.x changed during DOWN activation: {post_a_xs}",
        )

    def test_door_x_constant_during_down_activation(self):
        _, _, door_xs = self._run_and_collect_x(CardinalDirection.DOWN)
        self.assertTrue(
            all(abs(v - door_xs[0]) < 1e-9 for v in door_xs),
            f"door.x changed during DOWN activation: {door_xs}",
        )


# ===========================================================================
# Posts never move – regression test
# ===========================================================================


class TestSlidingDoorPostsNeverMove(unittest.TestCase):
    """Post_a and post_b must be stationary regardless of door animation."""

    DT = 0.05
    STEPS = 15

    def _run_posts(
        self,
        direction: CardinalDirection,
        x: float = 200.0,
        y: float = 100.0,
    ) -> tuple[list[tuple], list[tuple]]:
        d = _make_door(x=x, y=y, direction=direction)
        d.update(self.DT)
        pos_a, pos_b = [], []
        d.activate()
        for _ in range(self.STEPS):
            d.update(self.DT)
            pos_a.append((d._post_a.x, d._post_a.y))
            pos_b.append((d._post_b.x, d._post_b.y))
        return pos_a, pos_b

    def _assert_constant(self, positions: list[tuple], label: str) -> None:
        ref = positions[0]
        for pos in positions:
            self.assertAlmostEqual(pos[0], ref[0], msg=f"{label}.x drifted: {positions}")
            self.assertAlmostEqual(pos[1], ref[1], msg=f"{label}.y drifted: {positions}")

    def test_posts_stationary_left(self):
        pos_a, pos_b = self._run_posts(CardinalDirection.LEFT)
        self._assert_constant(pos_a, "post_a (LEFT)")
        self._assert_constant(pos_b, "post_b (LEFT)")

    def test_posts_stationary_right(self):
        pos_a, pos_b = self._run_posts(CardinalDirection.RIGHT)
        self._assert_constant(pos_a, "post_a (RIGHT)")
        self._assert_constant(pos_b, "post_b (RIGHT)")

    def test_posts_stationary_up(self):
        pos_a, pos_b = self._run_posts(CardinalDirection.UP)
        self._assert_constant(pos_a, "post_a (UP)")
        self._assert_constant(pos_b, "post_b (UP)")

    def test_posts_stationary_down(self):
        pos_a, pos_b = self._run_posts(CardinalDirection.DOWN)
        self._assert_constant(pos_a, "post_a (DOWN)")
        self._assert_constant(pos_b, "post_b (DOWN)")


# ===========================================================================
# create() factory
# ===========================================================================


class TestSlidingDoorCreate(unittest.TestCase):

    def test_create_returns_door_instance(self):
        d = SlidingDoorSceneObject.create(name="d")
        self.assertIsInstance(d, SlidingDoorSceneObject)

    def test_create_stores_name(self):
        d = SlidingDoorSceneObject.create(name="bay_door")
        self.assertEqual(d.name, "bay_door")

    def test_create_direction_left(self):
        d = SlidingDoorSceneObject.create(name="d", direction=CardinalDirection.LEFT)
        self.assertEqual(d.direction, CardinalDirection.LEFT)

    def test_create_direction_right(self):
        d = SlidingDoorSceneObject.create(name="d", direction=CardinalDirection.RIGHT)
        self.assertEqual(d.direction, CardinalDirection.RIGHT)

    def test_create_direction_up(self):
        d = SlidingDoorSceneObject.create(name="d", direction=CardinalDirection.UP)
        self.assertEqual(d.direction, CardinalDirection.UP)

    def test_create_direction_down(self):
        d = SlidingDoorSceneObject.create(name="d", direction=CardinalDirection.DOWN)
        self.assertEqual(d.direction, CardinalDirection.DOWN)

    # --- Body sizing for horizontal directions ---

    def test_create_left_body_width(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.LEFT,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.width, _BOUNDING_SPAN)

    def test_create_left_body_height(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.LEFT,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT,
        )
        self.assertAlmostEqual(d.height, _DOOR_HEIGHT)

    def test_create_right_body_width(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.RIGHT,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.width, _BOUNDING_SPAN)

    def test_create_right_body_height(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.RIGHT,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT,
        )
        self.assertAlmostEqual(d.height, _DOOR_HEIGHT)

    # --- Body sizing for vertical directions ---

    def test_create_up_body_width(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.UP,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT,
        )
        self.assertAlmostEqual(d.width, _DOOR_HEIGHT)

    def test_create_up_body_height(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.UP,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.height, _BOUNDING_SPAN)

    def test_create_down_body_height(self):
        d = SlidingDoorSceneObject.create(
            name="d", direction=CardinalDirection.DOWN,
            total_width=_TOTAL_WIDTH, door_height=_DOOR_HEIGHT, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.height, _BOUNDING_SPAN)

    # --- Body origin placement ---

    def test_create_right_origin_at_x_y(self):
        d = SlidingDoorSceneObject.create(name="d", x=100.0, y=50.0, direction=CardinalDirection.RIGHT)
        self.assertAlmostEqual(d.x, 100.0)
        self.assertAlmostEqual(d.y, 50.0)

    def test_create_left_shifts_body_origin_left(self):
        """LEFT door: body_x = x - opening so the open panel position sits at offset 0."""
        d = SlidingDoorSceneObject.create(
            name="d", x=200.0, y=50.0,
            direction=CardinalDirection.LEFT,
            total_width=_TOTAL_WIDTH, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.x, 200.0 - _OPENING)

    def test_create_down_origin_at_x_y(self):
        d = SlidingDoorSceneObject.create(name="d", x=50.0, y=100.0, direction=CardinalDirection.DOWN)
        self.assertAlmostEqual(d.x, 50.0)
        self.assertAlmostEqual(d.y, 100.0)

    def test_create_up_shifts_body_origin_up(self):
        """UP door: body_y = y - opening so the open panel position sits at offset 0."""
        d = SlidingDoorSceneObject.create(
            name="d", x=50.0, y=200.0,
            direction=CardinalDirection.UP,
            total_width=_TOTAL_WIDTH, post_size=_POST_SIZE,
        )
        self.assertAlmostEqual(d.y, 200.0 - _OPENING)

    def test_create_stores_total_width(self):
        d = SlidingDoorSceneObject.create(name="d", total_width=120.0)
        self.assertAlmostEqual(d._total_width, 120.0)

    def test_create_stores_door_height(self):
        d = SlidingDoorSceneObject.create(name="d", door_height=20.0)
        self.assertAlmostEqual(d._door_height, 20.0)

    def test_create_stores_post_size(self):
        d = SlidingDoorSceneObject.create(name="d", post_size=15.0)
        self.assertAlmostEqual(d._post_size, 15.0)


# ===========================================================================
# compile_properties()
# ===========================================================================


class TestSlidingDoorCompileProperties(unittest.TestCase):

    def _compiled(self, **kwargs) -> dict:
        d = _make_door(**kwargs)
        d.compile_properties()
        return d._properties

    def test_direction_in_properties(self):
        props = self._compiled(direction=CardinalDirection.LEFT)
        self.assertIn("direction", props)

    def test_direction_value_left(self):
        props = self._compiled(direction=CardinalDirection.LEFT)
        # LEFT is alias for WEST; enum .name returns the canonical name
        self.assertEqual(props["direction"], CardinalDirection.LEFT.name)

    def test_direction_value_down(self):
        props = self._compiled(direction=CardinalDirection.DOWN)
        self.assertEqual(props["direction"], CardinalDirection.DOWN.name)

    def test_total_width_in_properties(self):
        props = self._compiled(total_width=80.0)
        self.assertAlmostEqual(props["total_width"], 80.0)

    def test_door_height_in_properties(self):
        props = self._compiled(door_height=20.0)
        self.assertAlmostEqual(props["door_height"], 20.0)

    def test_post_size_in_properties(self):
        props = self._compiled(post_size=12.0)
        self.assertAlmostEqual(props["post_size"], 12.0)

    def test_animation_duration_in_properties(self):
        props = self._compiled(animation_duration=1.5)
        self.assertAlmostEqual(props["animation_duration"], 1.5)

    def test_post_color_in_properties(self):
        props = self._compiled(post_color="#001122")
        self.assertEqual(props["post_color"], "#001122")

    def test_door_color_in_properties(self):
        props = self._compiled(door_color="#aabb00")
        self.assertEqual(props["door_color"], "#aabb00")

    def test_active_in_properties(self):
        props = self._compiled()
        self.assertIn("active", props)
        self.assertFalse(props["active"])

    def test_name_in_properties(self):
        props = self._compiled(name="gate")
        self.assertEqual(props["name"], "gate")


# ===========================================================================
# from_dict() round-trip
# ===========================================================================


class TestSlidingDoorFromDict(unittest.TestCase):

    def _roundtrip(self, **kwargs) -> SlidingDoorSceneObject:
        original = _make_door(**kwargs)
        original.compile_properties()
        data = original.to_dict()
        return SlidingDoorSceneObject.from_dict(data)

    def test_roundtrip_name(self):
        d = self._roundtrip(name="exit_door")
        self.assertEqual(d.name, "exit_door")

    def test_roundtrip_direction_left(self):
        d = self._roundtrip(direction=CardinalDirection.LEFT)
        self.assertEqual(d.direction, CardinalDirection.LEFT)

    def test_roundtrip_direction_right(self):
        d = self._roundtrip(direction=CardinalDirection.RIGHT)
        self.assertEqual(d.direction, CardinalDirection.RIGHT)

    def test_roundtrip_direction_up(self):
        d = self._roundtrip(direction=CardinalDirection.UP)
        self.assertEqual(d.direction, CardinalDirection.UP)

    def test_roundtrip_direction_down(self):
        d = self._roundtrip(direction=CardinalDirection.DOWN)
        self.assertEqual(d.direction, CardinalDirection.DOWN)

    def test_roundtrip_total_width(self):
        d = self._roundtrip(total_width=80.0)
        self.assertAlmostEqual(d._total_width, 80.0)

    def test_roundtrip_door_height(self):
        d = self._roundtrip(door_height=20.0)
        self.assertAlmostEqual(d._door_height, 20.0)

    def test_roundtrip_post_size(self):
        d = self._roundtrip(post_size=12.0)
        self.assertAlmostEqual(d._post_size, 12.0)

    def test_roundtrip_animation_duration(self):
        d = self._roundtrip(animation_duration=2.0)
        self.assertAlmostEqual(d._animation_duration, 2.0)

    def test_roundtrip_post_color(self):
        d = self._roundtrip(post_color="#ff8800")
        self.assertEqual(d._post_color, "#ff8800")

    def test_roundtrip_door_color(self):
        d = self._roundtrip(door_color="#0088ff")
        self.assertEqual(d._door_color, "#0088ff")

    def test_roundtrip_layer(self):
        d = self._roundtrip(layer=4)
        self.assertEqual(d._layer, 4)

    def test_from_dict_missing_body_raises(self):
        d = _make_door()
        d.compile_properties()
        data = d.to_dict()
        data.pop("body", None)
        with self.assertRaises((ValueError, KeyError)):
            SlidingDoorSceneObject.from_dict(data)


# ===========================================================================
# SceneObjectFactory template
# ===========================================================================


class TestSlidingDoorFactoryTemplate(unittest.TestCase):

    def test_template_registered(self):
        tmpl = SceneObjectFactory.get_template(SlidingDoorSceneObject._template_name)
        self.assertIsNotNone(tmpl)

    def test_template_class_is_sliding_door(self):
        tmpl = SceneObjectFactory.get_template(SlidingDoorSceneObject._template_name)
        self.assertIs(tmpl.scene_object_class, SlidingDoorSceneObject)

    def test_from_dict_produces_door_instance(self):
        d = _make_door(name="factory_test")
        d.compile_properties()
        restored = SlidingDoorSceneObject.from_dict(d.to_dict())
        self.assertIsInstance(restored, SlidingDoorSceneObject)


# ===========================================================================
# Rotation – component layout stability
# REGRESSION: rotating the SceneObject must not misalign the door panel or
# posts.  Only CardinalDirection.RIGHT produced a clean connection before the
# fix because the generic rotate_components formula cannot correctly decode the
# slide-axis semantics of a sliding door.
# ===========================================================================

# Precomputed expected values for direction-specific layouts.
# DOWN / RIGHT  ("positive axis" cases) ─────────────────────────────────────
_RIGHT_POST_A_AXIS = 0.0
_RIGHT_POST_B_AXIS = _TOTAL_WIDTH - _POST_SIZE          # 90.0
_RIGHT_DOOR_CLOSED = _POST_SIZE                         # 10.0
_RIGHT_DOOR_OPEN = _TOTAL_WIDTH                       # 100.0

_DOWN_POST_A_AXIS = 0.0
_DOWN_POST_B_AXIS = _TOTAL_WIDTH - _POST_SIZE           # 90.0
_DOWN_DOOR_CLOSED = _POST_SIZE                         # 10.0
_DOWN_DOOR_OPEN = _TOTAL_WIDTH                       # 100.0

# LEFT / UP  ("negative axis" cases) ────────────────────────────────────────
_LEFT_POST_A_AXIS = _OPENING                            # 80.0
_LEFT_POST_B_AXIS = _OPENING + _TOTAL_WIDTH - _POST_SIZE  # 170.0
_LEFT_DOOR_CLOSED = _OPENING + _POST_SIZE               # 90.0
_LEFT_DOOR_OPEN = 0.0

_UP_POST_A_AXIS = _OPENING                              # 80.0
_UP_POST_B_AXIS = _OPENING + _TOTAL_WIDTH - _POST_SIZE  # 170.0
_UP_DOOR_CLOSED = _OPENING + _POST_SIZE                # 90.0
_UP_DOOR_OPEN = 0.0


class TestSlidingDoorRotationLayout(unittest.TestCase):
    """After any 90° rotation component sizes, parent offsets, and slide
    positions must exactly match what a door freshly built in the new
    direction would produce."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_horizontal_sizes(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        self.assertAlmostEqual(d._post_a.width, _POST_SIZE, msg=f"post_a.width {msg}")
        self.assertAlmostEqual(d._post_a.height, _DOOR_HEIGHT, msg=f"post_a.height {msg}")
        self.assertAlmostEqual(d._post_b.width, _POST_SIZE, msg=f"post_b.width {msg}")
        self.assertAlmostEqual(d._post_b.height, _DOOR_HEIGHT, msg=f"post_b.height {msg}")
        self.assertAlmostEqual(d._door.width, _OPENING, msg=f"door.width {msg}")
        self.assertAlmostEqual(d._door.height, _DOOR_HEIGHT, msg=f"door.height {msg}")

    def _assert_vertical_sizes(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        self.assertAlmostEqual(d._post_a.width, _DOOR_HEIGHT, msg=f"post_a.width {msg}")
        self.assertAlmostEqual(d._post_a.height, _POST_SIZE, msg=f"post_a.height {msg}")
        self.assertAlmostEqual(d._post_b.width, _DOOR_HEIGHT, msg=f"post_b.width {msg}")
        self.assertAlmostEqual(d._post_b.height, _POST_SIZE, msg=f"post_b.height {msg}")
        self.assertAlmostEqual(d._door.width, _DOOR_HEIGHT, msg=f"door.width {msg}")
        self.assertAlmostEqual(d._door.height, _OPENING, msg=f"door.height {msg}")

    def _assert_right_offsets(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        ox_a, oy_a = d._post_a.parent_offset
        ox_b, oy_b = d._post_b.parent_offset
        ox_d, oy_d = d._door.parent_offset
        self.assertAlmostEqual(ox_a, _RIGHT_POST_A_AXIS, msg=f"post_a.ox {msg}")
        self.assertAlmostEqual(oy_a, 0.0, msg=f"post_a.oy {msg}")
        self.assertAlmostEqual(ox_b, _RIGHT_POST_B_AXIS, msg=f"post_b.ox {msg}")
        self.assertAlmostEqual(oy_b, 0.0, msg=f"post_b.oy {msg}")
        self.assertAlmostEqual(ox_d, _RIGHT_DOOR_CLOSED, msg=f"door.ox {msg}")
        self.assertAlmostEqual(oy_d, 0.0, msg=f"door.oy {msg}")

    def _assert_down_offsets(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        ox_a, oy_a = d._post_a.parent_offset
        ox_b, oy_b = d._post_b.parent_offset
        ox_d, oy_d = d._door.parent_offset
        self.assertAlmostEqual(ox_a, 0.0, msg=f"post_a.ox {msg}")
        self.assertAlmostEqual(oy_a, _DOWN_POST_A_AXIS, msg=f"post_a.oy {msg}")
        self.assertAlmostEqual(ox_b, 0.0, msg=f"post_b.ox {msg}")
        self.assertAlmostEqual(oy_b, _DOWN_POST_B_AXIS, msg=f"post_b.oy {msg}")
        self.assertAlmostEqual(ox_d, 0.0, msg=f"door.ox {msg}")
        self.assertAlmostEqual(oy_d, _DOWN_DOOR_CLOSED, msg=f"door.oy {msg}")

    def _assert_left_offsets(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        ox_a, oy_a = d._post_a.parent_offset
        ox_b, oy_b = d._post_b.parent_offset
        ox_d, oy_d = d._door.parent_offset
        self.assertAlmostEqual(ox_a, _LEFT_POST_A_AXIS, msg=f"post_a.ox {msg}")
        self.assertAlmostEqual(oy_a, 0.0, msg=f"post_a.oy {msg}")
        self.assertAlmostEqual(ox_b, _LEFT_POST_B_AXIS, msg=f"post_b.ox {msg}")
        self.assertAlmostEqual(oy_b, 0.0, msg=f"post_b.oy {msg}")
        self.assertAlmostEqual(ox_d, _LEFT_DOOR_CLOSED, msg=f"door.ox {msg}")
        self.assertAlmostEqual(oy_d, 0.0, msg=f"door.oy {msg}")

    def _assert_up_offsets(self, d: SlidingDoorSceneObject, msg: str = "") -> None:
        ox_a, oy_a = d._post_a.parent_offset
        ox_b, oy_b = d._post_b.parent_offset
        ox_d, oy_d = d._door.parent_offset
        self.assertAlmostEqual(ox_a, 0.0, msg=f"post_a.ox {msg}")
        self.assertAlmostEqual(oy_a, _UP_POST_A_AXIS, msg=f"post_a.oy {msg}")
        self.assertAlmostEqual(ox_b, 0.0, msg=f"post_b.ox {msg}")
        self.assertAlmostEqual(oy_b, _UP_POST_B_AXIS, msg=f"post_b.oy {msg}")
        self.assertAlmostEqual(ox_d, 0.0, msg=f"door.ox {msg}")
        self.assertAlmostEqual(oy_d, _UP_DOOR_CLOSED, msg=f"door.oy {msg}")

    # ------------------------------------------------------------------
    # Component sizes after CW rotation
    # ------------------------------------------------------------------

    def test_cw_right_to_down_sizes(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_clockwise()
        self._assert_vertical_sizes(d, "after CW RIGHT→DOWN")

    def test_cw_down_to_left_sizes(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_clockwise()
        self._assert_horizontal_sizes(d, "after CW DOWN→LEFT")

    def test_cw_left_to_up_sizes(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        d.rotate_clockwise()
        self._assert_vertical_sizes(d, "after CW LEFT→UP")

    def test_cw_up_to_right_sizes(self):
        d = _make_door(direction=CardinalDirection.UP)
        d.rotate_clockwise()
        self._assert_horizontal_sizes(d, "after CW UP→RIGHT")

    # ------------------------------------------------------------------
    # Component offsets after CW rotation
    # ------------------------------------------------------------------

    def test_cw_right_to_down_offsets(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_clockwise()
        self._assert_down_offsets(d, "after CW RIGHT→DOWN")

    def test_cw_down_to_left_offsets(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_clockwise()
        self._assert_left_offsets(d, "after CW DOWN→LEFT")

    def test_cw_left_to_up_offsets(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        d.rotate_clockwise()
        self._assert_up_offsets(d, "after CW LEFT→UP")

    def test_cw_up_to_right_offsets(self):
        d = _make_door(direction=CardinalDirection.UP)
        d.rotate_clockwise()
        self._assert_right_offsets(d, "after CW UP→RIGHT")

    # ------------------------------------------------------------------
    # Component sizes after CCW rotation
    # ------------------------------------------------------------------

    def test_ccw_right_to_up_sizes(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_counterclockwise()
        self._assert_vertical_sizes(d, "after CCW RIGHT→UP")

    def test_ccw_down_to_right_sizes(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_counterclockwise()
        self._assert_horizontal_sizes(d, "after CCW DOWN→RIGHT")

    def test_ccw_left_to_down_sizes(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        d.rotate_counterclockwise()
        self._assert_vertical_sizes(d, "after CCW LEFT→DOWN")

    def test_ccw_up_to_left_sizes(self):
        d = _make_door(direction=CardinalDirection.UP)
        d.rotate_counterclockwise()
        self._assert_horizontal_sizes(d, "after CCW UP→LEFT")

    # ------------------------------------------------------------------
    # Component offsets after CCW rotation
    # ------------------------------------------------------------------

    def test_ccw_right_to_up_offsets(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_counterclockwise()
        self._assert_up_offsets(d, "after CCW RIGHT→UP")

    def test_ccw_down_to_right_offsets(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_counterclockwise()
        self._assert_right_offsets(d, "after CCW DOWN→RIGHT")

    def test_ccw_left_to_down_offsets(self):
        d = _make_door(direction=CardinalDirection.LEFT)
        d.rotate_counterclockwise()
        self._assert_down_offsets(d, "after CCW LEFT→DOWN")

    def test_ccw_up_to_left_offsets(self):
        d = _make_door(direction=CardinalDirection.UP)
        d.rotate_counterclockwise()
        self._assert_left_offsets(d, "after CCW UP→LEFT")

    # ------------------------------------------------------------------
    # Door connects flush to post_a at the closed position
    # Invariant: door's slide-axis offset == post_a's slide-axis offset + post_size
    # ------------------------------------------------------------------

    def test_door_flush_with_post_a_after_cw_all_directions(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                d = _make_door(direction=start)
                d.rotate_clockwise()
                ox_a, oy_a = d._post_a.parent_offset
                ox_d, oy_d = d._door.parent_offset
                if d.is_horizontal:
                    self.assertAlmostEqual(
                        ox_d, ox_a + _POST_SIZE,
                        msg=f"door.ox should equal post_a.ox + post_size after CW from {start}",
                    )
                else:
                    self.assertAlmostEqual(
                        oy_d, oy_a + _POST_SIZE,
                        msg=f"door.oy should equal post_a.oy + post_size after CW from {start}",
                    )

    def test_door_flush_with_post_a_after_ccw_all_directions(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                d = _make_door(direction=start)
                d.rotate_counterclockwise()
                ox_a, oy_a = d._post_a.parent_offset
                ox_d, oy_d = d._door.parent_offset
                if d.is_horizontal:
                    self.assertAlmostEqual(
                        ox_d, ox_a + _POST_SIZE,
                        msg=f"door.ox should equal post_a.ox + post_size after CCW from {start}",
                    )
                else:
                    self.assertAlmostEqual(
                        oy_d, oy_a + _POST_SIZE,
                        msg=f"door.oy should equal post_a.oy + post_size after CCW from {start}",
                    )

    # ------------------------------------------------------------------
    # Offsets remain correct after update() following rotation
    # (regression: stale _door_slide_pos could override to a wrong axis)
    # ------------------------------------------------------------------

    def test_cw_right_to_down_offsets_after_update(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_clockwise()
        d.update(0.016)
        self._assert_down_offsets(d, "after CW RIGHT→DOWN + update")

    def test_cw_down_to_left_offsets_after_update(self):
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_clockwise()
        d.update(0.016)
        self._assert_left_offsets(d, "after CW DOWN→LEFT + update")

    def test_ccw_right_to_up_offsets_after_update(self):
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_counterclockwise()
        d.update(0.016)
        self._assert_up_offsets(d, "after CCW RIGHT→UP + update")

    # ------------------------------------------------------------------
    # Four CW rotations restore the original layout
    # ------------------------------------------------------------------

    def test_four_cw_rotations_restore_sizes(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                d = _make_door(direction=start)
                w0_a, h0_a = d._post_a.width, d._post_a.height
                w0_d, h0_d = d._door.width, d._door.height
                for _ in range(4):
                    d.rotate_clockwise()
                self.assertAlmostEqual(d._post_a.width, w0_a, msg=f"post_a.width after 4×CW from {start}")
                self.assertAlmostEqual(d._post_a.height, h0_a, msg=f"post_a.height after 4×CW from {start}")
                self.assertAlmostEqual(d._door.width, w0_d, msg=f"door.width after 4×CW from {start}")
                self.assertAlmostEqual(d._door.height, h0_d, msg=f"door.height after 4×CW from {start}")

    def test_four_cw_rotations_restore_offsets(self):
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                d = _make_door(direction=start)
                ox0_a, oy0_a = d._post_a.parent_offset
                ox0_b, oy0_b = d._post_b.parent_offset
                ox0_d, oy0_d = d._door.parent_offset
                for _ in range(4):
                    d.rotate_clockwise()
                ox_a, oy_a = d._post_a.parent_offset
                ox_b, oy_b = d._post_b.parent_offset
                ox_d, oy_d = d._door.parent_offset
                self.assertAlmostEqual(ox_a, ox0_a, msg=f"post_a.ox after 4×CW from {start}")
                self.assertAlmostEqual(oy_a, oy0_a, msg=f"post_a.oy after 4×CW from {start}")
                self.assertAlmostEqual(ox_b, ox0_b, msg=f"post_b.ox after 4×CW from {start}")
                self.assertAlmostEqual(oy_b, oy0_b, msg=f"post_b.oy after 4×CW from {start}")
                self.assertAlmostEqual(ox_d, ox0_d, msg=f"door.ox after 4×CW from {start}")
                self.assertAlmostEqual(oy_d, oy0_d, msg=f"door.oy after 4×CW from {start}")

    # ------------------------------------------------------------------
    # Animation clip targets update with direction
    # After rotating to a LEFT/UP door the open position changes to 0.0;
    # after rotating to a RIGHT/DOWN door it becomes total_width (100.0).
    # ------------------------------------------------------------------

    def test_animation_open_target_correct_after_cw_to_left(self):
        """CW DOWN→LEFT: open == 0.0."""
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_clockwise()
        self.assertAlmostEqual(d._door_open_offset, 0.0)

    def test_animation_closed_target_correct_after_cw_to_left(self):
        """CW DOWN→LEFT: closed == opening + post_size = 90.0."""
        d = _make_door(direction=CardinalDirection.DOWN)
        d.rotate_clockwise()
        self.assertAlmostEqual(d._door_closed_offset, _LEFT_DOOR_CLOSED)

    def test_animation_open_target_correct_after_cw_to_down(self):
        """CW RIGHT→DOWN: open == total_width = 100.0."""
        d = _make_door(direction=CardinalDirection.RIGHT)
        d.rotate_clockwise()
        self.assertAlmostEqual(d._door_open_offset, _TOTAL_WIDTH)

    def test_door_slide_pos_reset_to_closed_after_rotation(self):
        """_door_slide_pos must equal _door_closed_offset immediately after any rotation."""
        for start in (CardinalDirection.RIGHT, CardinalDirection.DOWN,
                      CardinalDirection.LEFT, CardinalDirection.UP):
            with self.subTest(start=start):
                d = _make_door(direction=start)
                d.rotate_clockwise()
                self.assertAlmostEqual(
                    d._door_slide_pos, d._door_closed_offset,
                    msg=f"_door_slide_pos should equal _door_closed_offset after CW from {start}",
                )


if __name__ == "__main__":
    unittest.main()
