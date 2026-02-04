"""Physics protocols for runtime simulation.

Defines interfaces for physics bodies, colliders, materials, and rigid body dynamics.
"""
from typing import (
    List,
    Protocol,
    runtime_checkable,
    Self,
    Tuple,
)
from enum import Enum, auto
from pyrox.interfaces.protocols.coord import IArea2D, IArea3D
from pyrox.interfaces.protocols.kinematic import IKinematic2D, IKinematic3D


class ColliderType(Enum):
    """Types of collision shapes."""
    RECTANGLE = auto()
    CIRCLE = auto()
    POLYGON = auto()
    NONE = auto()  # For non-collidable objects

    @classmethod
    def from_str(cls, value: str) -> 'ColliderType':
        """Create ColliderType from string representation."""
        mapping = {
            'RECTANGLE': cls.RECTANGLE,
            'CIRCLE': cls.CIRCLE,
            'POLYGON': cls.POLYGON,
            'NONE': cls.NONE,
        }
        return mapping[value.upper()]


class BodyType(Enum):
    """Physics body types."""
    STATIC = auto()      # Does not move (walls, terrain)
    DYNAMIC = auto()     # Fully simulated (player, enemies, projectiles)
    KINEMATIC = auto()   # Moves but isn't affected by forces (moving platforms)

    @classmethod
    def from_str(cls, value: str) -> 'BodyType':
        """Create BodyType from string representation."""
        mapping = {
            'STATIC': cls.STATIC,
            'DYNAMIC': cls.DYNAMIC,
            'KINEMATIC': cls.KINEMATIC,
        }
        return mapping[value.upper()]


class CollisionLayer(Enum):
    """Collision layers for selective collision detection."""
    DEFAULT = auto()
    PLAYER = auto()
    ENEMY = auto()
    PROJECTILE = auto()
    TERRAIN = auto()
    TRIGGER = auto()      # Overlap detection only, no physics response
    TRANSPARENT = auto()  # Visual only, no collision

    @classmethod
    def from_str(cls, value: str) -> 'CollisionLayer':
        """Create CollisionLayer from string representation."""
        mapping = {
            'DEFAULT': cls.DEFAULT,
            'PLAYER': cls.PLAYER,
            'ENEMY': cls.ENEMY,
            'PROJECTILE': cls.PROJECTILE,
            'TERRAIN': cls.TERRAIN,
            'TRIGGER': cls.TRIGGER,
            'TRANSPARENT': cls.TRANSPARENT,
        }
        return mapping[value.upper()]


@runtime_checkable
class IMaterial(Protocol):
    """Protocol for material properties that affect physics interactions."""

    @property
    def density(self) -> float:
        """Mass per unit area (kg/m²) or volume (kg/m³)."""
        return self.get_density()

    @density.setter
    def density(self, value: float) -> None:
        self.set_density(value)

    @property
    def restitution(self) -> float:
        """Bounciness (0.0 = no bounce, 1.0 = perfect bounce)."""
        return self.get_restitution()

    @restitution.setter
    def restitution(self, value: float) -> None:
        self.set_restitution(value)

    @property
    def friction(self) -> float:
        """Surface friction coefficient (0.0 = ice, 1.0 = rubber)."""
        return self.get_friction()

    @friction.setter
    def friction(self, value: float) -> None:
        self.set_friction(value)

    @property
    def drag(self) -> float:
        """Air/fluid resistance coefficient."""
        return self.get_drag()

    @drag.setter
    def drag(self, value: float) -> None:
        self.set_drag(value)

    def get_density(self) -> float: ...
    def set_density(self, value: float) -> None: ...
    def get_restitution(self) -> float: ...
    def set_restitution(self, value: float) -> None: ...
    def get_friction(self) -> float: ...
    def set_friction(self, value: float) -> None: ...
    def get_drag(self) -> float: ...
    def set_drag(self, value: float) -> None: ...
    @classmethod
    def from_dict(cls, data: dict) -> Self: ...


