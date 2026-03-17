"""Unit tests for the scene animation system.

Covers AnimationEasing, AnimationTrack, AnimationClip, and SceneAnimator.
All tests are pure-Python with no GUI or Qt dependency.
"""
import unittest
from unittest.mock import MagicMock

from pyrox.models.scene.animation import (
    AnimationClip,
    AnimationEasing,
    AnimationMode,
    AnimationTrack,
    SceneAnimator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_clip(
    name: str = "clip",
    duration: float = 1.0,
    mode: AnimationMode = AnimationMode.ONCE,
    prop: str = "x",
    start_val: float = 0.0,
    end_val: float = 100.0,
) -> AnimationClip:
    """Build a single-track clip covering [0, duration]."""
    clip = AnimationClip(name, duration, mode)
    clip.add_track(
        AnimationTrack(prop)
        .add_keyframe(0.0, start_val)
        .add_keyframe(duration, end_val)
    )
    return clip


def _advance(animator: SceneAnimator, target, total_dt: float, step: float = 0.05) -> None:
    """Drive *animator* forward by *total_dt* seconds in fixed *step* increments.

    The animator caps each individual ``update`` call to 0.1 s (to protect
    against large real-time stalls), so tests that want to simulate several
    seconds of elapsed time must call it repeatedly in small increments.
    """
    remaining = total_dt
    while remaining > 1e-9:
        dt = min(remaining, step)
        animator.update(dt, target)
        remaining -= dt


class _MockTarget:
    """Minimal set_property / get_property target for animator tests."""

    def __init__(self):
        self._props: dict = {}

    def set_property(self, name: str, value) -> None:
        self._props[name] = value

    def get_property(self, name: str):
        return self._props.get(name)


# ===========================================================================
# AnimationEasing
# ===========================================================================

class TestAnimationEasing(unittest.TestCase):

    def test_linear_endpoints(self):
        self.assertAlmostEqual(AnimationEasing.LINEAR.apply(0.0), 0.0)
        self.assertAlmostEqual(AnimationEasing.LINEAR.apply(1.0), 1.0)

    def test_linear_midpoint(self):
        self.assertAlmostEqual(AnimationEasing.LINEAR.apply(0.5), 0.5)

    def test_ease_in_starts_slow(self):
        # Quadratic — value at 0.5 should be less than 0.5 (slower start)
        self.assertLess(AnimationEasing.EASE_IN.apply(0.5), 0.5)

    def test_ease_in_endpoints(self):
        self.assertAlmostEqual(AnimationEasing.EASE_IN.apply(0.0), 0.0)
        self.assertAlmostEqual(AnimationEasing.EASE_IN.apply(1.0), 1.0)

    def test_ease_out_ends_slow(self):
        # Deceleration — value at 0.5 should be greater than 0.5 (quicker start)
        self.assertGreater(AnimationEasing.EASE_OUT.apply(0.5), 0.5)

    def test_ease_out_endpoints(self):
        self.assertAlmostEqual(AnimationEasing.EASE_OUT.apply(0.0), 0.0)
        self.assertAlmostEqual(AnimationEasing.EASE_OUT.apply(1.0), 1.0)

    def test_ease_in_out_symmetric(self):
        e = AnimationEasing.EASE_IN_OUT
        self.assertAlmostEqual(e.apply(0.5), 0.5, places=6)
        # Symmetric: apply(t) + apply(1-t) == 1
        for t in (0.1, 0.25, 0.75, 0.9):
            self.assertAlmostEqual(e.apply(t) + e.apply(1.0 - t), 1.0, places=6)

    def test_ease_in_out_endpoints(self):
        self.assertAlmostEqual(AnimationEasing.EASE_IN_OUT.apply(0.0), 0.0)
        self.assertAlmostEqual(AnimationEasing.EASE_IN_OUT.apply(1.0), 1.0)

    def test_sine_midpoint(self):
        self.assertAlmostEqual(AnimationEasing.SINE.apply(0.5), 0.5, places=6)

    def test_sine_endpoints(self):
        self.assertAlmostEqual(AnimationEasing.SINE.apply(0.0), 0.0)
        self.assertAlmostEqual(AnimationEasing.SINE.apply(1.0), 1.0)

    def test_clamps_below_zero(self):
        self.assertAlmostEqual(AnimationEasing.LINEAR.apply(-1.0), 0.0)

    def test_clamps_above_one(self):
        self.assertAlmostEqual(AnimationEasing.LINEAR.apply(2.0), 1.0)


# ===========================================================================
# AnimationTrack
# ===========================================================================

class TestAnimationTrack(unittest.TestCase):

    def _linear_track(self, start=0.0, end=100.0, t_start=0.0, t_end=1.0) -> AnimationTrack:
        return (
            AnimationTrack("x", easing=AnimationEasing.LINEAR)
            .add_keyframe(t_start, start)
            .add_keyframe(t_end, end)
        )

    def test_empty_track_returns_zero(self):
        track = AnimationTrack("x")
        self.assertEqual(track.sample(0.5), 0.0)

    def test_single_keyframe_always_returns_its_value(self):
        track = AnimationTrack("x")
        track.add_keyframe(0.0, 42.0)
        self.assertEqual(track.sample(0.0), 42.0)
        self.assertEqual(track.sample(999.0), 42.0)

    def test_before_first_keyframe_returns_first_value(self):
        track = self._linear_track()
        self.assertAlmostEqual(track.sample(-1.0), 0.0)

    def test_after_last_keyframe_returns_last_value(self):
        track = self._linear_track()
        self.assertAlmostEqual(track.sample(100.0), 100.0)

    def test_linear_interpolation_midpoint(self):
        track = self._linear_track(start=0.0, end=100.0, t_start=0.0, t_end=1.0)
        self.assertAlmostEqual(track.sample(0.5), 50.0)

    def test_linear_interpolation_quarter(self):
        track = self._linear_track(start=0.0, end=100.0, t_start=0.0, t_end=1.0)
        self.assertAlmostEqual(track.sample(0.25), 25.0)

    def test_keyframes_added_out_of_order_are_sorted(self):
        track = AnimationTrack("x", easing=AnimationEasing.LINEAR)
        track.add_keyframe(1.0, 100.0)
        track.add_keyframe(0.0, 0.0)
        # Mid-point interpolation should still work correctly despite insertion order
        self.assertAlmostEqual(track.sample(0.5), 50.0)

    def test_multiple_segments(self):
        # 0→0 at t=0, 0→50 at t=0.5, 50→100 at t=1.0
        track = AnimationTrack("x", easing=AnimationEasing.LINEAR)
        track.add_keyframe(0.0, 0.0)
        track.add_keyframe(0.5, 50.0)
        track.add_keyframe(1.0, 100.0)
        self.assertAlmostEqual(track.sample(0.25), 25.0)
        self.assertAlmostEqual(track.sample(0.75), 75.0)

    def test_add_keyframe_returns_self(self):
        track = AnimationTrack("x")
        result = track.add_keyframe(0.0, 0.0)
        self.assertIs(result, track)

    def test_ease_in_out_applied(self):
        track = AnimationTrack("x", easing=AnimationEasing.EASE_IN_OUT)
        track.add_keyframe(0.0, 0.0).add_keyframe(1.0, 100.0)
        # At midpoint EASE_IN_OUT value == 50 (symmetric)
        self.assertAlmostEqual(track.sample(0.5), 50.0, places=4)
        # At t=0.25 the eased value should be less than a linear 25.0 (slow start)
        self.assertLess(track.sample(0.25), 25.0)

    def test_zero_length_segment_first_value_returned(self):
        # When two keyframes share the same time, the sample(t) condition
        # `t <= kfs[0].time` fires for t == kfs[0].time, so the first
        # keyframe's value is returned — this is well-defined and expected.
        track = AnimationTrack("x", easing=AnimationEasing.LINEAR)
        track.add_keyframe(0.5, 10.0)
        track.add_keyframe(0.5, 20.0)
        self.assertAlmostEqual(track.sample(0.5), 10.0)


# ===========================================================================
# AnimationClip
# ===========================================================================

class TestAnimationClip(unittest.TestCase):

    def test_name_and_duration(self):
        clip = AnimationClip("my_clip", 2.5)
        self.assertEqual(clip.name, "my_clip")
        self.assertAlmostEqual(clip.duration, 2.5)

    def test_minimum_duration_clamped(self):
        clip = AnimationClip("c", 0.0)
        self.assertGreater(clip.duration, 0.0)

    def test_default_mode_is_once(self):
        clip = AnimationClip("c", 1.0)
        self.assertEqual(clip.mode, AnimationMode.ONCE)

    def test_mode_stored(self):
        clip = AnimationClip("c", 1.0, mode=AnimationMode.LOOP)
        self.assertEqual(clip.mode, AnimationMode.LOOP)

    def test_add_track_returns_self(self):
        clip = AnimationClip("c", 1.0)
        result = clip.add_track(AnimationTrack("x"))
        self.assertIs(result, clip)

    def test_tracks_property_returns_copy(self):
        clip = AnimationClip("c", 1.0)
        track = AnimationTrack("x")
        clip.add_track(track)
        tracks = clip.tracks
        tracks.clear()
        # Original internal list unchanged
        self.assertEqual(len(clip.tracks), 1)

    def test_sample_all_returns_all_tracks(self):
        clip = AnimationClip("c", 1.0)
        clip.add_track(AnimationTrack("x", easing=AnimationEasing.LINEAR)
                       .add_keyframe(0.0, 0.0).add_keyframe(1.0, 10.0))
        clip.add_track(AnimationTrack("y", easing=AnimationEasing.LINEAR)
                       .add_keyframe(0.0, 5.0).add_keyframe(1.0, 15.0))
        result = clip.sample_all(0.5)
        self.assertAlmostEqual(result["x"], 5.0)
        self.assertAlmostEqual(result["y"], 10.0)

    def test_sample_all_empty_clip(self):
        clip = AnimationClip("c", 1.0)
        self.assertEqual(clip.sample_all(0.5), {})


# ===========================================================================
# SceneAnimator — clip management
# ===========================================================================

class TestSceneAnimatorClipManagement(unittest.TestCase):

    def setUp(self):
        self.animator = SceneAnimator()
        self.clip = _make_clip("move", 1.0)

    def test_initial_state(self):
        self.assertFalse(self.animator.is_playing)
        self.assertIsNone(self.animator.active_clip)
        self.assertEqual(self.animator.clip_names, [])

    def test_add_clip(self):
        self.animator.add_clip(self.clip)
        self.assertIn("move", self.animator.clip_names)

    def test_get_clip(self):
        self.animator.add_clip(self.clip)
        self.assertIs(self.animator.get_clip("move"), self.clip)

    def test_get_clip_missing(self):
        self.assertIsNone(self.animator.get_clip("no_such"))

    def test_remove_clip(self):
        self.animator.add_clip(self.clip)
        self.animator.remove_clip("move")
        self.assertNotIn("move", self.animator.clip_names)

    def test_remove_active_clip_stops_playback(self):
        self.animator.add_clip(self.clip)
        self.animator.play("move")
        self.animator.remove_clip("move")
        self.assertFalse(self.animator.is_playing)
        self.assertIsNone(self.animator.active_clip)

    def test_remove_nonexistent_clip_is_safe(self):
        self.animator.remove_clip("ghost")  # should not raise


# ===========================================================================
# SceneAnimator — playback control
# ===========================================================================

class TestSceneAnimatorPlayback(unittest.TestCase):

    def setUp(self):
        self.animator = SceneAnimator()
        self.clip = _make_clip("move", 1.0)
        self.animator.add_clip(self.clip)
        self.target = _MockTarget()

    def test_play_starts_playing(self):
        self.animator.play("move")
        self.assertTrue(self.animator.is_playing)
        self.assertEqual(self.animator.active_clip, "move")

    def test_play_unknown_clip_does_not_start(self):
        self.animator.play("ghost")
        self.assertFalse(self.animator.is_playing)

    def test_play_resets_time_by_default(self):
        self.animator.play("move")
        self.animator.update(0.5, self.target)
        self.animator.play("move", reset=True)
        # After reset, update(0) pushes start value
        self.animator.update(0.0, self.target)
        self.assertAlmostEqual(self.target.get_property("x"), 0.0, places=3)  # type: ignore

    def test_play_no_reset_continues_from_current_time(self):
        self.animator.play("move")
        self.animator.update(0.5, self.target)
        mid_val = self.target.get_property("x")
        self.animator.play("move", reset=False)
        self.animator.update(0.0, self.target)
        # Value should stay near mid_val (no jump back to start)
        self.assertAlmostEqual(self.target.get_property("x"), mid_val, places=1)  # type: ignore

    def test_stop_resets_playing_and_time(self):
        self.animator.play("move")
        self.animator.update(0.5, self.target)
        self.animator.stop()
        self.assertFalse(self.animator.is_playing)

    def test_pause_halts_without_reset(self):
        self.animator.play("move")
        self.animator.update(0.4, self.target)
        paused_val = self.target.get_property("x")
        self.animator.pause()
        self.assertFalse(self.animator.is_playing)
        # Value unchanged after pause
        self.animator.update(0.4, self.target)
        self.assertAlmostEqual(self.target.get_property("x"), paused_val, places=3)  # type: ignore

    def test_resume_continues_playback(self):
        self.animator.play("move")
        self.animator.update(0.4, self.target)
        self.animator.pause()
        self.animator.resume()
        self.assertTrue(self.animator.is_playing)


# ===========================================================================
# SceneAnimator — ONCE mode
# ===========================================================================

class TestSceneAnimatorOnce(unittest.TestCase):

    def setUp(self):
        self.animator = SceneAnimator()
        self.clip = _make_clip("move", 1.0, AnimationMode.ONCE, "x", 0.0, 100.0)
        self.animator.add_clip(self.clip)
        self.target = _MockTarget()

    def test_value_at_start(self):
        self.animator.play("move")
        self.animator.update(0.0, self.target)
        self.assertAlmostEqual(self.target.get_property("x"), 0.0, places=3)  # type: ignore

    def test_value_at_midpoint(self):
        self.animator.play("move")
        _advance(self.animator, self.target, 0.5)
        self.assertAlmostEqual(self.target.get_property("x"), 50.0, places=2)  # type: ignore

    def test_stops_at_end(self):
        self.animator.play("move")
        _advance(self.animator, self.target, 1.5)
        self.assertFalse(self.animator.is_playing)
        self.assertAlmostEqual(self.target.get_property("x"), 100.0, places=2)  # type: ignore

    def test_on_complete_callback_fires_once(self):
        cb = MagicMock()
        self.animator.add_on_complete(cb)
        self.animator.play("move")
        _advance(self.animator, self.target, 1.5)
        cb.assert_called_once()

    def test_on_complete_not_fired_before_end(self):
        cb = MagicMock()
        self.animator.add_on_complete(cb)
        self.animator.play("move")
        _advance(self.animator, self.target, 0.5)
        cb.assert_not_called()


# ===========================================================================
# SceneAnimator — LOOP mode
# ===========================================================================

class TestSceneAnimatorLoop(unittest.TestCase):

    def setUp(self):
        self.animator = SceneAnimator()
        self.clip = _make_clip("move", 1.0, AnimationMode.LOOP, "x", 0.0, 100.0)
        self.animator.add_clip(self.clip)
        self.target = _MockTarget()

    def test_still_playing_after_one_cycle(self):
        self.animator.play("move")
        _advance(self.animator, self.target, 1.1)
        self.assertTrue(self.animator.is_playing)

    def test_wraps_back_near_start(self):
        self.animator.play("move")
        # Just past the end — should wrap to 0.1 s into clip → 10 units
        _advance(self.animator, self.target, 1.1)
        self.assertAlmostEqual(self.target.get_property("x"), 10.0, places=0)  # type: ignore

    def test_multiple_loops(self):
        self.animator.play("move")
        # 3.5 cycles → 0.5 into clip → 50 units
        _advance(self.animator, self.target, 3.5)
        self.assertAlmostEqual(self.target.get_property("x"), 50.0, places=0)  # type: ignore


# ===========================================================================
# SceneAnimator — PING_PONG mode
# ===========================================================================

class TestSceneAnimatorPingPong(unittest.TestCase):

    def setUp(self):
        self.animator = SceneAnimator()
        self.clip = _make_clip("move", 1.0, AnimationMode.PING_PONG, "x", 0.0, 100.0)
        self.animator.add_clip(self.clip)
        self.target = _MockTarget()

    def test_still_playing_after_forward_pass(self):
        self.animator.play("move")
        _advance(self.animator, self.target, 1.1)
        self.assertTrue(self.animator.is_playing)

    def test_reverses_after_first_pass(self):
        self.animator.play("move")
        # At 1.5 s: forward pass ends at 1.0, reflects to 0.5 back → 50 units
        _advance(self.animator, self.target, 1.5)
        self.assertAlmostEqual(self.target.get_property("x"), 50.0, places=0)  # type: ignore

    def test_value_at_end_of_forward_pass(self):
        self.animator.play("move")
        _advance(self.animator, self.target, 1.0)
        self.assertAlmostEqual(self.target.get_property("x"), 100.0, places=0)  # type: ignore

    def test_returns_to_start_after_full_ping_pong_cycle(self):
        self.animator.play("move")
        # Forward 1.0 s + backward 1.0 s = 2.0 s total → back at 0
        _advance(self.animator, self.target, 2.0)
        self.assertAlmostEqual(self.target.get_property("x"), 0.0, places=0)  # type: ignore


# ===========================================================================
# SceneAnimator — dt capping
# ===========================================================================

class TestSceneAnimatorDtCap(unittest.TestCase):

    def test_single_update_capped_to_point_one_seconds(self):
        """A single update call advances time by at most 0.1 s regardless of dt."""
        animator = SceneAnimator()
        # 10-second clip; one huge update should only advance 0.1 s → 1 unit
        clip = _make_clip("c", 10.0, AnimationMode.LOOP, "x", 0.0, 100.0)
        animator.add_clip(clip)
        target = _MockTarget()
        animator.play("c")
        animator.update(999.0, target)
        self.assertAlmostEqual(target.get_property("x"), 1.0, places=1)  # type: ignore


# ===========================================================================
# SceneAnimator — no active clip / not playing guard
# ===========================================================================

class TestSceneAnimatorGuards(unittest.TestCase):

    def test_update_returns_false_when_not_playing(self):
        animator = SceneAnimator()
        target = _MockTarget()
        result = animator.update(0.1, target)
        self.assertFalse(result)

    def test_update_returns_false_after_clip_removed(self):
        animator = SceneAnimator()
        clip = _make_clip()
        animator.add_clip(clip)
        animator.play("clip")
        animator.remove_clip("clip")
        target = _MockTarget()
        result = animator.update(0.1, target)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
