"""Top-down piston composite scene object.

A piston consists of two components:

* **rod** — a rectangle that grows/shrinks along the piston axis.
* **head** — a square that sits flush at the tip of the rod.

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

    # In the render / update loop:
    piston.update(dt)
"""
from pyrox.interfaces import IBasePhysicsBody, BodyType, CardinalDirection, CollisionLayer
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.scene.assets.topdown._compkinemetic import ActivatableCompositeKinematicSceneObject
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate

SCENE_OBJECT_TYPE_PISTON = "piston"
SCENE_OBJECT_TEMPLATE_NAME_PISTON = "Top-Down Piston"


class PistonSceneObject(ActivatableCompositeKinematicSceneObject):
    """Top-down composite piston with animated rod and head.

    The composite's origin is the **base** (mounting point) of the piston.
    The two child components are:

    * ``"rod"``  — a rectangle aligned along the piston axis whose length
      is driven by the extend/retract animations.
    * ``"head"`` — a square that follows the tip of the rod automatically
      every :meth:`update` call.

    Both components are centred on the perpendicular axis relative to the
    piston head size, so the rod appears centred inside the head footprint.
    """

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        direction: CardinalDirection = CardinalDirection.RIGHT,
        retracted_length: float = 20.0,
        extended_length: float = 60.0,
        rod_thickness: float = 8.0,
        head_size: float = 14.0,
        animation_duration: float = 0.5,
        rod_color: str = "#888888",
        head_color: str = "#555555",
        layer: int = 0,
        properties: dict = dict(),
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
        **kwargs,
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
        self._retracted_length = float(retracted_length)
        self._extended_length = float(extended_length)
        self._rod_thickness = float(rod_thickness)
        self._head_size = float(head_size)
        self._rod_color = rod_color
        self._head_color = head_color
        self._tracking_rod_length = self._retracted_length  # For driving the rod animation
        self._prev_head_world_pos: tuple[float, float] | None = None
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            scene_object_type=SCENE_OBJECT_TYPE_PISTON,
            template_name=SCENE_OBJECT_TEMPLATE_NAME_PISTON,
            id=id,
            group_id=group_id,
            tags=tags,
            layer=layer,
            direction=direction,
            animation_duration=animation_duration,
            properties=properties,
        )

    def current_animator_position(self) -> float:
        return self._tracking_rod_length

    # ------------------------------------------------------------------
    # Build Methods
    # ------------------------------------------------------------------

    def build_components(self):
        """Override this method in derived classes to build the kinematic components and register them as children."""
        # ------------------------------------------------------------------
        # Rod component
        # ------------------------------------------------------------------
        rod_w = self._retracted_length if self.is_horizontal else self._rod_thickness
        rod_h = self._rod_thickness if self.is_horizontal else self._retracted_length

        self._rod = self.create_simple_component(
            name="rod",
            template_name="Piston Rod",
            body_type=BodyType.KINEMATIC,
            width=rod_w,
            height=rod_h,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            scene_object_type="piston_rod",
            bg_color=self._rod_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Head component
        # ------------------------------------------------------------------
        self._head = self.create_simple_component(
            name="head",
            template_name="Base Physics Body",
            body_type=BodyType.KINEMATIC,
            width=self._head_size,
            height=self._head_size,
            collision_layer=CollisionLayer.TERRAIN,
            collision_mask=self.default_collision_mask,
            scene_object_type="piston_head",
            bg_color=self._head_color,
            layer=self._layer,
        )

        # ------------------------------------------------------------------
        # Animation clips (registered on the rod)
        # The animated property is "width" for horizontal pistons and
        # "height" for vertical pistons.
        # ------------------------------------------------------------------

        self.create_clips_on_property(
            tracking_property='_tracking_rod_length',
            target1=self._retracted_length,
            target2=self._extended_length,
            animation_duration=self._animation_duration,
        )

        # ------------------------------------------------------------------
        # Register components at initial (retracted) offsets
        # ------------------------------------------------------------------
        rod_ox, rod_oy = self._rod_offset(self._retracted_length)
        head_ox, head_oy = self._head_offset(self._retracted_length)
        self.add_component("rod",  self._rod,  offset_x=rod_ox,  offset_y=rod_oy)
        self.add_component("head", self._head, offset_x=head_ox, offset_y=head_oy)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Advance animations and keep the head aligned with the rod tip.

        Calls :meth:`CompositeSceneObject.update` (which ticks both the rod
        and head animators) then re-calculates component offsets based on the
        rod's current animated length.  World positions are written directly
        to each component's physics body so the spatial grid and collision
        detection always see up-to-date bounds.  The head's kinematic velocity
        is derived from its per-frame position delta so the impulse solver can
        compute the correct push force against dynamic objects.

        Args:
            dt: Elapsed wall-clock seconds since the last call.
        """
        super().update(dt)
        current_len = self._tracking_rod_length

        if self.is_horizontal:
            self._rod.width = current_len
        else:
            self._rod.height = current_len

        rod_ox, rod_oy = self._rod_offset(current_len)
        head_ox, head_oy = self._head_offset(current_len)

        # Sync physics body world positions immediately (eliminates the
        # 1-frame lag left by CompositeSceneObject.update using stale offsets).
        self._rod.x = self.x + rod_ox
        self._rod.y = self.y + rod_oy
        head_world_x = self.x + head_ox
        head_world_y = self.y + head_oy
        self._head.x = head_world_x
        self._head.y = head_world_y

        # Propagate animation-driven head velocity so the impulse solver sees
        # the effective kinematic speed and can push dynamic bodies correctly.
        if dt > 0 and self._prev_head_world_pos is not None:
            vx = (head_world_x - self._prev_head_world_pos[0]) / dt
            vy = (head_world_y - self._prev_head_world_pos[1]) / dt
            self._head.physics_body.set_linear_velocity(vx, vy)
        self._prev_head_world_pos = (head_world_x, head_world_y)

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
        direction: CardinalDirection = CardinalDirection.RIGHT,
        retracted_length: float = 20.0,
        extended_length: float = 60.0,
        rod_thickness: float = 8.0,
        head_size: float = 14.0,
        animation_duration: float = 0.5,
        rod_color: str = "#888888",
        head_color: str = "#555555",
        layer: int = 0,
        body: dict | None = None,
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
        physics_body = cls.get_composite_body_from_dict(body or {})

        if not physics_body:
            is_horizontal = direction in (CardinalDirection.RIGHT, CardinalDirection.LEFT)
            if is_horizontal:
                body_w = extended_length + head_size
                body_h = head_size
            else:
                body_w = head_size
                body_h = extended_length + head_size
            physics_body = BasePhysicsBody(
                name=f"{name}_body",
                template_name='Base Physics Body',
                x=float(x),
                y=float(y),
                width=body_w,
                height=body_h,
                collision_layer=CollisionLayer.TRANSPARENT,
                collision_mask=[],
            )

        return cls(
            name=name,
            physics_body=physics_body,
            direction=direction,
            retracted_length=retracted_length,
            extended_length=extended_length,
            rod_thickness=rod_thickness,
            head_size=head_size,
            animation_duration=animation_duration,
            rod_color=rod_color,
            head_color=head_color,
            layer=layer,
            id=kwargs.get("id"),
            description=kwargs.get("description", ""),
            group_id=kwargs.get("group_id"),
            tags=kwargs.get("tags"),
            properties=kwargs.get("properties") or {},
        )

    @classmethod
    def from_dict(cls, data: dict) -> "PistonSceneObject":
        """Restore a :class:`PistonSceneObject` from a serialised dictionary."""
        props = data.get("properties", {})
        direction = CardinalDirection.from_str(props.get("direction", "RIGHT")) or CardinalDirection.RIGHT
        physics_body = cls.get_composite_body_from_dict(data.get("body", {}))
        if not physics_body:
            raise ValueError(
                f"PistonSceneObject.from_dict: could not reconstruct physics body from data: {data.get('body')}"
            )
        return cls(
            name=data["name"],
            physics_body=physics_body,
            description=data.get("description", ""),
            direction=direction,
            retracted_length=float(props.get("retracted_length", 20.0)),
            extended_length=float(props.get("extended_length", 60.0)),
            rod_thickness=float(props.get("rod_thickness", 8.0)),
            head_size=float(props.get("head_size", 14.0)),
            animation_duration=float(props.get("animation_duration", 0.5)),
            rod_color=props.get("rod_color", "#888888"),
            head_color=props.get("head_color", "#555555"),
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
            "direction": self._direction.name,
            "retracted_length": self._retracted_length,
            "extended_length": self._extended_length,
            "rod_thickness": self._rod_thickness,
            "head_size": self._head_size,
        })

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
            case CardinalDirection.RIGHT:
                return (0.0, perp_offset)
            case CardinalDirection.LEFT:
                return (-current_length, perp_offset)
            case CardinalDirection.DOWN:
                return (perp_offset, 0.0)
            case CardinalDirection.UP:
                return (perp_offset, -current_length)
        raise ValueError(f"Invalid piston direction: {self._direction}")

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
            case CardinalDirection.RIGHT:
                return (current_length, 0.0)
            case CardinalDirection.LEFT:
                return (-hs, 0.0)
            case CardinalDirection.DOWN:
                return (0.0, current_length)
            case CardinalDirection.UP:
                return (0.0, -hs)
        raise ValueError(f"Invalid piston direction: {self._direction}")

    # ------------------------------------------------------------------
    # Public API for external control
    # ------------------------------------------------------------------

    @property
    def extended_length(self) -> float:
        """Target rod length when fully extended."""
        return self._extended_length

    @extended_length.setter
    def extended_length(self, value: float) -> None:
        """Set the target rod length when fully extended."""
        self._extended_length = float(value)
        self.update_activate_deactivate_targets(target_active=self._extended_length, target_inactive=self._retracted_length)
        self._compile_properties()  # Update the properties dict for serialization


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME_PISTON,
        scene_object_class=PistonSceneObject,
        description="Composite piston with animated rod and head (top-down view)",
        factory_func=PistonSceneObject.create,
        default_kwargs={
            "name": SCENE_OBJECT_TEMPLATE_NAME_PISTON,
            "direction": CardinalDirection.RIGHT,
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