class ICollider2D(IArea2D):
    """Protocol for collision detection."""

    @property
    def collider_type(self) -> ColliderType:
        """The type of collider shape."""
        return self.get_collider_type()

    @property
    def collision_layer(self) -> CollisionLayer:
        """The collision layer this object belongs to."""
        return self.get_collision_layer()

    @property
    def collision_mask(self) -> List[CollisionLayer]:
        """Which layers this object can collide with."""
        return self.get_collision_mask()

    @property
    def is_trigger(self) -> bool:
        """Whether this collider is a trigger (no physics response, only detection)."""
        return self.get_is_trigger()

    @is_trigger.setter
    def is_trigger(self, value: bool) -> None:
        self.set_is_trigger(value)

    def get_collider_type(self) -> ColliderType: ...
    def set_collider_type(self, value: ColliderType) -> None: ...
    def get_collision_layer(self) -> CollisionLayer: ...
    def set_collision_layer(self, value: CollisionLayer) -> None: ...
    def get_collision_mask(self) -> List[CollisionLayer]: ...
    def set_collision_mask(self, value: List[CollisionLayer]) -> None: ...
    def get_is_trigger(self) -> bool: ...
    def set_is_trigger(self, value: bool) -> None: ...

    def check_collision(self, other: 'ICollider2D') -> bool:
        """Check if this collider intersects with another."""
        ...

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (min_x, min_y, max_x, max_y)."""
        ...


class ICollider3D(IArea3D):
    """Protocol for collision detection."""

    @property
    def collider_type(self) -> ColliderType:
        """The type of collider shape."""
        return self.get_collider_type()

    @property
    def collision_layer(self) -> CollisionLayer:
        """The collision layer this object belongs to."""
        return self.get_collision_layer()

    @property
    def collision_mask(self) -> List[CollisionLayer]:
        """Which layers this object can collide with."""
        return self.get_collision_mask()

    @property
    def is_trigger(self) -> bool:
        """Whether this collider is a trigger (no physics response, only detection)."""
        return self.get_is_trigger()

    @is_trigger.setter
    def is_trigger(self, value: bool) -> None:
        self.set_is_trigger(value)

    def get_collider_type(self) -> ColliderType: ...
    def set_collider_type(self, value: ColliderType) -> None: ...
    def get_collision_layer(self) -> CollisionLayer: ...
    def set_collision_layer(self, value: CollisionLayer) -> None: ...
    def get_collision_mask(self) -> List[CollisionLayer]: ...
    def set_collision_mask(self, value: List[CollisionLayer]) -> None: ...
    def get_is_trigger(self) -> bool: ...
    def set_is_trigger(self, value: bool) -> None: ...

    def check_collision(self, other: 'ICollider3D') -> bool:
        """Check if this collider intersects with another."""
        ...

    def get_bounds(self) -> Tuple[float, float, float, float, float, float]:
        """Get bounding box as (min_x, min_y, min_z, max_x, max_y, max_z)."""
        ...


class IRigidBody2D(IKinematic2D):
    """Protocol for rigid body physics properties."""

    @property
    def mass(self) -> float:
        """Mass in kilograms."""
        return self.get_mass()

    @mass.setter
    def mass(self, value: float) -> None:
        self.set_mass(value)

    @property
    def inverse_mass(self) -> float:
        """Inverse mass (0 for infinite mass/static bodies)."""
        return self.get_inverse_mass()

    @property
    def moment_of_inertia(self) -> float:
        """Rotational inertia."""
        return self.get_moment_of_inertia()

    @property
    def angular_velocity(self) -> float:
        """Angular velocity in rad/s."""
        return self.get_angular_velocity()

    @property
    def linear_acceleration(self) -> Tuple[float, float]:
        """Linear acceleration (ax, ay) in m/s²."""
        return self.get_linear_acceleration()

    @property
    def force(self) -> Tuple[float, float]:
        """Accumulated force (fx, fy) in Newtons."""
        return self.get_force()

    @property
    def torque(self) -> float:
        """Accumulated torque in N⋅m."""
        return self.get_torque()

    def get_mass(self) -> float: ...
    def set_mass(self, value: float) -> None: ...
    def get_inverse_mass(self) -> float: ...
    def get_moment_of_inertia(self) -> float: ...
    def set_moment_of_inertia(self, value: float) -> None: ...
    def get_angular_velocity(self) -> float: ...
    def set_angular_velocity(self, value: float) -> None: ...
    def get_force(self) -> Tuple[float, float]: ...
    def set_force(self, fx: float, fy: float) -> None: ...
    def get_torque(self) -> float: ...
    def set_torque(self, value: float) -> None: ...
    def apply_force(self, fx: float, fy: float) -> None: ...
    def apply_impulse(self, jx: float, jy: float) -> None: ...
    def apply_torque(self, torque: float) -> None: ...
    def clear_forces(self) -> None: ...


class IRigidBody3D(IKinematic3D):
    """Protocol for rigid body physics properties."""

    @property
    def mass(self) -> float:
        """Mass in kilograms."""
        return self.get_mass()

    @mass.setter
    def mass(self, value: float) -> None:
        self.set_mass(value)

    @property
    def inverse_mass(self) -> float:
        """Inverse mass (0 for infinite mass/static bodies)."""
        return self.get_inverse_mass()

    @property
    def moment_of_inertia(self) -> float:
        """Rotational inertia."""
        return self.get_moment_of_inertia()

    @property
    def angular_velocity(self) -> float:
        """Angular velocity in rad/s."""
        return self.get_angular_velocity()

    @property
    def force(self) -> Tuple[float, float, float]:
        """Accumulated force (fx, fy) in Newtons."""
        return self.get_force()

    @property
    def torque(self) -> float:
        """Accumulated torque in N⋅m."""
        return self.get_torque()

    def get_mass(self) -> float: ...
    def set_mass(self, value: float) -> None: ...
    def get_inverse_mass(self) -> float: ...
    def get_moment_of_inertia(self) -> float: ...
    def set_moment_of_inertia(self, value: float) -> None: ...
    def get_angular_velocity(self) -> float: ...
    def set_angular_velocity(self, value: float) -> None: ...
    def get_force(self) -> Tuple[float, float, float]: ...
    def set_force(self, fx: float, fy: float) -> None: ...
    def get_torque(self) -> float: ...
    def set_torque(self, value: float) -> None: ...
    def apply_force(self, fx: float, fy: float) -> None: ...
    def apply_impulse(self, jx: float, jy: float) -> None: ...
    def apply_torque(self, torque: float) -> None: ...
    def clear_forces(self) -> None: ...


class IPhysicsBody2D(
    IRigidBody2D
):
    """Protocol for complete physics body with collision and dynamics."""

    @property
    def body_type(self) -> BodyType:
        """The type of physics body."""
        return self.get_body_type()

    @body_type.setter
    def body_type(self, value: BodyType) -> None:
        self.set_body_type(value)

    @property
    def collider(self) -> ICollider2D:
        """The collider associated with this physics body."""
        return self.get_collider()

    @property
    def enabled(self) -> bool:
        """Whether physics simulation is enabled for this body."""
        return self.get_enabled()

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.set_enabled(value)

    @property
    def material(self) -> IMaterial:
        """The material properties of this physics body."""
        return self.get_material()

    @property
    def rigid_body(self) -> IRigidBody2D:
        """The rigid body component of this physics body."""
        return self.get_rigid_body()

    @property
    def sleeping(self) -> bool:
        """Whether the body is sleeping (optimization for stationary objects)."""
        return self.get_sleeping()

    @sleeping.setter
    def sleeping(self, value: bool) -> None:
        self.set_sleeping(value)

    def get_body_type(self) -> BodyType: ...
    def set_body_type(self, value: BodyType) -> None: ...
    def get_enabled(self) -> bool: ...
    def set_enabled(self, value: bool) -> None: ...
    def get_collider(self) -> ICollider2D: ...
    def set_collider(self, collider: ICollider2D) -> None: ...
    def get_rigid_body(self) -> IRigidBody2D: ...
    def set_rigid_body(self, rigid_body: IRigidBody2D) -> None: ...
    def get_material(self) -> IMaterial: ...
    def set_material(self, material: IMaterial) -> None: ...
    def get_sleeping(self) -> bool: ...
    def set_sleeping(self, value: bool) -> None: ...
    def update(self, dt: float) -> None: ...
    def on_collision_enter(self, other: 'IPhysicsBody2D') -> None: ...
    def on_collision_stay(self, other: 'IPhysicsBody2D') -> None: ...
    def on_collision_exit(self, other: 'IPhysicsBody2D') -> None: ...
    def is_on_top_of(self, other: 'IPhysicsBody2D') -> bool: ...


@runtime_checkable
class IPhysicsEngine(Protocol):
    """Protocol for the physics simulation engine."""

    @property
    def gravity(self) -> Tuple[float, float]:
        """Global gravity vector (gx, gy) in m/s²."""
        return self.get_gravity()

    @property
    def time_scale(self) -> float:
        """Time scale multiplier (1.0 = normal, 0.5 = slow-mo, 2.0 = fast-forward)."""
        return self.get_time_scale()

    @property
    def physics_step(self) -> float:
        """Fixed physics timestep in seconds."""
        return self.get_physics_step()

    def get_gravity(self) -> Tuple[float, float]: ...
    def set_gravity(self, gx: float, gy: float) -> None: ...
    def get_time_scale(self) -> float: ...
    def set_time_scale(self, value: float) -> None: ...
    def get_physics_step(self) -> float: ...
    def set_physics_step(self, value: float) -> None: ...

    def register_body(self, body: IPhysicsBody2D) -> None:
        """Register a physics body with the engine."""
        ...

    def unregister_body(self, body: IPhysicsBody2D) -> None:
        """Remove a physics body from the engine."""
        ...

    def step(self, dt: float) -> None:
        """Advance physics simulation by dt seconds."""
        ...

    def reset(self) -> None:
        """Reset the physics engine to initial state."""
        ...


__all__ = [
    'ColliderType',
    'BodyType',
    'CollisionLayer',
    'IMaterial',
    'ICollider2D',
    'ICollider3D',
    'IRigidBody2D',
    'IRigidBody3D',
    'IPhysicsBody2D',
    'IPhysicsEngine',
]
