"""Top-down piston composite scene object.

A piston consists of two components:

* **rod** — a rectangle that grows/shrinks along the piston axis.
* **head** — a square that sits flush at the tip of the rod.

The :attr:`extended` property drives the animation:

* ``True``  → plays the ``"extend"`` clip (rod grows, head moves outward).
* ``False`` → plays the ``"retract"`` clip (rod shrinks, head moves inward).

The piston can face any of the four cardinal directions.  The composite's
origin is the **base** (mounting point) of the piston:

    RIGHT  →  rod grows toward +X
    LEFT   →  rod grows toward -X
    DOWN   →  rod grows toward +Y  (screen-down)
    UP     →  rod grows toward -Y  (screen-up)

Example::

    piston = PistonSceneObject.create(
        name="Clamp",
        x=200.0,
        y=150.0,
        direction=PistonDirection.RIGHT,
        retracted_length=20.0,
        extended_length=60.0,
    )
    scene.add_scene_object(piston)

    # Extend the piston (triggers the "extend" animation):
    piston.extended = True

    # In the render / update loop:
    piston.update(dt)
"""
from __future__ import annotations

from enum import Enum, auto

from pyrox.interfaces import IBasePhysicsBody
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.scene.animation import (
    AnimationClip,
    AnimationEasing,
    AnimationMode,
    AnimationTrack,
)
from pyrox.models.scene.compositesceneobject import CompositeSceneObject
from pyrox.models.scene.sceneobject import SceneObject
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate

SCENE_OBJECT_TYPE_PISTON = "piston"
SCENE_OBJECT_TEMPLATE_NAME_PISTON = "Top-Down Piston"


class PistonDirection(Enum):
    """Direction in which the piston rod extends from its base."""

    RIGHT = auto()  # rod grows toward +X
    LEFT = auto()   # rod grows toward −X
    DOWN = auto()   # rod grows toward +Y
    UP = auto()     # rod grows toward −Y


