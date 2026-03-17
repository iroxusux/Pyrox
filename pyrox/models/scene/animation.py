"""Animation system for scene objects.

Provides keyframe-based tweening animations for SceneObject properties.
Designed for performance: low overhead, pure Python interpolation,
no heavy external dependencies.

Example — gate swing open::

    clip = AnimationClip("gate_open", duration=1.0, mode=AnimationMode.ONCE)
    clip.add_track(
        AnimationTrack("yaw", easing=AnimationEasing.EASE_IN_OUT)
        .add_keyframe(0.0, 0.0)
        .add_keyframe(1.0, 90.0)
    )
    gate.animator.add_clip(clip)
    gate.animator.play("gate_open")

Example — piston (ping-pong)::

    clip = AnimationClip("piston", duration=0.8, mode=AnimationMode.PING_PONG)
    clip.add_track(
        AnimationTrack("x", easing=AnimationEasing.EASE_IN_OUT)
        .add_keyframe(0.0, 0.0)
        .add_keyframe(0.8, 50.0)
    )
    piston.animator.add_clip(clip)
    piston.animator.play("piston")
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional


class AnimationEasing(Enum):
    """Easing functions applied to each keyframe segment."""

    LINEAR = auto()
    EASE_IN = auto()       # Quadratic acceleration
    EASE_OUT = auto()      # Quadratic deceleration
    EASE_IN_OUT = auto()   # Smooth-step (cubic)
    SINE = auto()          # Sinusoidal

    def apply(self, t: float) -> float:
        """Map a normalised time *t* ∈ [0, 1] through this easing curve."""
        t = max(0.0, min(1.0, t))
        match self:
            case AnimationEasing.LINEAR:
                return t
            case AnimationEasing.EASE_IN:
                return t * t
            case AnimationEasing.EASE_OUT:
                return 1.0 - (1.0 - t) * (1.0 - t)
            case AnimationEasing.EASE_IN_OUT:
                return t * t * (3.0 - 2.0 * t)
            case AnimationEasing.SINE:
                return (1.0 - math.cos(t * math.pi)) / 2.0
            case _:
                return t


class AnimationMode(Enum):
    """Playback behaviour when a clip reaches its end."""

    ONCE = auto()       # Play once then stop at the last frame
    LOOP = auto()       # Jump back to time 0 and repeat
    PING_PONG = auto()  # Play forward then backward, alternating


@dataclass
class Keyframe:
    """A single (time, value) control point on an animation track."""

    time: float   # Seconds from clip start
    value: float  # Property value at this instant


@dataclass
class AnimationTrack:
    """Animates a single named property through a sequence of keyframes.

    Keyframes are kept sorted by time.  Between adjacent keyframes the value
    is interpolated using the track's :class:`AnimationEasing`.

    Example::

        track = AnimationTrack("yaw", easing=AnimationEasing.EASE_IN_OUT)
        track.add_keyframe(0.0, 0.0)
        track.add_keyframe(1.0, 90.0)
    """

    property: str
    keyframes: list[Keyframe] = field(default_factory=list)
    easing: AnimationEasing = AnimationEasing.LINEAR

    def add_keyframe(self, time: float, value: float) -> 'AnimationTrack':
        """Append a keyframe, maintaining sorted order.  Returns *self* for chaining."""
        self.keyframes.append(Keyframe(time, value))
        self.keyframes.sort(key=lambda k: k.time)
        return self

    def sample(self, t: float) -> float:
        """Return the interpolated value at time *t* seconds."""
        kfs = self.keyframes
        if not kfs:
            return 0.0
        if len(kfs) == 1 or t <= kfs[0].time:
            return kfs[0].value
        if t >= kfs[-1].time:
            return kfs[-1].value

        for i in range(len(kfs) - 1):
            a, b = kfs[i], kfs[i + 1]
            if a.time <= t <= b.time:
                seg = b.time - a.time
                if seg <= 0.0:
                    return b.value
                local_t = (t - a.time) / seg
                eased = self.easing.apply(local_t)
                return a.value + (b.value - a.value) * eased

        return kfs[-1].value


class AnimationClip:
    """A named clip containing one or more :class:`AnimationTrack` instances.

    Example — gate swing::

        clip = AnimationClip("gate_open", duration=1.0, mode=AnimationMode.ONCE)
        clip.add_track(
            AnimationTrack("yaw", easing=AnimationEasing.EASE_IN_OUT)
            .add_keyframe(0.0, 0.0)
            .add_keyframe(1.0, 90.0)
        )

    Example — piston::

        clip = AnimationClip("piston", duration=0.8, mode=AnimationMode.PING_PONG)
        clip.add_track(
            AnimationTrack("x")
            .add_keyframe(0.0, 0.0)
            .add_keyframe(0.8, 50.0)
        )
    """

    def __init__(
        self,
        name: str,
        duration: float,
        mode: AnimationMode = AnimationMode.ONCE,
    ) -> None:
        self.name = name
        self.duration = max(duration, 0.001)
        self.mode = mode
        self._tracks: list[AnimationTrack] = []

    def add_track(self, track: AnimationTrack) -> 'AnimationClip':
        """Attach a track to this clip.  Returns *self* for chaining."""
        self._tracks.append(track)
        return self

    @property
    def tracks(self) -> list[AnimationTrack]:
        return list(self._tracks)

    def sample_all(self, t: float) -> dict[str, float]:
        """Return ``{property: value}`` for every track at time *t*."""
        return {track.property: track.sample(t) for track in self._tracks}


class SceneAnimator:
    """Manages and ticks animations attached to a :class:`SceneObject`.

    Each SceneObject owns one ``SceneAnimator``.  Register clips with
    :meth:`add_clip`, start playback with :meth:`play`, then call
    :meth:`update` each frame to advance the playhead and push property
    values onto the target object.

    Example::

        obj.animator.add_clip(gate_open_clip)
        obj.animator.play("gate_open")

        # In game / render loop:
        obj.update(dt)  # SceneObject.update delegates to animator.update
    """

    def __init__(self) -> None:
        self._clips: dict[str, AnimationClip] = {}
        self._active_clip: Optional[str] = None
        self._time: float = 0.0
        self._playing: bool = False
        self._reversed: bool = False          # Used by PING_PONG mode
        self._on_complete: list[Callable] = []

    # ------------------------------------------------------------------
    # Clip management
    # ------------------------------------------------------------------

    def add_clip(self, clip: AnimationClip) -> None:
        """Register *clip* by its name."""
        self._clips[clip.name] = clip

    def remove_clip(self, name: str) -> None:
        """Unregister *name*, stopping playback if it is currently active."""
        self._clips.pop(name, None)
        if self._active_clip == name:
            self.stop()
            self._active_clip = None

    def get_clip(self, name: str) -> Optional[AnimationClip]:
        """Return the :class:`AnimationClip` registered as *name*, or ``None``."""
        return self._clips.get(name)

    @property
    def clip_names(self) -> list[str]:
        """Names of all registered clips."""
        return list(self._clips.keys())

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def play(self, name: str, reset: bool = True) -> None:
        """Start playing *name*.

        Args:
            name:  Clip name — must have been added with :meth:`add_clip`.
            reset: If ``True`` (default) restart from time 0.
        """
        if name not in self._clips:
            return
        if reset or self._active_clip != name:
            self._time = 0.0
            self._reversed = False
        self._active_clip = name
        self._playing = True

    def stop(self) -> None:
        """Stop and rewind to the start."""
        self._playing = False
        self._time = 0.0
        self._reversed = False

    def pause(self) -> None:
        """Pause without resetting the playhead."""
        self._playing = False

    def resume(self) -> None:
        """Resume a paused animation from the current position."""
        if self._active_clip and self._active_clip in self._clips:
            self._playing = True

    @property
    def is_playing(self) -> bool:
        """``True`` while a clip is actively playing."""
        return self._playing

    @property
    def active_clip(self) -> Optional[str]:
        """Name of the currently active clip, or ``None``."""
        return self._active_clip

    def add_on_complete(self, callback: Callable) -> None:
        """Register *callback* to be called when a ``ONCE``-mode clip finishes."""
        self._on_complete.append(callback)

    # ------------------------------------------------------------------
    # Update (called each frame)
    # ------------------------------------------------------------------

    def update(self, dt: float, target: Any) -> bool:
        """Advance the playhead by *dt* seconds and apply values to *target*.

        Args:
            dt:     Elapsed wall-clock seconds since the last call.
                    Values larger than ~0.1 s are clamped to avoid large
                    position jumps after a stall.
            target: An object that exposes ``set_property(name, value)``,
                    typically a :class:`~pyrox.models.scene.SceneObject`.

        Returns:
            ``True`` if at least one property value was written to *target*.
        """
        if not self._playing or not self._active_clip:
            return False

        clip = self._clips.get(self._active_clip)
        if clip is None:
            return False

        dt = min(dt, 0.1)  # Cap to avoid large jumps after a stall

        # Advance the playhead
        if self._reversed:
            self._time -= dt
        else:
            self._time += dt

        # Handle end-of-clip behaviour
        match clip.mode:
            case AnimationMode.ONCE:
                if self._time >= clip.duration:
                    self._time = clip.duration
                    self._playing = False
                    for prop, val in clip.sample_all(self._time).items():
                        target.set_property(prop, val)
                    for cb in self._on_complete:
                        cb()
                    return True

            case AnimationMode.LOOP:
                while self._time >= clip.duration:
                    self._time -= clip.duration

            case AnimationMode.PING_PONG:
                if not self._reversed and self._time >= clip.duration:
                    # Reflect forward overflow back into range
                    self._time = clip.duration - (self._time - clip.duration)
                    self._reversed = True
                elif self._reversed and self._time <= 0.0:
                    # Reflect backward underflow back into range
                    self._time = -self._time
                    self._reversed = False

        for prop, val in clip.sample_all(self._time).items():
            target.set_property(prop, val)
        return True
