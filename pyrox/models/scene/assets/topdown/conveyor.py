"""Top-down conveyor composite scene object.

A conveyor consists of 3 components: a static base, an animated belt and a physics conveyor object.

The belt is a rectangle that continuously scrolls along the conveyor axis, driven by an infinite looping animation clip.

The base is a static rectangle that serves as the main physics body for the composite and defines the position and bounding for the conveyor.

The belt is a child component that sits flush on top of the base and provides the visual scrolling effect.

The physics conveyor is a transparent kinematic body that sits on top of the belt and provides the collision surface for
    dynamic objects to be pushed by the conveyor.

* **base** — a rectangle that serves as the main physics body for the composite and defines the world position
    and bounding box for the entire conveyor.

* **belt** — a rectangle that continuously scrolls along the conveyor axis, driven by an infinite looping animation clip.

* **physics conveyor** — a transparent kinematic body that sits on top of the belt and provides the collision surface for
    dynamic objects to be pushed by the conveyor.
"""
import math
from typing import Self
from pyrox.interfaces import BodyType, CardinalDirection, CollisionLayer
from pyrox.models.physics.conveyor import ConveyorBody
from pyrox.models.scene.assets.topdown._compkinemetic import ActivatableCompositeKinematicSceneObject
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate

SCENE_OBJECT_TYPE = "conveyor"
SCENE_OBJECT_TEMPLATE_NAME = "Top-Down Conveyor"


