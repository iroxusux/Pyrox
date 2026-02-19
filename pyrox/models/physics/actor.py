"""Top-down player actor physics body implementation.

Provides a kinematic physics body for a player-controlled actor in a
top-down scene. Accepts a :class:`KeyboardInputSource` to drive movement
from any keyboard backend.
"""
from __future__ import annotations

from typing import List, Optional

from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory

# ---------------------------------------------------------------------------
# Player actor body
# ---------------------------------------------------------------------------


class TopDownPlayerBody(BasePhysicsBody):
    """A kinematic physics body controlled by keyboard input.

    Represents the player in a top-down scene.  Because the actor is
    kinematic it is not subject to gravity or external forces — velocity is
    set directly from the keyboard state each tick, giving tight, responsive
    movement.

    The player can be moved programmatically via :meth:`move_left`,
    :meth:`move_right`, :meth:`move_up`, and :meth:`move_down`, or
    automatically by providing a :class:`KeyboardInputSource` which is polled
    in :meth:`update`.

    Attributes:
        speed:    Movement speed in world units per second.
        keyboard: Optional keyboard source that drives automatic movement.
    """

    def __init__(
        self,
        name: str = "Player",
        id: str = "",
        template_name: str = "TopDownPlayer",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 20.0,
        height: float = 20.0,
        speed: float = 150.0,
        collision_layer: CollisionLayer = CollisionLayer.PLAYER,
        collision_mask: Optional[List[CollisionLayer]] = None,
        material: Optional[Material] = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialize top-down player body.

        Args:
            name:            Display name of the player.
            id:              Optional explicit ID (auto-generated if empty).
            template_name:   Factory template name.
            x:               Initial X position.
            y:               Initial Y position.
            width:           Collision width.
            height:          Collision height.
            speed:           Movement speed in world units per second.
            keyboard:        Optional :class:`KeyboardInputSource` to poll
                             each :meth:`update` call.
            collision_layer: Physics layer this body occupies.
            collision_mask:  Which layers this body collides with.
            material:        Material properties (uses a light default if ``None``).
        """
        if collision_mask is None:
            collision_mask = [
                CollisionLayer.DEFAULT,
                CollisionLayer.TERRAIN,
                CollisionLayer.ENEMY,
                CollisionLayer.SENSOR,
            ]

        if material is None:
            material = Material(
                density=1.0,
                restitution=0.0,
                friction=0.5,
                drag=0.0,
            )

        # Mass for a humanoid actor; moment of inertia not really used
        # in kinematic mode but initialised for completeness.
        mass = 70.0
        moment = (1.0 / 12.0) * mass * (width * width + height * height)

        super().__init__(
            name=name,
            id=id,
            template_name=template_name,
            tags=["player", "actor"],
            body_type=BodyType.KINEMATIC,
            enabled=True,
            sleeping=False,
            mass=mass,
            moment_of_inertia=moment,
            collider_type=ColliderType.RECTANGLE,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=False,
            x=x,
            y=y,
            width=width,
            height=height,
            material=material,
        )

        self._movement_speed: float = speed

        # Use cardinal directions to track multiple dirs at once
        # e.g. if both left and up are pressed, movement_direction = "NW"
        self._movement_direction: str = ""

    # ------------------------------------------------------------------
    # Direct movement helpers
    # ------------------------------------------------------------------

    @property
    def move_left(self) -> bool:
        """Whether left movement is currently active."""
        return "W" in self._movement_direction

    @move_left.setter
    def move_left(self, active: bool) -> None:
        self.set_move_left(active)

    def set_move_left(self, active: bool) -> None:
        """Apply leftward movement for one tick.

        Args:
            dt: Delta time in seconds.
        """
        if active and "W" not in self._movement_direction:
            self._movement_direction += "W"
            self.set_move_right(False)  # Ensure opposite direction is not active
        elif not active and "W" in self._movement_direction:
            self._movement_direction = self._movement_direction.replace("W", "")

    @property
    def move_right(self) -> bool:
        """Whether right movement is currently active."""
        return "E" in self._movement_direction

    @move_right.setter
    def move_right(self, active: bool) -> None:
        self.set_move_right(active)

    def set_move_right(self, active: bool) -> None:
        """Apply rightward movement for one tick.

        Args:
            dt: Delta time in seconds.
        """
        if active and "E" not in self._movement_direction:
            self._movement_direction += "E"
            self.set_move_left(False)  # Ensure opposite direction is not active
        elif not active and "E" in self._movement_direction:
            self._movement_direction = self._movement_direction.replace("E", "")

    @property
    def move_up(self) -> bool:
        """Whether upward movement is currently active."""
        return "N" in self._movement_direction

    @move_up.setter
    def move_up(self, active: bool) -> None:
        self.set_move_up(active)

    def set_move_up(self, active: bool) -> None:
        """Apply upward movement for one tick.

        Args:
            dt: Delta time in seconds.
        """
        if active and "N" not in self._movement_direction:
            self._movement_direction += "N"
            self.set_move_down(False)  # Ensure opposite direction is not active
        elif not active and "N" in self._movement_direction:
            self._movement_direction = self._movement_direction.replace("N", "")

    @property
    def move_down(self) -> bool:
        """Whether downward movement is currently active."""
        return "S" in self._movement_direction

    @move_down.setter
    def move_down(self, active: bool) -> None:
        self.set_move_down(active)

    def set_move_down(self, active: bool) -> None:
        """Apply downward movement for one tick.

        Args:
            dt: Delta time in seconds.
        """
        if active and "S" not in self._movement_direction:
            self._movement_direction += "S"
            self.set_move_up(False)  # Ensure opposite direction is not active
        elif not active and "S" in self._movement_direction:
            self._movement_direction = self._movement_direction.replace("S", "")

    # ------------------------------------------------------------------
    # Physics callbacks
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Poll keyboard input and advance the actor for one physics tick.

        If a :class:`KeyboardInputSource` is attached it is read here and
        velocity is set accordingly.  The physics engine is then responsible
        for integrating velocity into position.

        Args:
            dt: Delta time in seconds.
        """
        direction = self._movement_direction
        speed = self._movement_speed

        vx = 0.0
        vy = 0.0

        if "W" in direction:
            vx -= speed

        if "E" in direction:
            vx += speed

        if "N" in direction:
            vy -= speed

        if "S" in direction:
            vy += speed

        self.velocity_x = vx
        self.velocity_y = vy

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when collision starts with another body.

        Args:
            other: The other physics body involved in the collision.
        """
        pass

    def on_collision_stay(self, other: IPhysicsBody2D) -> None:
        """Called each frame while colliding with another body.

        Args:
            other: The other physics body.
        """
        pass

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when a collision with another body ends.

        Args:
            other: The other physics body.
        """
        pass

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def create_default(
        cls,
        name: str = "Player",
        x: float = 0.0,
        y: float = 0.0,
        **kwargs,
    ) -> 'TopDownPlayerBody':
        """Create a default top-down player actor.

        Args:
            name:     Display name.
            x:        Starting X position.
            y:        Starting Y position.
            keyboard: Optional keyboard source.
            **kwargs: Additional constructor arguments.

        Returns:
            A :class:`TopDownPlayerBody` with sensible defaults.
        """
        return cls(name=name, x=x, y=y, **kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<TopDownPlayerBody '{self.name}' "
            f"movement_speed={self._movement_speed:.1f} "
            f"pos=({self.x:.1f}, {self.y:.1f}) "
            f"size=({self.width:.1f}x{self.height:.1f}) "
        )


# ---------------------------------------------------------------------------
# Factory registration
# ---------------------------------------------------------------------------

PhysicsSceneFactory.register_template(
    template_name="TopDownPlayer",
    template=PhysicsSceneTemplate(
        name="TopDownPlayer",
        body_class=TopDownPlayerBody,
        description="Keyboard-driven kinematic player for top-down scenes.",
        default_kwargs={
            "width": 20.0,
            "height": 20.0,
            "speed": 150.0,
        },
        category="Actors",
    ),
)
