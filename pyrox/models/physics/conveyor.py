"""Conveyor belt physics body implementation.

Provides a static or kinematic conveyor belt that moves objects
placed on top of it in a specified direction and speed.
"""
from enum import Enum
from typing import Any, Callable, List, Set
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class Direction(Enum):
    """Cardinal directions for conveyor movement.

    Attributes:
        NORTH: Upward movement (negative Y)
        SOUTH: Downward movement (positive Y)
        EAST: Rightward movement (positive X)
        WEST: Leftward movement (negative X)
    """
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

    @classmethod
    def from_str(cls, value: str) -> 'Direction':
        """Create Direction from string.

        Args:
            value: String representation (case-insensitive)

        Returns:
            Direction enum value
        """
        value_lower = value.lower()
        for direction in cls:
            if direction.value == value_lower:
                return direction
        raise ValueError(f"Invalid direction: {value}")

    def get_velocity_vector(self, speed: float) -> tuple[float, float]:
        """Get velocity vector for this direction.

        Args:
            speed: Speed magnitude

        Returns:
            Tuple of (vx, vy)
        """
        if self == Direction.NORTH:
            return (0.0, -speed)
        elif self == Direction.SOUTH:
            return (0.0, speed)
        elif self == Direction.EAST:
            return (speed, 0.0)
        elif self == Direction.WEST:
            return (-speed, 0.0)
        return (0.0, 0.0)