class ConveyorSceneObject(ActivatableCompositeKinematicSceneObject):
    """Top-down conveyor composite scene object.

    A conveyor consists of 3 components: a static base, an animated belt and a physics conveyor object.

    The belt is a rectangle that continuously scrolls along the conveyor axis, driven by an infinite looping animation clip.

    The base is a static rectangle that serves as the main physics body for the composite and defines the
        position and bounding for the conveyor.

    The belt is a child component that sits flush on top of the base and provides the visual scrolling effect.

    The physics conveyor is a transparent kinematic body that sits on top of the belt and provides the collision surface for
        dynamic objects to be pushed by the conveyor.

    * **base** — a rectangle that serves as the main physics body for the composite and defines the world position
        and bounding box for the entire conveyor.

    * **belt** — a rectangle that continuously scrolls along the conveyor axis, driven by an infinite looping animation clip.

    * **physics conveyor** — a transparent kinematic body that sits on top of the belt and provides the collision surface for
        dynamic objects to be pushed by the conveyor.
    """

    def __init__(
        self,
        name: str,
        physics_body: ConveyorBody,
        description: str = "",
        direction: CardinalDirection = CardinalDirection.RIGHT,
        conveyor_length: float = 60.0,
        conveyor_width: float = 20.0,
        conveyor_speed: float = 30.0,
        conveyor_color: str = "#888888",
        belt_length: float = 10.0,  # A small rectangle that serves as the repeating pattern for the belt animation
        belt_color: str = "#555555",
        layer: int = 0,
        properties: dict = dict(),
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
        **kwargs,
    ) -> None:
        """Initialize the conveyor scene object with the given parameters:

        Args:
            name:              Identifier for this conveyor.
            physics_body:      The main physics body for the conveyor (the base).
            description:       Optional text description of the conveyor.
            direction:         Axis and sense the conveyor moves towards.
            conveyor_length:   Length of the conveyor along its movement axis.
            conveyor_width:    Width of the conveyor perpendicular to its movement axis.
            conveyor_speed:    Speed at which the belt moves (units per second).
            conveyor_color:    CSS hex fill colour for the conveyor base.
            belt_color:        CSS hex fill colour for the moving belt.
            layer:             Render layer (z-order).
            properties:        Additional custom properties as a dictionary.
            id:                Optional unique identifier for serialization.
            group_id:          Optional group identifier for grouping related objects.
            tags:              Optional list of string tags for categorization.
        """
        self._conveyor_length = conveyor_length
        self._conveyor_width = conveyor_width
        self._conveyor_speed = conveyor_speed
        self._conveyor_color = conveyor_color
        self._belt_color = belt_color
        self._belt_length = belt_length
        # Slice for size padding for visual distinction between the belt and base (prevents z-fighting when colors are similar)
        self._belt_size_slice = 4.0
        self._belt_position = 0.0  # Current position of the belt animation (0 to belt_length)
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            scene_object_type=SCENE_OBJECT_TYPE,
            template_name=SCENE_OBJECT_TEMPLATE_NAME,
            id=id,
            group_id=group_id,
            tags=tags,
            layer=layer,
            direction=direction,
            properties=properties,
        )

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------
    def current_animator_position(self) -> float:
        """Get the current position of the belt animation (0 to belt_length)."""
        return self._belt_position

    # ------------------------------------------------------------------
    # Build Methods
    # ------------------------------------------------------------------

    def build_components(self):
        is_h = self.is_horizontal
        cross_offset = self._belt_size_slice / 2.0

        # ------------------------------------------------------------------
        # Base component — full conveyor footprint, direction-aware
        # ------------------------------------------------------------------
        base_w = self._conveyor_length if is_h else self._conveyor_width
        base_h = self._conveyor_width if is_h else self._conveyor_length
        self._base = self.create_simple_component(
            name="base",
            template_name="Base Physics Body",
            body_type=BodyType.KINEMATIC,
            width=base_w,
            height=base_h,
            collision_layer=CollisionLayer.TRANSPARENT,
            collision_mask=[],
            scene_object_type=SCENE_OBJECT_TYPE,
            bg_color=self._conveyor_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Belt stripe components — tiled along the scroll axis so the belt
        # appears continuous at all times.  Each stripe is a short marker
        # that scrolls in the conveyor direction and wraps seamlessly.
        # Stripe dimensions:
        #   along-axis  = belt_length  (the repeating mark length)
        #   cross-axis  = conveyor_width - belt_size_slice  (inset from base)
        # ------------------------------------------------------------------
        stripe_along = max(1.0, self._belt_length - self._belt_size_slice)
        stripe_cross = max(1.0, self._conveyor_width - self._belt_size_slice)
        stripe_w = stripe_along if is_h else stripe_cross
        stripe_h = stripe_cross if is_h else stripe_along

        n_stripes = max(1, math.ceil(self._conveyor_length / self._belt_length))
        self._belt_stripes: list = []
        for i in range(n_stripes):
            stripe = self.create_simple_component(
                name=f"belt_{i}",
                template_name="Base Physics Body",
                body_type=BodyType.KINEMATIC,
                width=stripe_w,
                height=stripe_h,
                collision_layer=CollisionLayer.TRANSPARENT,
                collision_mask=[],
                scene_object_type=SCENE_OBJECT_TYPE,
                bg_color=self._belt_color,
                layer=self._layer + 1,
            )
            self._belt_stripes.append(stripe)

        # ------------------------------------------------------------------
        # Physics conveyor component — full footprint, transparent, owns the
        # kinematic velocity that friction-pushes dynamic bodies on the belt.
        # ------------------------------------------------------------------
        phys_w = self._conveyor_length if is_h else self._conveyor_width - self._belt_size_slice
        phys_h = self._conveyor_width - self._belt_size_slice if is_h else self._conveyor_length
        self._physics_conveyor = self.create_simple_component(
            name="physics_conveyor",
            template_name="Top-Down Conveyor Belt",
            body_type=BodyType.KINEMATIC,
            width=phys_w,
            height=phys_h,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            scene_object_type=SCENE_OBJECT_TYPE,
            bg_color="#00000000",  # Fully transparent
            layer=self._layer + 2,
        )
        belt = self._get_belt_physics_body()
        belt.set_belt_speed(self._conveyor_speed if self._active else 0.0)
        belt.set_direction(self._direction)

        # ------------------------------------------------------------------
        # Register components — base at origin, stripes evenly distributed
        # along the scroll axis, physics conveyor inset from base edges.
        # ------------------------------------------------------------------
        self.add_component("base", self._base, offset_x=0.0, offset_y=0.0)

        for i, stripe in enumerate(self._belt_stripes):
            initial = (i * self._belt_length) % self._conveyor_length
            if is_h:
                self.add_component(f"belt_{i}", stripe, offset_x=initial, offset_y=cross_offset)
            else:
                self.add_component(f"belt_{i}", stripe, offset_x=cross_offset, offset_y=initial)

        if is_h:
            self.add_component("physics", self._physics_conveyor, offset_x=0.0, offset_y=cross_offset)
        else:
            self.add_component("physics", self._physics_conveyor, offset_x=cross_offset, offset_y=0.0)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        super().update(dt)

        # Advance the belt position.  The sign encodes direction so the
        # stripes visually scroll toward the conveyor's output end.
        speed = (
            self._conveyor_speed
            if self._direction in (CardinalDirection.RIGHT, CardinalDirection.DOWN)
            else -self._conveyor_speed
        )
        self._belt_position = (self._belt_position + speed * dt) % self._belt_length

        cross_offset = self._belt_size_slice / 2.0

        # Update each stripe's offset so they tile seamlessly along the scroll axis.
        for i, stripe in enumerate(self._belt_stripes):
            scroll_offset = (self._belt_position + i * self._belt_length) % self._conveyor_length
            if self.is_horizontal:
                self._components[f"belt_{i}"] = (stripe, scroll_offset, cross_offset)
                stripe.x = self.x + scroll_offset
                stripe.y = self.y + cross_offset
            else:
                self._components[f"belt_{i}"] = (stripe, cross_offset, scroll_offset)
                stripe.x = self.x + cross_offset
                stripe.y = self.y + scroll_offset

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        direction: CardinalDirection = CardinalDirection.RIGHT,
        conveyor_length: float = 60.0,
        conveyor_width: float = 20.0,
        conveyor_speed: float = 30.0,
        conveyor_color: str = "#888888",
        belt_length: float = 10.0,
        belt_color: str = "#555555",
        layer: int = 0,
        body: dict | None = None,
        **kwargs,
    ) -> Self:
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
        physics_body = cls.get_composite_body_from_dict(body or {})

        if not physics_body:
            is_horizontal = direction in (CardinalDirection.RIGHT, CardinalDirection.LEFT)
            if is_horizontal:
                body_w = conveyor_length
                body_h = conveyor_width
            else:
                body_w = conveyor_width
                body_h = conveyor_length
            physics_body = ConveyorBody(
                name=f"{name}_body",
                template_name='Base Physics Body',
                x=float(x),
                y=float(y),
                width=body_w,
                height=body_h,
                collision_layer=CollisionLayer.TRANSPARENT,
                collision_mask=[],
            )
        else:
            if not isinstance(physics_body, ConveyorBody):
                raise TypeError(f"Expected physics_body to be ConveyorBody, got {type(physics_body)}")

        return cls(
            name=name,
            physics_body=physics_body,
            direction=direction,
            conveyor_length=conveyor_length,
            conveyor_width=conveyor_width,
            conveyor_speed=conveyor_speed,
            conveyor_color=conveyor_color,
            belt_length=belt_length,
            belt_color=belt_color,
            layer=layer,
            id=kwargs.get("id"),
            description=kwargs.get("description", ""),
            group_id=kwargs.get("group_id"),
            tags=kwargs.get("tags"),
            properties=kwargs.get("properties") or {},
        )

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Restore a :class:`ConveyorSceneObject` from a serialised dictionary."""
        props = data.get("properties", {})
        direction = CardinalDirection.from_str(props.get("direction", "RIGHT")) or CardinalDirection.RIGHT
        physics_body = cls.get_composite_body_from_dict(data.get("body", {}))
        if not physics_body:
            raise ValueError(
                f"ConveyorSceneObject.from_dict: could not reconstruct physics body from data: {data.get('body')}"
            )
        return cls(
            name=data["name"],
            physics_body=physics_body,
            description=data.get("description", ""),
            direction=direction,
            conveyor_length=props.get("conveyor_length", 60.0),
            conveyor_width=props.get("conveyor_width", 20.0),
            conveyor_speed=props.get("conveyor_speed", 30.0),
            conveyor_color=props.get("conveyor_color", "#888888"),
            belt_length=props.get("belt_length", 10.0),
            belt_color=props.get("belt_color", "#555555"),
            layer=data.get("layer", 0),
            properties=props,
            id=data.get("id"),
            group_id=data.get("group_id"),
            tags=data.get("tags", []),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super()._compile_properties()
        self._properties.update({
            "conveyor_length": self._conveyor_length,
            "conveyor_width": self._conveyor_width,
            "conveyor_speed": self._conveyor_speed,
            "conveyor_color": self._conveyor_color,
            "belt_length": self._belt_length,
            "belt_color": self._belt_color,
        })

    def _get_belt_physics_body(self) -> ConveyorBody:
        if not isinstance(self._physics_conveyor.physics_body, ConveyorBody):
            raise TypeError(f"Expected physics conveyor body to be ConveyorBody, got {type(self._physics_conveyor.physics_body)}")
        return self._physics_conveyor.physics_body

    # ------------------------------------------------------------------
    # Public API for external control
    # ------------------------------------------------------------------

    @property
    def conveyor_speed(self) -> float:
        """Get the current speed of the conveyor belt."""
        return self.get_conveyor_speed()

    @conveyor_speed.setter
    def conveyor_speed(self, speed: float) -> None:
        """Set the speed of the conveyor belt."""
        return self.set_conveyor_speed(speed)

    def get_conveyor_speed(self) -> float:
        """Get the current speed of the conveyor belt."""
        return self._conveyor_speed

    def set_conveyor_speed(self, speed: float) -> None:
        """Set the speed of the conveyor belt."""
        self._conveyor_speed = speed
        self._get_belt_physics_body().set_belt_speed(speed if self._active else 0.0)

    def get_conveyor_width(self) -> float:
        """Get the current width of the conveyor base."""
        return self._conveyor_width

    def set_conveyor_width(self, width: float) -> None:
        """Set the width of the conveyor base and resize all belt stripes accordingly."""
        self._conveyor_width = width
        is_h = self.is_horizontal
        stripe_cross = max(1.0, width - self._belt_size_slice)
        if is_h:
            self._base.width = width
            for stripe in self._belt_stripes:
                stripe.height = stripe_cross
        else:
            self._base.height = width
            for stripe in self._belt_stripes:
                stripe.width = stripe_cross
        self._physics_conveyor.width = width - self._belt_size_slice if not is_h else self._physics_conveyor.width
        self._physics_conveyor.height = width - self._belt_size_slice if is_h else self._physics_conveyor.height

    def get_conveyor_length(self) -> float:
        """Get the current length of the conveyor."""
        return self._conveyor_length

    def set_conveyor_length(self, length: float) -> None:
        """Set the length of the conveyor and rebuild the tiling belt stripes."""
        self._conveyor_length = length
        is_h = self.is_horizontal
        if is_h:
            self._base.width = length
            self._physics_conveyor.width = length
        else:
            self._base.height = length
            self._physics_conveyor.height = length
        # Rebuild stripe count and re-register all belt components
        for i in range(len(self._belt_stripes)):
            self.remove_component(f"belt_{i}")
        self._belt_stripes.clear()
        n_stripes = max(1, math.ceil(length / self._belt_length))
        stripe_along = max(1.0, self._belt_length - self._belt_size_slice)
        stripe_cross = max(1.0, self._conveyor_width - self._belt_size_slice)
        stripe_w = stripe_along if is_h else stripe_cross
        stripe_h = stripe_cross if is_h else stripe_along
        cross_offset = self._belt_size_slice / 2.0
        for i in range(n_stripes):
            stripe = self.create_simple_component(
                name=f"belt_{i}",
                template_name="Base Physics Body",
                body_type=BodyType.KINEMATIC,
                width=stripe_w,
                height=stripe_h,
                collision_layer=CollisionLayer.TRANSPARENT,
                collision_mask=[],
                scene_object_type=SCENE_OBJECT_TYPE,
                bg_color=self._belt_color,
                layer=self._layer + 1,
            )
            self._belt_stripes.append(stripe)
            initial = (i * self._belt_length) % length
            if is_h:
                self.add_component(f"belt_{i}", stripe, offset_x=initial, offset_y=cross_offset)
            else:
                self.add_component(f"belt_{i}", stripe, offset_x=cross_offset, offset_y=initial)
        self._compile_properties()


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME,
        scene_object_class=ConveyorSceneObject,
        description="Composite conveyor with animated belt (top-down view)",
        factory_func=ConveyorSceneObject.create,
        default_kwargs={
            "name": SCENE_OBJECT_TEMPLATE_NAME,
            "direction": CardinalDirection.RIGHT,
            "conveyor_length": 60.0,
            "conveyor_width": 20.0,
            "conveyor_speed": 30.0,
            "conveyor_color": "#888888",
            "belt_length": 10.0,
            "belt_color": "#555555",
            "layer": 0,
        },
        category="Conveyance",
    )
)
