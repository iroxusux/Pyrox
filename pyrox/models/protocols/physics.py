"""Physics body models and mixins.

Provides concrete implementations of physics protocols that can be mixed
into scene objects to add physics simulation capabilities.
"""
from typing import Self
from pyrox.interfaces import (
    ISpatial2D,
    IPhysicsBody2D,
    ICollider2D,
    IMaterial,
    IRigidBody2D,
    BodyType,
    ColliderType,
    CollisionLayer,
)
from pyrox.models.protocols.kinematic import Kinematic2D


class Material(IMaterial):
    """Concrete implementation of material properties."""

    def __init__(
        self,
        density: float = 1.0,
        restitution: float = 0.3,
        friction: float = 0.5,
        drag: float = 0.1,
    ):
        """Initialize material properties.

        Args:
            density: Mass per unit area (kg/m²)
            restitution: Bounciness (0.0-1.0)
            friction: Surface friction (0.0-1.0)
            drag: Air resistance coefficient
        """
        self._density = density
        self._restitution = max(0.0, min(1.0, restitution))
        self._friction = max(0.0, min(1.0, friction))
        self._drag = drag

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create Material from dictionary.

        Args:
            data: Dictionary with material properties
        Returns:
            Instance of IMaterial
        """
        return cls(
            density=data.get('density', 1.0),
            restitution=data.get('restitution', 0.3),
            friction=data.get('friction', 0.5),
            drag=data.get('drag', 0.1),
        )


class Collider2D(ICollider2D):
    """Standalone collider implementation.

    Can be used independently or composed into other objects.
    """

    def __init__(
        self,
        parent_body: ISpatial2D | None = None,
        collider_type: ColliderType = ColliderType.RECTANGLE,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: list[CollisionLayer] = list(),
        is_trigger: bool = False,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
    ):
        """Initialize collider.

        Args:
            parent_body: Optional reference to parent physics body (for delegation)
            collider_type: Shape of collision bounds
            collision_layer: Which layer this collider is on
            collision_mask: Which layers this collider can collide with
            is_trigger: Whether this is a trigger (no physics response)
            x, y: Position coordinates
            width, height: Size dimensions
        """
        self._parent_body = parent_body
        self._collider_type = collider_type
        self._collision_layer = collision_layer
        self._collision_mask = collision_mask or []
        self._is_trigger = is_trigger

        if not parent_body:
            self._x = x
            self._y = y
            self._width = width
            self._height = height


class RigidBody2D(
    Kinematic2D,
    IRigidBody2D,
):
    """Standalone rigid body implementation.

    Provides mass, velocity, and force management without requiring
    spatial attributes from the parent class.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        height: float = 0.0,
        width: float = 0.0,
        mass: float = 1.0,
        moment_of_inertia: float = 1.0,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        acceleration_x: float = 0.0,
        acceleration_y: float = 0.0,
        angular_velocity: float = 0.0,
    ):
        """Initialize rigid body.

        Args:
            mass: Mass in kilograms
            moment_of_inertia: Rotational inertia
            velocity_x: Initial X velocity
            velocity_y: Initial Y velocity
            angular_velocity: Initial angular velocity
        """
        Kinematic2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            acceleration_x=acceleration_x,
            acceleration_y=acceleration_y,
        )
        self._mass = mass
        self._inverse_mass = 1.0 / mass if mass > 0 else 0.0
        self._moment_of_inertia = moment_of_inertia
        self._angular_velocity = angular_velocity
        self._force_x = 0.0
        self._force_y = 0.0
        self._torque = 0.0


class PhysicsBody2D(
    IPhysicsBody2D,
    RigidBody2D
):
    """Complete standalone physics body implementation (2Dimensional).

    Combines all physics components (rigid body, collider, material) into
    a single object. Can be used independently without mixing into other classes.
    """

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        body_type: BodyType = BodyType.DYNAMIC,
        enabled: bool = True,
        sleeping: bool = False,

        # RigidBody parameters
        mass: float = 1.0,
        moment_of_inertia: float = 1.0,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        acceleration_x: float = 0.0,
        acceleration_y: float = 0.0,
        angular_velocity: float = 0.0,

        # Collider parameters
        collider_type: ColliderType = ColliderType.RECTANGLE,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: list[CollisionLayer] = list(),
        is_trigger: bool = False,


        # Material parameters
        material: IMaterial | None = None,
    ):
        """Initialize complete physics body.

        Args:
            body_type: Type of physics body
            enabled: Whether physics simulation is enabled
            sleeping: Whether the body is sleeping
            mass: Mass in kilograms
            moment_of_inertia: Rotational inertia
            velocity_x: Initial X velocity
            velocity_y: Initial Y velocity
            angular_velocity: Initial angular velocity
            collider_type: Shape of collision bounds
            collision_layer: Which layer this object is on
            collision_mask: Which layers this object collides with
            is_trigger: Whether this is a trigger (no physics response)
            x, y: Position coordinates
            width, height: Size dimensions
            material: Material properties (creates default if None)
        """
        # Physics body state
        if isinstance(body_type, str):
            body_type = BodyType.from_str(body_type)

        self._body_type = body_type
        self._enabled = enabled
        self._sleeping = sleeping

        RigidBody2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            mass=mass,
            moment_of_inertia=moment_of_inertia,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            acceleration_x=acceleration_x,
            acceleration_y=acceleration_y,
            angular_velocity=angular_velocity,
        )

        if isinstance(collider_type, str):
            collider_type = ColliderType.from_str(collider_type)

        if isinstance(collision_layer, str):
            collision_layer = CollisionLayer.from_str(collision_layer)

        if isinstance(collision_mask, list):
            collision_mask = [
                CollisionLayer.from_str(layer) if isinstance(layer, str) else layer
                for layer in collision_mask
            ]

        self._collider = Collider2D(
            parent_body=self,
            collider_type=collider_type,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=is_trigger,
        )

        self._material = material or Material()

    # Properties for convenience

    def get_inverse_mass(self) -> float:
        if self._body_type == BodyType.STATIC:
            return 0.0
        return super().get_inverse_mass()

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

        if max_y < other_min_y or min_y > other_max_y:
            return False

        return True
