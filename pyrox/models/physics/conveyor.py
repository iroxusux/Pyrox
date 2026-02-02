"""Conveyor belt physics body implementation.

Provides a static or kinematic conveyor belt that moves objects
placed on top of it in a specified direction and speed.
"""
from typing import List, Set
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class ConveyorBody(BasePhysicsBody):
    """Conveyor belt that moves objects on top of it.

    A conveyor belt is typically a STATIC or KINEMATIC body that doesn't
    move itself, but applies velocity to dynamic objects sitting on top.

    Attributes:
        belt_velocity: (vx, vy) velocity applied to objects on the belt
        is_active: Whether the conveyor is currently running
        direction: Direction the belt moves (1.0 = right, -1.0 = left for X)
        speed: Speed of the belt in units/second
    """

    def __init__(
        self,
        name: str = "Conveyor",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 20.0,
        direction: float = 1.0,  # 1.0 = right, -1.0 = left
        belt_speed: float = 50.0,  # units per second
        is_active: bool = True,
        body_type: BodyType = BodyType.STATIC,
        collision_layer: CollisionLayer = CollisionLayer.TERRAIN,
        collision_mask: List[CollisionLayer] | None = None,
        material: Material | None = None,
    ):
        """Initialize conveyor belt.

        Args:
            name: Name of the conveyor
            x: X position
            y: Y position
            width: Width of the conveyor belt
            height: Height of the conveyor belt
            direction: Direction multiplier (1.0 = right/up, -1.0 = left/down)
            speed: Speed of the belt in units/second
            is_active: Whether the conveyor starts active
            body_type: Usually STATIC or KINEMATIC
            collision_layer: Collision layer
            collision_mask: Which layers can be affected by this conveyor
            material: Material properties (high friction recommended)
        """
        # Default collision mask includes common dynamic objects
        if collision_mask is None:
            collision_mask = [
                CollisionLayer.DEFAULT,
                CollisionLayer.PLAYER,
                CollisionLayer.ENEMY,
            ]

        # Use high-friction material by default for conveyors
        if material is None:
            material = Material(
                density=1.0,
                restitution=0.1,  # Low bounce
                friction=0.9,     # High friction
                drag=0.05
            )

        BasePhysicsBody.__init__(
            self=self,
            name=name,
            tags=["conveyor", "platform"],
            body_type=body_type,
            enabled=True,
            sleeping=False,
            mass=0.0 if body_type == BodyType.STATIC else 100.0,
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

        self.direction = direction
        self.belt_speed = belt_speed
        self.is_active = is_active
        self._objects_on_belt: Set[IPhysicsBody2D] = set()

    @property
    def belt_velocity(self) -> tuple[float, float]:
        """Get the current belt velocity vector.

        Returns:
            (vx, vy) velocity tuple
        """
        if not self.is_active:
            return (0.0, 0.0)
        return (self.direction * self.belt_speed, 0.0)

    def set_direction(self, direction: float) -> None:
        """Set the belt direction.

        Args:
            direction: 1.0 for right/forward, -1.0 for left/backward
        """
        self.direction = 1.0 if direction >= 0 else -1.0

    def set_belt_speed(self, belt_speed: float) -> None:
        """Set the belt speed.

        Args:
            speed: Speed in units/second (always positive)
        """
        self.belt_speed = abs(belt_speed)

    def toggle(self) -> None:
        """Toggle the conveyor on/off."""
        self.is_active = not self.is_active

    def activate(self) -> None:
        """Turn the conveyor on."""
        self.is_active = True

    def deactivate(self) -> None:
        """Turn the conveyor off."""
        self.is_active = False

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when an object starts colliding with the conveyor.

        Args:
            other: The colliding physics body
        """
        # Track objects that enter the conveyor
        if self.is_on_top_of(other):
            self._objects_on_belt.add(other)

    def on_collision_stay(self, other: IPhysicsBody2D) -> None:
        """Called each frame while an object is colliding with the conveyor.

        This is where we apply the conveyor motion to objects on top.

        Args:
            other: The colliding physics body
        """
        if not self.is_active:
            return

        # Only affect dynamic bodies that are on top of the conveyor
        if other.body_type != BodyType.DYNAMIC:
            return

        if not self.is_on_top_of(other):
            # Object is touching but not on top (side collision)
            self._objects_on_belt.discard(other)
            return

        # Add to tracking set
        self._objects_on_belt.add(other)

        # Apply conveyor velocity to the object
        belt_vx, belt_vy = self.belt_velocity
        current_vx, current_vy = other.linear_velocity

        # Override X velocity with belt velocity, preserve Y velocity
        # This allows objects to fall naturally while being carried
        other.set_linear_velocity(belt_vx, current_vy)

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when an object stops colliding with the conveyor.

        Args:
            other: The physics body that left
        """
        self._objects_on_belt.discard(other)

    def update(self, dt: float) -> None:
        """Update the conveyor each physics step.

        Args:
            dt: Delta time in seconds
        """
        # Clean up tracking set (remove objects no longer in contact)
        # The collision callbacks handle this, but this is a safety check
        pass

    def get_objects_on_belt(self) -> Set[IPhysicsBody2D]:
        """Get all objects currently on the conveyor belt.

        Returns:
            Set of physics bodies on the belt
        """
        return self._objects_on_belt.copy()

    def __repr__(self) -> str:
        """String representation."""
        state = "ACTIVE" if self.is_active else "INACTIVE"
        dir_str = "→" if self.direction > 0 else "←"
        return (f"<ConveyorBody '{self.name}' {state} "
                f"{dir_str} {self.belt_speed:.1f}u/s "
                f"pos=({self.x:.1f}, {self.y:.1f}) "
                f"size=({self.width:.1f}x{self.height:.1f}) "
                f"objects={len(self._objects_on_belt)}>")


# Register conveyor template in factory
PhysicsSceneFactory.register_template(
    template_name="Conveyor Belt",
    template=PhysicsSceneTemplate(
        name="Conveyor Belt",
        body_class=ConveyorBody,
        default_kwargs={
            "name": "Conveyor",
            "width": 200.0,
            "height": 20.0,
            "direction": 1.0,
            "belt_speed": 50.0,
            "is_active": True,
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Platforms",
        description="A conveyor belt that moves objects placed on top of it.",
    )
)