class ConveyorBody(BasePhysicsBody):
    """Conveyor belt that moves objects on top of it.

    A conveyor belt is typically a STATIC or KINEMATIC body that doesn't
    move itself, but applies velocity to dynamic objects sitting on top.

    Attributes:
        belt_velocity: (vx, vy) velocity applied to objects on the belt
        is_active: Whether the conveyor is currently running
        direction: Cardinal direction the belt moves (NORTH, SOUTH, EAST, WEST)
        belt_speed: Speed of the belt in units/second
    """

    def __init__(
        self,
        name: str = "Conveyor",
        template_name: str = "Conveyor Belt",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 20.0,
        direction: Direction | str = Direction.EAST,
        belt_speed: float = 50.0,  # units per second
        is_active: bool = True,
        body_type: BodyType = BodyType.STATIC,
        collision_layer: CollisionLayer = CollisionLayer.TERRAIN,
        collision_mask: List[CollisionLayer] | None = None,
        is_trigger: bool = False,
        material: Material | None = None,
        *args,
        **kwargs
    ):
        """Initialize conveyor belt.

        Args:
            name: Name of the conveyor
            x: X position
            y: Y position
            width: Width of the conveyor belt
            height: Height of the conveyor belt
            direction: Direction of belt movement (NORTH, SOUTH, EAST, WEST)
            belt_speed: Speed of the belt in units/second
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
            template_name=template_name,
            tags=["conveyor", "platform"],
            body_type=body_type,
            enabled=True,
            sleeping=False,
            mass=0.0 if body_type == BodyType.STATIC else 100.0,
            collider_type=ColliderType.RECTANGLE,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=is_trigger,
            x=x,
            y=y,
            width=width,
            height=height,
            material=material,
        )

        # Convert string to Direction enum if needed
        if isinstance(direction, str):
            self._direction = Direction.from_str(direction)
        else:
            self._direction = direction

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
        return self._direction.get_velocity_vector(self.belt_speed)

    @belt_velocity.setter
    def belt_velocity(self, velocity: tuple[float, float]) -> None:
        """Set the belt velocity vector.

        This will update the direction and speed based on the provided velocity.

        Args:
            velocity: (vx, vy) velocity tuple
        """
        vx, vy = velocity
        if vx > 0:
            self._direction = Direction.EAST
            self.belt_speed = vx
        elif vx < 0:
            self._direction = Direction.WEST
            self.belt_speed = -vx
        elif vy > 0:
            self._direction = Direction.SOUTH
            self.belt_speed = vy
        elif vy < 0:
            self._direction = Direction.NORTH
            self.belt_speed = -vy
        else:
            # No movement, keep current direction but set speed to 0
            self.belt_speed = 0.0

    @property
    def direction(self) -> Direction:
        """Get the belt direction.

        Returns:
            Direction enum value
        """
        return self._direction

    @direction.setter
    def direction(self, direction: Direction | str) -> None:
        """Set the belt direction.

        Args:
            direction: Direction enum or string ("north", "south", "east", "west")
        """
        if isinstance(direction, str):
            self._direction = Direction.from_str(direction)
        else:
            self._direction = direction

    def get_direction(self) -> str:
        """Get the belt direction as a string.

        Returns:
            Direction name (north, south, east, west)
        """
        return self._direction.value

    def set_direction(self, direction: Direction | str) -> None:
        """Set the belt direction.

        Args:
            direction: Direction enum or string ("north", "south", "east", "west")
        """
        if isinstance(direction, str):
            self._direction = Direction.from_str(direction)
        else:
            self._direction = direction

    def set_belt_speed(self, belt_speed: float) -> None:
        """Set the belt speed.

        Args:
            belt_speed: Speed in units/second (always positive)
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
        if other.is_on_top_of(self):
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

        if not other.is_on_top_of(self):
            # Object is touching but not on top (side collision)
            self._objects_on_belt.discard(other)
            return

        # Add to tracking set
        self._objects_on_belt.add(other)

        # Apply conveyor velocity to the object
        belt_vx, belt_vy = self.belt_velocity
        current_vx, current_vy = other.linear_velocity

        # Apply belt velocity while preserving perpendicular movement
        # For top-down: add belt velocity to current velocity
        # For side-view: replace horizontal, preserve vertical (falling)
        if self.is_trigger:  # Top-down mode
            other.set_linear_velocity(current_vx + belt_vx, current_vy + belt_vy)
        else:  # Side-scroller mode
            if abs(belt_vx) > 0:  # Moving horizontally
                other.set_linear_velocity(belt_vx, current_vy)
            else:  # Moving vertically
                other.set_linear_velocity(current_vx, belt_vy)

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

    def get_inputs(self) -> dict[str, Callable[..., None]]:
        """Get available input connections.

        Returns dict mapping input names to methods, properties, or other connection endpoints.
        """
        return {
            "activate": self.activate,
            "deactivate": self.deactivate,
            "toggle": self.toggle,
            "set_direction": self.set_direction,
            "set_belt_speed": self.set_belt_speed,
        }

    def get_properties(self) -> dict[str, Any]:
        """Get properties that can be edited in the properties panel.

        Returns:
            Dictionary mapping property names to their metadata
        """
        # Get base properties from parent
        properties = super().get_properties()

        # Add conveyor-specific properties
        properties.update({
            "direction": self.direction.value,  # Show as string in properties
            "belt_speed": self.belt_speed,
            "is_active": self.is_active,
        })

        return properties

    @classmethod
    def from_dict(cls, data: dict) -> 'ConveyorBody':
        """Create a ConveyorBody from a dictionary representation.

        Args:
            data: Dictionary with body properties
        Returns:
            Instance of ConveyorBody
        """
        # Handle direction field - it might be stored as string
        direction = data.get('direction', 'east')
        if isinstance(direction, str):
            direction = Direction.from_str(direction)

        return cls(
            name=data.get('name', 'Conveyor'),
            id=data.get('id', ''),
            template_name=data.get('template_name', 'Conveyor Belt'),
            tags=data.get('tags', ['conveyor', 'platform']),
            body_type=BodyType.from_str(data.get('body_type', 'STATIC')),
            enabled=data.get('enabled', True),
            sleeping=data.get('sleeping', False),
            mass=data.get('mass', 0.0),
            moment_of_inertia=data.get('moment_of_inertia', 1.0),
            velocity_x=data.get('velocity_x', 0.0),
            velocity_y=data.get('velocity_y', 0.0),
            acceleration_x=data.get('acceleration_x', 0.0),
            acceleration_y=data.get('acceleration_y', 0.0),
            angular_velocity=data.get('angular_velocity', 0.0),
            collider_type=ColliderType.from_str(data.get('collider_type', 'RECTANGLE')),
            collision_layer=CollisionLayer.from_str(data.get('collision_layer', 'TERRAIN')),
            collision_mask=[
                CollisionLayer.from_str(layer) for layer in data.get('collision_mask', [])
            ] if data.get('collision_mask') else None,
            is_trigger=data.get('is_trigger', False),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            width=data.get('width', 100.0),
            height=data.get('height', 20.0),
            roll=data.get('roll', 0.0),
            pitch=data.get('pitch', 0.0),
            yaw=data.get('yaw', 0.0),
            direction=direction,
            belt_speed=data.get('belt_speed', 50.0),
            is_active=data.get('is_active', True),
            material=Material.from_dict(data['material']) if data.get('material') else None,
        )

    def to_dict(self) -> dict:
        """Convert conveyor to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        # Get base body dict
        base_dict = super().to_dict()

        # Add conveyor-specific fields
        base_dict.update({
            "direction": self._direction.value,  # Save as string
            "belt_speed": self.belt_speed,
            "is_active": self.is_active,
        })

        return base_dict

    def __repr__(self) -> str:
        """String representation."""
        state = "ACTIVE" if self.is_active else "INACTIVE"
        dir_symbols = {
            Direction.NORTH: "↑",
            Direction.SOUTH: "↓",
            Direction.EAST: "→",
            Direction.WEST: "←",
        }
        dir_str = dir_symbols.get(self._direction, "?")
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
            "width": 200.0,
            "height": 20.0,
            "direction": Direction.EAST,
            "belt_speed": 50.0,
            "is_active": True,
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Platforms",
        description="A conveyor belt that moves objects placed on top of it.",
    )
)


# Register top-down conveyor template in factory
PhysicsSceneFactory.register_template(
    template_name="Top-Down Conveyor Belt",
    template=PhysicsSceneTemplate(
        name="Top-Down Conveyor Belt",
        body_class=ConveyorBody,
        default_kwargs={
            "width": 200.0,
            "height": 20.0,
            "direction": Direction.NORTH,
            "belt_speed": 50.0,
            "is_active": True,
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
            "collision_mask": [
                CollisionLayer.DEFAULT,
                CollisionLayer.PLAYER,
                CollisionLayer.ENEMY,
            ],
            "is_trigger": True,
        },
        category="Platforms",
        description="A top-down conveyor belt that moves objects in cardinal directions.",
    )
)