class PistonSceneObject(CompositeSceneObject):
    """Top-down composite piston with animated rod and head.

    The composite's origin is the **base** (mounting point) of the piston.
    The two child components are:

    * ``"rod"``  — a rectangle aligned along the piston axis whose length
      is driven by the extend/retract animations.
    * ``"head"`` — a square that follows the tip of the rod automatically
      every :meth:`update` call.

    Both components are centred on the perpendicular axis relative to the
    piston head size, so the rod appears centred inside the head footprint.

    Attributes:
        CLIP_EXTEND:  Name of the extend animation clip registered on the rod.
        CLIP_RETRACT: Name of the retract animation clip registered on the rod.
    """

    CLIP_EXTEND = "extend"
    CLIP_RETRACT = "retract"

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        direction: PistonDirection = PistonDirection.RIGHT,
        retracted_length: float = 20.0,
        extended_length: float = 60.0,
        rod_thickness: float = 8.0,
        head_size: float = 14.0,
        animation_duration: float = 0.5,
        rod_color: str = "#888888",
        head_color: str = "#555555",
        layer: int = 0,
    ) -> None:
        """Initialise the piston with the given parameters.

        .. tip::
            Prefer :meth:`create` when you do not need to supply a custom
            physics body — it handles body sizing automatically.

        Args:
            name:               Identifier for this piston.
            physics_body:       Physics body for the composite (defines world
                                position and overall bounding box).
            direction:          Axis and sense the rod extends toward.
            retracted_length:   Rod length when fully retracted.
            extended_length:    Rod length when fully extended.
            rod_thickness:      Cross-section size of the rod rectangle.
            head_size:          Width *and* height of the square piston head.
            animation_duration: Seconds for a full extend or retract stroke.
            rod_color:          CSS hex fill colour for the rod.
            head_color:         CSS hex fill colour for the head.
            layer:              Render layer (z-order).
        """
        super().__init__(
            name=name,
            physics_body=physics_body,
            scene_object_type=SCENE_OBJECT_TYPE_PISTON,
            template_name=SCENE_OBJECT_TEMPLATE_NAME_PISTON,
            layer=layer,
        )

        self._direction = direction
        self._retracted_length = float(retracted_length)
        self._extended_length = float(extended_length)
        self._rod_thickness = float(rod_thickness)
        self._head_size = float(head_size)
        self._extended = False
        self._is_horizontal = direction in (PistonDirection.RIGHT, PistonDirection.LEFT)

        # ------------------------------------------------------------------
        # Rod component
        # ------------------------------------------------------------------
        rod_w = self._retracted_length if self._is_horizontal else self._rod_thickness
        rod_h = self._rod_thickness if self._is_horizontal else self._retracted_length

        rod_body = BasePhysicsBody(
            name=f"{name}_rod",
            template_name='Base Physics Body',
            width=rod_w,
            height=rod_h,
        )
        self._rod = SceneObject(
            name=f"{name}_rod",
            scene_object_type="piston_rod",
            physics_body=rod_body,
            bg_color=rod_color,
            layer=layer,
        )

        # ------------------------------------------------------------------
        # Head component
        # ------------------------------------------------------------------
        head_body = BasePhysicsBody(
            name=f"{name}_head",
            template_name='Base Physics Body',
            width=head_size,
            height=head_size,
        )
        self._head = SceneObject(
            name=f"{name}_head",
            scene_object_type="piston_head",
            physics_body=head_body,
            bg_color=head_color,
            layer=layer,
        )

        # ------------------------------------------------------------------
        # Animation clips (registered on the rod)
        # The animated property is "width" for horizontal pistons and
        # "height" for vertical pistons.
        # ------------------------------------------------------------------
        length_prop = "width" if self._is_horizontal else "height"

        extend_clip = (
            AnimationClip(self.CLIP_EXTEND, animation_duration, AnimationMode.ONCE)
            .add_track(
                AnimationTrack(length_prop, easing=AnimationEasing.EASE_IN_OUT)
                .add_keyframe(0.0, self._retracted_length)
                .add_keyframe(animation_duration, self._extended_length)
            )
        )
        retract_clip = (
            AnimationClip(self.CLIP_RETRACT, animation_duration, AnimationMode.ONCE)
            .add_track(
                AnimationTrack(length_prop, easing=AnimationEasing.EASE_IN_OUT)
                .add_keyframe(0.0, self._extended_length)
                .add_keyframe(animation_duration, self._retracted_length)
            )
        )
        self._rod.animator.add_clip(extend_clip)
        self._rod.animator.add_clip(retract_clip)

        # ------------------------------------------------------------------
        # Register components at initial (retracted) offsets
        # ------------------------------------------------------------------
        rod_ox, rod_oy = self._rod_offset(self._retracted_length)
        head_ox, head_oy = self._head_offset(self._retracted_length)
        self.add_component("rod",  self._rod,  offset_x=rod_ox,  offset_y=rod_oy)
        self.add_component("head", self._head, offset_x=head_ox, offset_y=head_oy)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def direction(self) -> PistonDirection:
        """The direction in which the piston extends."""
        return self._direction

    @property
    def extended(self) -> bool:
        """``True`` when the piston is extended (or in the process of extending)."""
        return self._extended

    @extended.setter
    def extended(self, value: bool) -> None:
        """Trigger the extend or retract animation.

        If called mid-animation the new clip starts from the current rod length
        so transitions are always smooth regardless of timing.

        Args:
            value: ``True`` to extend, ``False`` to retract.
        """
        if value == self._extended:
            return
        self._extended = value
        clip_name = self.CLIP_EXTEND if value else self.CLIP_RETRACT
        self._snap_animation_start(clip_name)
        self._rod.animator.play(clip_name)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance animations and keep the head aligned with the rod tip.

        Calls :meth:`CompositeSceneObject.update` (which ticks both the rod
        and head animators) then re-calculates component offsets based on the
        rod's current animated length.

        Args:
            dt: Elapsed wall-clock seconds since the last call.
        """
        super().update(dt)
        current_len = self._current_rod_length()
        rod_ox, rod_oy = self._rod_offset(current_len)
        head_ox, head_oy = self._head_offset(current_len)
        # Mutate in-place so existing external references to _components remain valid
        self._components["rod"] = (self._rod, rod_ox, rod_oy)
        self._components["head"] = (self._head, head_ox, head_oy)

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        direction: PistonDirection = PistonDirection.RIGHT,
        retracted_length: float = 20.0,
        extended_length: float = 60.0,
        rod_thickness: float = 8.0,
        head_size: float = 14.0,
        animation_duration: float = 0.5,
        rod_color: str = "#888888",
        head_color: str = "#555555",
        layer: int = 0,
        body_dict: dict | None = None,
        **kwargs,
    ) -> "PistonSceneObject":
        """Create a :class:`PistonSceneObject` without manually building a physics body.

        The composite bounding box is sized to encompass the fully-extended
        piston, so scene-level hit-testing covers the entire range of motion.

        Args:
            name:               Identifier for this piston.
            x:                  Scene X of the piston base (mounting point).
            y:                  Scene Y of the piston base (mounting point).
            direction:          Axis and sense the rod extends toward.
            retracted_length:   Rod length when fully retracted.
            extended_length:    Rod length when fully extended.
            rod_thickness:      Cross-section size of the rod rectangle.
            head_size:          Width *and* height of the square piston head.
            animation_duration: Seconds for a full extend or retract stroke.
            rod_color:          CSS hex fill colour for the rod.
            head_color:         CSS hex fill colour for the head.
            layer:              Render layer (z-order).

        Returns:
            A fully-initialised :class:`PistonSceneObject`.
        """
        body_dict = body_dict or kwargs.get("body")
        if body_dict:
            body = BasePhysicsBody.from_dict(body_dict)

        else:
            is_horizontal = direction in (PistonDirection.RIGHT, PistonDirection.LEFT)
            if is_horizontal:
                body_w = extended_length + head_size
                body_h = head_size
            else:
                body_w = head_size
                body_h = extended_length + head_size
            body = BasePhysicsBody(
                name=f"{name}_body",
                template_name='Base Physics Body',
                x=float(x),
                y=float(y),
                width=body_w,
                height=body_h,
            )
        return cls(
            name=name,
            physics_body=body,
            direction=direction,
            retracted_length=retracted_length,
            extended_length=extended_length,
            rod_thickness=rod_thickness,
            head_size=head_size,
            animation_duration=animation_duration,
            rod_color=rod_color,
            head_color=head_color,
            layer=layer,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super()._compile_properties()
        self._properties.update({
            "direction": self._direction.name,
            "extended": self._extended,
            "retracted_length": self._retracted_length,
            "extended_length": self._extended_length,
            "rod_thickness": self._rod_thickness,
            "head_size": self._head_size,
        })

    def _current_rod_length(self) -> float:
        """Return the rod's current animated length (width or height)."""
        return self._rod.width if self._is_horizontal else self._rod.height

    def _rod_offset(self, current_length: float) -> tuple[float, float]:
        """Composite-relative offset for the rod's top-left corner.

        The rod is centred on the perpendicular axis within the head footprint.

        Args:
            current_length: Current rod length (animated).

        Returns:
            ``(offset_x, offset_y)`` relative to the composite origin.
        """
        # Centre the rod cross-section within the head square
        perp_offset = (self._head_size - self._rod_thickness) / 2.0
        match self._direction:
            case PistonDirection.RIGHT:
                return (0.0, perp_offset)
            case PistonDirection.LEFT:
                return (-current_length, perp_offset)
            case PistonDirection.DOWN:
                return (perp_offset, 0.0)
            case PistonDirection.UP:
                return (perp_offset, -current_length)

    def _head_offset(self, current_length: float) -> tuple[float, float]:
        """Composite-relative offset for the head's top-left corner.

        The head always sits flush at the tip of the rod.

        Args:
            current_length: Current rod length (animated).

        Returns:
            ``(offset_x, offset_y)`` relative to the composite origin.
        """
        hs = self._head_size
        match self._direction:
            case PistonDirection.RIGHT:
                return (current_length, 0.0)
            case PistonDirection.LEFT:
                return (-hs, 0.0)
            case PistonDirection.DOWN:
                return (0.0, current_length)
            case PistonDirection.UP:
                return (0.0, -hs)

    def _snap_animation_start(self, clip_name: str) -> None:
        """Update the first keyframe of *clip_name* to the current rod length.

        This ensures smooth mid-stroke transitions — the new animation always
        starts from where the rod currently is rather than jumping to the
        clip's original start value.

        Args:
            clip_name: ``CLIP_EXTEND`` or ``CLIP_RETRACT``.
        """
        clip = self._rod.animator.get_clip(clip_name)
        if clip is None:
            return
        current_len = self._current_rod_length()
        # clip.tracks returns a shallow-copy list; the AnimationTrack objects
        # are shared references so mutating keyframes[0].value is safe.
        for track in clip.tracks:
            if track.keyframes:
                track.keyframes[0].value = current_len


SceneObjectFactory.register_template(
    "Top-Down Piston",
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME_PISTON,
        scene_object_class=PistonSceneObject,
        description="Composite piston with animated rod and head (top-down view)",
        factory_func=PistonSceneObject.create,
        default_kwargs={
            "name": SCENE_OBJECT_TEMPLATE_NAME_PISTON,
            "direction": PistonDirection.RIGHT,
            "retracted_length": 20.0,
            "extended_length": 60.0,
            "rod_thickness": 8.0,
            "head_size": 14.0,
            "animation_duration": 1.0,
            "rod_color": "#888888",
            "head_color": "#555555",
            "layer": 0,
        },
        category="Machinery",
    )
)
