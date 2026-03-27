"""Unit tests for CompositeKinematicSceneObject and ActivatableCompositeKinematicSceneObject.

Notes on two known construction quirks patched here:

1. ``CompositeSceneObject.__init__`` does not accept ``scene_object_type`` or
   ``template_name`` keyword arguments, even though
   ``CompositeKinematicSceneObject.__init__`` passes them via ``super().__init__``.
   ``_accepting_composite_init`` strips those kwargs before delegating so that
   the real initialisation logic in the kinematic class can be exercised.

2. ``CompositeSceneObject.__init__`` calls ``self.set_direction`` before
   initialising ``self._components``, which triggers ``rotate_components`` and
   would raise ``AttributeError``.  ``_accepting_composite_init`` pre-initialises
   ``_components`` to an empty dict to guard against this.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from pyrox.interfaces import BodyType, CardinalDirection, CollisionLayer
from pyrox.models.scene.animation import (
    AnimationClip,
    AnimationEasing,
    AnimationMode,
    AnimationTrack,
)

from pyrox.models.scene.assets.topdown._compkinemetic import (
    ActivatableCompositeKinematicSceneObject,
    CompositeKinematicSceneObject,
)


# ---------------------------------------------------------------------------
# Concrete test subclasses
# ---------------------------------------------------------------------------

class _ConcreteKinematic(CompositeKinematicSceneObject):
    """Minimal concrete ``CompositeKinematicSceneObject`` for testing."""

    _scene_object_type = "test_kinematic"
    _template_name = "ConcreteKinematic"

    def build_components(self) -> None:
        pass


class _ConcreteActivatable(ActivatableCompositeKinematicSceneObject):
    """Minimal concrete ``ActivatableCompositeKinematicSceneObject`` for testing."""

    _scene_object_type = "test_activatable"
    _template_name = "ConcreteActivatable"

    def build_components(self) -> None:
        pass

    def current_animator_position(self) -> float:
        return 42.0


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def _mock_body(direction: CardinalDirection = CardinalDirection.RIGHT) -> MagicMock:
    """Return a MagicMock physics body.

    ``body.direction`` is set as an instance attribute equal to *direction* so
    that the ``if self.direction == direction: return`` early-exit check in
    ``ICompositeSceneObject.set_direction`` fires immediately, preventing the
    full rotation path (which would access ``_components``) from running.
    """
    body = MagicMock()
    body.get_collider.return_value = MagicMock()
    body.direction = direction
    return body


def _make_kinematic(
    name: str = "ck",
    direction: CardinalDirection = CardinalDirection.RIGHT,
    physics_body: MagicMock | None = None,
    **kwargs,
) -> _ConcreteKinematic:
    body = physics_body or _mock_body(direction)
    return _ConcreteKinematic(
        name=name,
        physics_body=body,
        direction=direction,
        **kwargs,
    )


def _make_activatable(
    name: str = "ca",
    direction: CardinalDirection = CardinalDirection.RIGHT,
    properties: dict | None = None,
    animation_duration: float = 0.5,
    physics_body: MagicMock | None = None,
) -> _ConcreteActivatable:
    body = physics_body or _mock_body(direction)
    return _ConcreteActivatable(
        name=name,
        physics_body=body,
        direction=direction,
        properties=properties or {},
        animation_duration=animation_duration,
    )


# ===========================================================================
# CompositeKinematicSceneObject
# ===========================================================================

class TestCompositeKinematicInit(unittest.TestCase):

    def test_transparent_layer_set_on_collider(self):
        body = _mock_body()
        _make_kinematic(physics_body=body)
        body.get_collider.return_value.set_collision_layer.assert_called_once_with(
            CollisionLayer.TRANSPARENT
        )

    def test_default_collision_mask_set_on_collider(self):
        body = _mock_body()
        _make_kinematic(physics_body=body)
        body.get_collider.return_value.set_collision_mask.assert_called_once_with(
            CompositeKinematicSceneObject.default_collision_mask
        )

    def test_name_stored_correctly(self):
        obj = _make_kinematic(name="my_obj")
        self.assertEqual(obj.name, "my_obj")

    def test_default_collision_mask_contains_expected_layers(self):
        mask = CompositeKinematicSceneObject.default_collision_mask
        self.assertIn(CollisionLayer.DEFAULT, mask)
        self.assertIn(CollisionLayer.PLAYER, mask)
        self.assertIn(CollisionLayer.ENEMY, mask)


class TestCompositeKinematicDirectionProperties(unittest.TestCase):

    def test_is_horizontal_right(self):
        obj = _make_kinematic(direction=CardinalDirection.RIGHT)
        self.assertTrue(obj.is_horizontal)

    def test_is_horizontal_left(self):
        obj = _make_kinematic(direction=CardinalDirection.LEFT)
        self.assertTrue(obj.is_horizontal)

    def test_is_vertical_up(self):
        obj = _make_kinematic(direction=CardinalDirection.UP)
        self.assertTrue(obj.is_vertical)

    def test_is_vertical_down(self):
        obj = _make_kinematic(direction=CardinalDirection.DOWN)
        self.assertTrue(obj.is_vertical)

    def test_not_horizontal_when_up(self):
        obj = _make_kinematic(direction=CardinalDirection.UP)
        self.assertFalse(obj.is_horizontal)

    def test_not_horizontal_when_down(self):
        obj = _make_kinematic(direction=CardinalDirection.DOWN)
        self.assertFalse(obj.is_horizontal)

    def test_not_vertical_when_right(self):
        obj = _make_kinematic(direction=CardinalDirection.RIGHT)
        self.assertFalse(obj.is_vertical)

    def test_not_vertical_when_left(self):
        obj = _make_kinematic(direction=CardinalDirection.LEFT)
        self.assertFalse(obj.is_vertical)


class TestCompositeKinematicCompileProperties(unittest.TestCase):

    def test_compile_properties_adds_direction_key(self):
        obj = _make_kinematic(direction=CardinalDirection.UP)
        obj.compile_properties()
        self.assertIn("direction", obj._properties)

    def test_compile_properties_direction_uses_enum_name(self):
        obj = _make_kinematic(direction=CardinalDirection.UP)
        obj.compile_properties()
        self.assertEqual(obj._properties["direction"], CardinalDirection.UP.name)


class TestCompositeKinematicCreateSimpleClip(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_kinematic()

    def test_returns_animation_clip_instance(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 0.0, 100.0)
        self.assertIsInstance(clip, AnimationClip)

    def test_clip_name(self):
        clip = self.obj.create_simple_clip("my_clip", 1.0, "x", 0.0, 100.0)
        self.assertEqual(clip.name, "my_clip")

    def test_clip_duration(self):
        clip = self.obj.create_simple_clip("c", 2.5, "x", 0.0, 100.0)
        self.assertAlmostEqual(clip.duration, 2.5)

    def test_default_mode_is_once(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 0.0, 100.0)
        self.assertEqual(clip.mode, AnimationMode.ONCE)

    def test_custom_mode_respected(self):
        clip = self.obj.create_simple_clip(
            "c", 1.0, "x", 0.0, 100.0, animation_mode=AnimationMode.LOOP
        )
        self.assertEqual(clip.mode, AnimationMode.LOOP)

    def test_has_exactly_one_track(self):
        clip = self.obj.create_simple_clip("c", 1.0, "pos", 0.0, 50.0)
        self.assertEqual(len(clip.tracks), 1)

    def test_track_property_name(self):
        clip = self.obj.create_simple_clip("c", 1.0, "my_prop", 0.0, 50.0)
        self.assertEqual(clip.tracks[0].property, "my_prop")

    def test_track_has_two_keyframes(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 0.0, 50.0)
        self.assertEqual(len(clip.tracks[0].keyframes), 2)

    def test_start_keyframe_value(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 10.0, 90.0)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 10.0)

    def test_end_keyframe_value(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 10.0, 90.0)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 90.0)

    def test_keyframe_times(self):
        clip = self.obj.create_simple_clip("c", 2.0, "x", 0.0, 50.0)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].time, 0.0)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].time, 2.0)

    def test_default_easing_is_ease_in_out(self):
        clip = self.obj.create_simple_clip("c", 1.0, "x", 0.0, 50.0)
        self.assertEqual(clip.tracks[0].easing, AnimationEasing.EASE_IN_OUT)

    def test_custom_easing_respected(self):
        clip = self.obj.create_simple_clip(
            "c", 1.0, "x", 0.0, 50.0, animation_easing=AnimationEasing.LINEAR
        )
        self.assertEqual(clip.tracks[0].easing, AnimationEasing.LINEAR)


class TestCompositeKinematicCreateSimpleComponent(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_kinematic(name="parent")

    def _make_comp(self, name: str = "arm", **kwargs):
        defaults = dict(
            template_name="Base Physics Body",
            body_type=BodyType.STATIC,
            width=20.0,
            height=10.0,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=[CollisionLayer.DEFAULT],
        )
        defaults.update(kwargs)
        return self.obj.create_simple_component(name=name, **defaults)

    def test_returns_scene_object_instance(self):
        from pyrox.models.scene.sceneobject import SceneObject
        comp = self._make_comp()
        self.assertIsInstance(comp, SceneObject)

    def test_name_contains_parent_name(self):
        comp = self._make_comp(name="arm")
        self.assertIn("parent", comp.name)

    def test_name_contains_component_name(self):
        comp = self._make_comp(name="rod")
        self.assertIn("rod", comp.name)

    def test_default_bg_color(self):
        comp = self._make_comp()
        self.assertEqual(comp.bg_color, "#888888")

    def test_custom_bg_color(self):
        comp = self._make_comp(bg_color="#ff0000")
        self.assertEqual(comp.bg_color, "#ff0000")


class TestCompositeKinematicGetCompositeBodyFromDict(unittest.TestCase):

    def test_returns_none_for_none(self):
        result = _ConcreteKinematic.get_composite_body_from_dict(None)
        self.assertIsNone(result)

    def test_returns_none_for_empty_dict(self):
        result = _ConcreteKinematic.get_composite_body_from_dict({})
        self.assertIsNone(result)

    def test_returns_physics_body_for_valid_dict(self):
        from pyrox.models.physics import BasePhysicsBody
        result = _ConcreteKinematic.get_composite_body_from_dict({"name": "b"})
        self.assertIsInstance(result, BasePhysicsBody)

    def test_collision_layer_set_to_terrain(self):
        result = _ConcreteKinematic.get_composite_body_from_dict({"name": "b"})
        self.assertEqual(result.get_collider().collision_layer, CollisionLayer.TERRAIN)

    def test_collision_mask_matches_class_default(self):
        result = _ConcreteKinematic.get_composite_body_from_dict({"name": "b"})
        self.assertEqual(
            result.get_collider().collision_mask,
            _ConcreteKinematic.default_collision_mask,
        )


# ===========================================================================
# ActivatableCompositeKinematicSceneObject
# ===========================================================================

class TestActivatableInit(unittest.TestCase):

    def test_default_active_is_false(self):
        obj = _make_activatable()
        self.assertFalse(obj._active)

    def test_animation_duration_stored(self):
        obj = _make_activatable(animation_duration=1.25)
        self.assertAlmostEqual(obj._animation_duration, 1.25)

    def test_active_false_from_properties(self):
        obj = _make_activatable(properties={"active": False})
        self.assertFalse(obj._active)

    def test_active_true_from_properties(self):
        obj = _make_activatable(properties={"active": True})
        self.assertTrue(obj._active)


class TestActivatableActiveState(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_activatable()

    def test_get_active_state_default_false(self):
        self.assertFalse(self.obj.get_active_state())

    def test_set_active_state_to_true(self):
        self.obj.set_active_state(True)
        self.assertTrue(self.obj._active)

    def test_set_active_state_to_false_from_true(self):
        self.obj._active = True
        self.obj.set_active_state(False)
        self.assertFalse(self.obj._active)

    def test_set_active_state_same_value_is_noop(self):
        with patch.object(self.obj.animator, "play") as mock_play:
            self.obj.set_active_state(False)  # already False
            mock_play.assert_not_called()

    def test_set_active_state_plays_activate_clip(self):
        self.obj.animator.add_clip(
            AnimationClip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE, 0.5)
        )
        with patch.object(self.obj.animator, "play") as mock_play:
            self.obj.set_active_state(True)
            mock_play.assert_called_once_with(
                ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE
            )

    def test_set_active_state_plays_deactivate_clip(self):
        self.obj._active = True
        self.obj.animator.add_clip(
            AnimationClip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE, 0.5)
        )
        with patch.object(self.obj.animator, "play") as mock_play:
            self.obj.set_active_state(False)
            mock_play.assert_called_once_with(
                ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE
            )

    def test_active_property_getter(self):
        self.obj._active = True
        self.assertTrue(self.obj.active)

    def test_active_property_setter(self):
        self.obj.animator.add_clip(
            AnimationClip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE, 0.5)
        )
        self.obj.active = True
        self.assertTrue(self.obj._active)

    def test_is_animating_true_when_active(self):
        self.obj._active = True
        self.assertTrue(self.obj.is_animating)

    def test_is_animating_false_when_inactive(self):
        self.obj._active = False
        self.assertFalse(self.obj.is_animating)


class TestActivatableCurrentAnimatorPosition(unittest.TestCase):

    def test_concrete_subclass_returns_value(self):
        obj = _make_activatable()
        self.assertAlmostEqual(obj.current_animator_position(), 42.0)

    def test_base_class_raises_not_implemented(self):
        obj = _make_activatable()
        with self.assertRaises(NotImplementedError):
            ActivatableCompositeKinematicSceneObject.current_animator_position(obj)


class TestActivatableSnapAnimationStart(unittest.TestCase):

    def _make_obj_with_clip(self, initial: float = 5.0) -> _ConcreteActivatable:
        obj = _make_activatable()
        track = (
            AnimationTrack("x")
            .add_keyframe(0.0, initial)
            .add_keyframe(0.5, 100.0)
        )
        clip = (
            AnimationClip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE, 0.5)
            .add_track(track)
        )
        obj.animator.add_clip(clip)
        return obj

    def test_noop_when_clip_not_registered(self):
        obj = _make_activatable()
        obj.snap_animation_start("nonexistent")  # must not raise

    def test_first_keyframe_set_to_current_position(self):
        obj = self._make_obj_with_clip(initial=5.0)
        obj.snap_animation_start(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        clip = obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        # _ConcreteActivatable.current_animator_position() returns 42.0
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 42.0)

    def test_last_keyframe_unchanged(self):
        obj = self._make_obj_with_clip(initial=5.0)
        obj.snap_animation_start(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        clip = obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 100.0)


class TestActivatableUpdateAnimationStartEnd(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_activatable()
        track = AnimationTrack("x").add_keyframe(0.0, 0.0).add_keyframe(1.0, 100.0)
        self.obj.animator.add_clip(AnimationClip("clip", 1.0).add_track(track))

    def test_noop_when_clip_not_found(self):
        self.obj.update_animation_start_end("nonexistent", 0.0, 100.0)  # must not raise

    def test_first_keyframe_updated(self):
        self.obj.update_animation_start_end("clip", 25.0, 75.0)
        clip = self.obj.animator.get_clip("clip")
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 25.0)

    def test_last_keyframe_updated(self):
        self.obj.update_animation_start_end("clip", 25.0, 75.0)
        clip = self.obj.animator.get_clip("clip")
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 75.0)

    def test_noop_for_track_with_single_keyframe(self):
        track = AnimationTrack("y").add_keyframe(0.0, 0.0)
        self.obj.animator.add_clip(AnimationClip("one_kf", 1.0).add_track(track))
        self.obj.update_animation_start_end("one_kf", 10.0, 50.0)  # must not raise


class TestActivatableUpdateActivateDeactivateTargets(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_activatable()
        for clip_name in (
            ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE,
            ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE,
        ):
            track = AnimationTrack("x").add_keyframe(0.0, 0.0).add_keyframe(1.0, 0.0)
            self.obj.animator.add_clip(AnimationClip(clip_name, 1.0).add_track(track))

    def test_activate_clip_start_is_target_inactive(self):
        self.obj.update_activate_deactivate_targets(target_active=80.0, target_inactive=10.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 10.0)

    def test_activate_clip_end_is_target_active(self):
        self.obj.update_activate_deactivate_targets(target_active=80.0, target_inactive=10.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 80.0)

    def test_deactivate_clip_start_is_target_active(self):
        self.obj.update_activate_deactivate_targets(target_active=80.0, target_inactive=10.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 80.0)

    def test_deactivate_clip_end_is_target_inactive(self):
        self.obj.update_activate_deactivate_targets(target_active=80.0, target_inactive=10.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 10.0)


class TestActivatableCreateClipsOnProperty(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_activatable()

    def test_activate_clip_registered(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        self.assertIsNotNone(
            self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        )

    def test_deactivate_clip_registered(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        self.assertIsNotNone(
            self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE)
        )

    def test_activate_clip_start_is_target1(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 0.0)

    def test_activate_clip_end_is_target2(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 50.0)

    def test_deactivate_clip_start_is_target2(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[0].value, 50.0)

    def test_deactivate_clip_end_is_target1(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_DEACTIVATE)
        self.assertAlmostEqual(clip.tracks[0].keyframes[-1].value, 0.0)

    def test_custom_duration(self):
        self.obj.create_clips_on_property("pos", 0.0, 50.0, animation_duration=2.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertAlmostEqual(clip.duration, 2.0)

    def test_track_property_name(self):
        self.obj.create_clips_on_property("my_property", 0.0, 50.0)
        clip = self.obj.animator.get_clip(ActivatableCompositeKinematicSceneObject.CLIP_ACTIVATE)
        self.assertEqual(clip.tracks[0].property, "my_property")


class TestActivatableInputMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = _make_activatable()

    def test_activate_sets_active_true(self):
        self.obj.activate()
        self.assertTrue(self.obj._active)

    def test_deactivate_sets_active_false(self):
        self.obj._active = True
        self.obj.deactivate()
        self.assertFalse(self.obj._active)

    def test_toggle_false_to_true(self):
        self.obj._active = False
        self.obj.toggle()
        self.assertTrue(self.obj._active)

    def test_toggle_true_to_false(self):
        self.obj._active = True
        self.obj.toggle()
        self.assertFalse(self.obj._active)

    def test_get_inputs_has_activate(self):
        self.assertIn("activate", self.obj.get_inputs())

    def test_get_inputs_has_deactivate(self):
        self.assertIn("deactivate", self.obj.get_inputs())

    def test_get_inputs_has_toggle(self):
        self.assertIn("toggle", self.obj.get_inputs())

    def test_get_inputs_has_set_direction(self):
        self.assertIn("set_direction", self.obj.get_inputs())

    def test_get_inputs_methods_are_callable(self):
        inputs = self.obj.get_inputs()
        for key in ("activate", "deactivate", "toggle"):
            self.assertTrue(callable(inputs[key]), msg=f"'{key}' should be callable")

    def test_get_inputs_methods_are_bound_to_instance(self):
        inputs = self.obj.get_inputs()
        self.assertEqual(inputs["activate"], self.obj.activate)
        self.assertEqual(inputs["deactivate"], self.obj.deactivate)
        self.assertEqual(inputs["toggle"], self.obj.toggle)


class TestActivatableCompileProperties(unittest.TestCase):

    def test_compile_properties_includes_active_key(self):
        obj = _make_activatable()
        obj.compile_properties()
        self.assertIn("active", obj._properties)

    def test_compile_properties_active_false_by_default(self):
        obj = _make_activatable()
        obj.compile_properties()
        self.assertFalse(obj._properties["active"])

    def test_compile_properties_active_true_when_set(self):
        obj = _make_activatable()
        obj._active = True
        obj.compile_properties()
        self.assertTrue(obj._properties["active"])


if __name__ == "__main__":
    unittest.main()
