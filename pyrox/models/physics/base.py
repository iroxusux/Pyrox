"""Base physics body implementation with common functionality.

Provides a base class for creating custom physics bodies with
shared behavior and utilities.
"""
from typing import (
    Any,
    List,
    Optional
)
from pyrox.interfaces import (
    IBasePhysicsBody,
    BodyType,
    ColliderType,
    CollisionLayer,
    IMaterial
)
from pyrox.services import IdGeneratorService
from pyrox.models.protocols import Nameable, Connectable
from pyrox.models.protocols.physics import PhysicsBody2D, Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class BasePhysicsBody(
    IBasePhysicsBody,
    Nameable,
    Connectable,
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
        id: str = "",
        template_name: Optional[str] = None,
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
        material: IMaterial | None = None,
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
        Nameable.__init__(self=self, name=name)
        id = id or f'physics-body-{name}-{IdGeneratorService.get_id()}'
        Connectable.__init__(self=self, id=id)
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
        self._template_name = template_name
        self._tags = tags or []

    def get_tags(self) -> list[str]:
        """Get the list of tags associated with this body.

        Returns:
            List of tags
        """
        return self._tags

    def set_tags(self, tags: list[str]) -> None:
        """Set the list of tags for this body.

        Args:
            tags: List of tags to set
        """
        self._tags = tags

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

    # IConnectable methods
    def get_inputs(self) -> dict[str, Any]:
        """Get available input connections.

        Returns:
            Dictionary of input names to connection endpoints
        """
        return {}

    def get_outputs(self) -> dict[str, Any]:
        """Get available output connections.

        Returns:
            Dictionary of output names to connection endpoints
        """
        return {}

    def get_properties(self) -> dict[str, Any]:
        """Get properties that can be edited in the properties panel.

        Returns:
            Dictionary mapping property names to their metadata.
            Each entry should have:
            - type: 'float', 'int', 'bool', 'string', 'enum'
            - get: Callable that returns the current value
            - set: Callable that sets a new value
            - label: Display label for the property
            - For float/int: optional 'min', 'max'
            - For enum: 'values' list of valid values
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "acceleration_x": self.acceleration_x,
            "acceleration_y": self.acceleration_y,
            "body_type": self.body_type.name,
            "mass": self.mass,
            # Collider properties
            "collider_type": self.collider.collider_type.name,
            "collision_layer": self.collider.collision_layer.name,
            "collsion_mask": [layer.name for layer in self.collider.collision_mask],
            "is_trigger": self.collider.is_trigger,
            # Material properties
            "density": self.material.density,
            "restitution": self.material.restitution,
            "friction": self.material.friction,
            "drag": self.material.drag,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BasePhysicsBody':
        """Create a physics body from a dictionary representation.

        Args:
            data: Dictionary with body properties
        Returns:
            Instance of IBasePhysicsBody
        """
        return cls(
            name=data.get('name', ''),
            id=data.get('id', ''),
            template_name=data.get('template_name'),
            tags=data.get('tags', []),
            body_type=BodyType.from_str(data.get('body_type', 'DYNAMIC')),
            enabled=data.get('enabled', True),
            sleeping=data.get('sleeping', False),
            mass=data.get('mass', 1.0),
            moment_of_inertia=data.get('moment_of_inertia', 1.0),
            velocity_x=data.get('velocity_x', 0.0),
            velocity_y=data.get('velocity_y', 0.0),
            acceleration_x=data.get('acceleration_x', 0.0),
            acceleration_y=data.get('acceleration_y', 0.0),
            angular_velocity=data.get('angular_velocity', 0.0),
            collider_type=ColliderType.from_str(data.get('collider_type', 'RECTANGLE')),
            collision_layer=CollisionLayer.from_str(data.get('collision_layer', 'DEFAULT')),
            collision_mask=[
                CollisionLayer.from_str(layer) for layer in data.get('collision_mask', [])
            ] if data.get('collision_mask') else None,
            is_trigger=data.get('is_trigger', False),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            width=data.get('width', 10.0),
            height=data.get('height', 10.0),
            roll=data.get('roll', 0.0),
            pitch=data.get('pitch', 0.0),
            yaw=data.get('yaw', 0.0),
            material=Material.from_dict(data['material']) if data.get('material') else None,
        )

    def to_dict(self) -> dict:
        """Convert physics body to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "id": self.id,
            "template_name": self.template_name,
            "tags": self.tags,
            "body_type": self.body_type.name,
            "enabled": self.enabled,
            "sleeping": self.sleeping,
            "mass": self.mass,
            "moment_of_inertia": self.moment_of_inertia,
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "acceleration_x": self.acceleration_x,
            "acceleration_y": self.acceleration_y,
            "angular_velocity": self.angular_velocity,
            "collider_type": self.collider.collider_type.name,
            "collision_layer": self.collider.collision_layer.name,
            "collision_mask": [m.name for m in self.collider.collision_mask],
            "is_trigger": self.collider.is_trigger,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "material": {
                "density": self.material.density,
                "restitution": self.material.restitution,
                "friction": self.material.friction,
                "drag": self.material.drag,
            },
        }

    @property
    def template_name(self) -> Optional[str]:
        """Get the template name used to create this body, if any."""
        return self._template_name

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
