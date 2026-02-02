"""Base physics body implementation with common functionality.

Provides a base class for creating custom physics bodies with
shared behavior and utilities.
"""
from typing import List, Optional
from pyrox.interfaces import (
    IBasePhysicsBody,
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from pyrox.models.protocols.physics import PhysicsBody2D, Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class BasePhysicsBody(
    IBasePhysicsBody,
    PhysicsBody2D,
):
    """Base class for custom physics bodies.

    Extends PhysicsBody2D with common functionality and utilities
    for building specific physics objects.

    Attributes:
        name: Optional name for identification
        tags: List of string tags for categorization
    """

    def __init__(
        self,
        name: str = "",
        tags: Optional[List[str]] = None,
        body_type: BodyType = BodyType.DYNAMIC,
        enabled: bool = True,
        sleeping: bool = False,
        mass: float = 1.0,
        moment_of_inertia: float = 1.0,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        acceleration_x: float = 0.0,
        acceleration_y: float = 0.0,
        angular_velocity: float = 0.0,
        collider_type: ColliderType = ColliderType.RECTANGLE,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: List[CollisionLayer] | None = None,
        is_trigger: bool = False,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        material: Material | None = None,
    ):
        """Initialize base physics body.

        Args:
            name: Optional name for identification
            tags: List of tags for categorization
            body_type: Type of physics body (STATIC, DYNAMIC, KINEMATIC)
            enabled: Whether physics simulation is enabled
            sleeping: Whether the body starts sleeping
            mass: Mass in kilograms
            moment_of_inertia: Rotational inertia
            velocity_x: Initial X velocity
            velocity_y: Initial Y velocity
            acceleration_x: Initial X acceleration
            acceleration_y: Initial Y acceleration
            angular_velocity: Initial angular velocity in rad/s
            collider_type: Shape of collision bounds
            collision_layer: Which layer this object is on
            collision_mask: Which layers this object collides with
            is_trigger: Whether this is a trigger (no physics response)
            x: X position
            y: Y position
            width: Width of the body
            height: Height of the body
            roll: Roll rotation in degrees
            pitch: Pitch rotation in degrees
            yaw: Yaw rotation in degrees
            material: Material properties (creates default if None)
        """
        PhysicsBody2D.__init__(
            self=self,
            body_type=body_type,
            enabled=enabled,
            sleeping=sleeping,
            mass=mass,
            moment_of_inertia=moment_of_inertia,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            acceleration_x=acceleration_x,
            acceleration_y=acceleration_y,
            angular_velocity=angular_velocity,
            collider_type=collider_type,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=is_trigger,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            material=material,
        )

        self.name = name
        self.tags = tags or []

    def has_tag(self, tag: str) -> bool:
        """Check if this body has a specific tag.

        Args:
            tag: Tag to check for

        Returns:
            True if the body has the tag
        """
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """Add a tag to this body.

        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this body.

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)

    def is_on_top_of(self, other: IPhysicsBody2D) -> bool:
        """Check if this body is on top of another body.

        Useful for conveyor belts, platforms, etc.

        Args:
            other: The other physics body

        Returns:
            True if this body is resting on top of the other body
        """
        # Get bounding boxes
        min_x, min_y, max_x, max_y = self.get_bounds()
        other_min_x, other_min_y, other_max_x, other_max_y = other.get_bounds()

        # Check if horizontally aligned (overlapping in X)
        if max_x < other_min_x or min_x > other_max_x:
            return False

        # Check if this body's bottom is near the other's top
        # Allow small tolerance for floating point errors
        tolerance = 1.0
        bottom_y = max_y
        other_top_y = other_min_y

        return abs(bottom_y - other_top_y) < tolerance and bottom_y <= other_top_y + tolerance

    def __repr__(self) -> str:
        """String representation of the body."""
        name_str = f" '{self.name}'" if self.name else ""
        return (f"<{self.__class__.__name__}{name_str} "
                f"type={self.body_type.name} "
                f"pos=({self.x:.1f}, {self.y:.1f}) "
                f"size=({self.width:.1f}x{self.height:.1f})>")


# Register base template in factory
PhysicsSceneFactory.register_template(
    template_name="Base Physics Body",
    template=PhysicsSceneTemplate(
        name="Base Physics Body",
        body_class=BasePhysicsBody,
        description="A basic physics body with default properties.",
        default_kwargs={
            "body_type": BodyType.DYNAMIC,
            "width": 10.0,
            "height": 10.0,
            "material": Material(
                density=1.0,
                restitution=0.3,
                friction=0.5,
                drag=0.1
            ),
        },
        category="Basic"
    )
)
