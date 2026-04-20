"""Physics protocols for runtime simulation.

Defines interfaces for physics bodies, colliders, materials, and rigid body dynamics.
"""
from typing import (
    Protocol,
    Self,
)
from enum import Enum, auto
from pyrox.interfaces.protocols.coord import IArea2D
from pyrox.interfaces.protocols.kinematic import IKinematic2D


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
    SENSOR = auto()       # For invisible triggers and sensors
    TERRAIN = auto()
    TRIGGER = auto()      # Overlap detection only, no physics response
    TRANSPARENT = auto()  # Visual only, no collision
    UI = auto()           # In-scene UI elements, never collides with anything

    @classmethod
    def from_str(cls, value: str) -> 'CollisionLayer':
        """Create CollisionLayer from string representation."""
        mapping = {
            'DEFAULT': cls.DEFAULT,
            'PLAYER': cls.PLAYER,
            'ENEMY': cls.ENEMY,
            'PROJECTILE': cls.PROJECTILE,
            'SENSOR': cls.SENSOR,
            'TERRAIN': cls.TERRAIN,
            'TRIGGER': cls.TRIGGER,
            'TRANSPARENT': cls.TRANSPARENT,
            'UI': cls.UI,
        }
        return mapping[value.upper()]


class IMaterial:
    """Protocol for material properties that affect physics interactions."""
    _density: float
    _restitution: float
    _friction: float
    _drag: float

    def get_density(self) -> float:
        return self._density

    def set_density(self, value: float) -> None:
        if value < 0:
            raise ValueError("Density cannot be negative")
        self._density = value

    @property
    def density(self) -> float:
        """Mass per unit area (kg/m²) or volume (kg/m³)."""
        return self.get_density()

    @density.setter
    def density(self, value: float) -> None:
        self.set_density(value)

    def get_restitution(self) -> float:
        return self._restitution

    def set_restitution(self, value: float) -> None:
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        self._restitution = value

    @property
    def restitution(self) -> float:
        """Bounciness (0.0 = no bounce, 1.0 = perfect bounce)."""
        return self.get_restitution()

    @restitution.setter
    def restitution(self, value: float) -> None:
        self.set_restitution(value)

    def get_friction(self) -> float:
        return self._friction

    def set_friction(self, value: float) -> None:
        if value < 0.0:
            value = 0.0
        elif value > 1.0:
            value = 1.0
        self._friction = value

    @property
    def friction(self) -> float:
        """Surface friction coefficient (0.0 = ice, 1.0 = rubber)."""
        return self.get_friction()

    @friction.setter
    def friction(self, value: float) -> None:
        self.set_friction(value)

    def get_drag(self) -> float:
        return self._drag

    def set_drag(self, value: float) -> None:
        if value < 0:
            raise ValueError("Drag cannot be negative")
        self._drag = value

    @property
    def drag(self) -> float:
        """Air/fluid resistance coefficient."""
        return self.get_drag()

    @drag.setter
    def drag(self, value: float) -> None:
        self.set_drag(value)

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        raise NotImplementedError("from_dict method must be implemented by subclasses")


class ICollider2D(IArea2D):
    """Protocol for collision detection."""
    _collider_type: ColliderType
    _collision_layer: CollisionLayer
    _collision_mask: list[CollisionLayer]
    _is_trigger: bool
    _parent_body: 'IPhysicsBody2D | None'

    def get_collider_type(self) -> ColliderType:
        return self._collider_type

    def set_collider_type(self, value: ColliderType) -> None:
        if not isinstance(value, ColliderType):
            raise ValueError(f"Invalid collider type: {value}")
        self._collider_type = value

    @property
    def collider_type(self) -> ColliderType:
        """The type of collider shape."""
        return self.get_collider_type()

    @collider_type.setter
    def collider_type(self, value: ColliderType) -> None:
        self.set_collider_type(value)

    def get_collision_layer(self) -> CollisionLayer:
        return self._collision_layer

    def set_collision_layer(self, value: CollisionLayer) -> None:
        if not isinstance(value, CollisionLayer):
            raise ValueError(f"Invalid collision layer: {value}")
        self._collision_layer = value

    @property
    def collision_layer(self) -> CollisionLayer:
        """The collision layer this object belongs to."""
        return self.get_collision_layer()

    @collision_layer.setter
    def collision_layer(self, value: CollisionLayer) -> None:
        self.set_collision_layer(value)

    def get_collision_mask(self) -> list[CollisionLayer]:
        return self._collision_mask

    def set_collision_mask(self, value: list[CollisionLayer]) -> None:
        if not all(isinstance(layer, CollisionLayer) for layer in value):
            raise ValueError("Collision mask must be a list of CollisionLayer enums")
        self._collision_mask = value

    @property
    def collision_mask(self) -> list[CollisionLayer]:
        """Which layers this object can collide with."""
        return self.get_collision_mask()

    @collision_mask.setter
    def collision_mask(self, value: list[CollisionLayer]) -> None:
        self.set_collision_mask(value)

    def get_is_trigger(self) -> bool:
        return self._is_trigger

    def set_is_trigger(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("is_trigger must be a boolean value")
        self._is_trigger = value

    @property
    def is_trigger(self) -> bool:
        """Whether this collider is a trigger (no physics response, only detection)."""
        return self.get_is_trigger()

    @is_trigger.setter
    def is_trigger(self, value: bool) -> None:
        self.set_is_trigger(value)

    def check_collision(self, other: 'ICollider2D') -> bool:
        """Check if this collider intersects with another."""
        my_bounds = self.get_bounds()
        other_bounds = other.get_bounds()

        min_ax, min_ay, max_ax, max_ay = my_bounds
        min_bx, min_by, max_bx, max_by = other_bounds

        # AABB intersection test
        return not (max_ax < min_bx or min_ax > max_bx or max_ay < min_by or min_ay > max_by)

    def get_parent_body(self) -> 'IPhysicsBody2D | None':
        return self._parent_body

    def set_parent_body(self, body: 'IPhysicsBody2D | None') -> None:
        if body is not None and not isinstance(body, IPhysicsBody2D):
            raise ValueError("Parent body must be an instance of IPhysicsBody2D or None")
        self._parent_body = body

    @property
    def parent_body(self) -> 'IPhysicsBody2D | None':
        """The physics body this collider is attached to, if any."""
        return self.get_parent_body()

    @parent_body.setter
    def parent_body(self, body: 'IPhysicsBody2D | None') -> None:
        self.set_parent_body(body)

    # ------------------------------------------------------------------
    # Overrides for ICoord to provide parent coordinates if attached to a physics body
    # ------------------------------------------------------------------

    def get_x(self) -> float:
        if self.parent_body:
            return self.parent_body.get_x()
        return super().get_x()

    def set_x(self, x: float) -> None:
        if self.parent_body:
            self.parent_body.set_x(x)
        else:
            super().set_x(x)

    def get_y(self) -> float:
        if self.parent_body:
            return self.parent_body.get_y()
        return super().get_y()

    def set_y(self, y: float) -> None:
        if self.parent_body:
            self.parent_body.set_y(y)
        else:
            super().set_y(y)

    # ------------------------------------------------------------------
    # Overrides for IArea2D to provide parent area if attached to a physics body
    # ------------------------------------------------------------------

    def get_width(self) -> float:
        if self.parent_body:
            return self.parent_body.get_width()
        return super().get_width()

    def set_width(self, width: float) -> None:
        if self.parent_body:
            self.parent_body.set_width(width)
        else:
            super().set_width(width)

    def get_height(self) -> float:
        if self.parent_body:
            return self.parent_body.get_height()
        return super().get_height()

    def set_height(self, height: float) -> None:
        if self.parent_body:
            self.parent_body.set_height(height)
        else:
            super().set_height(height)


class IRigidBody2D(IKinematic2D):
    """Protocol for rigid body physics properties."""
    _mass: float
    _moment_of_inertia: float
    _angular_velocity: float
    _force_x: float
    _force_y: float
    _torque: float

    def get_mass(self) -> float:
        return self._mass

    def set_mass(self, value: float) -> None:
        if value < 0:
            raise ValueError("Mass cannot be negative")
        self._mass = value

    @property
    def mass(self) -> float:
        """Mass in kilograms."""
        return self.get_mass()

    @mass.setter
    def mass(self, value: float) -> None:
        self.set_mass(value)

    def get_inverse_mass(self) -> float:
        """Inverse mass (0 for infinite mass/static bodies)."""
        if self._mass == 0:
            return 0.0
        return 1.0 / self._mass

    @property
    def inverse_mass(self) -> float:
        """Inverse mass (0 for infinite mass/static bodies)."""
        return self.get_inverse_mass()

    def get_moment_of_inertia(self) -> float:
        return self._moment_of_inertia

    def set_moment_of_inertia(self, value: float) -> None:
        if value < 0:
            raise ValueError("Moment of inertia cannot be negative")
        self._moment_of_inertia = value

    @property
    def moment_of_inertia(self) -> float:
        """Rotational inertia."""
        return self.get_moment_of_inertia()

    @moment_of_inertia.setter
    def moment_of_inertia(self, value: float) -> None:
        self.set_moment_of_inertia(value)

    def get_angular_velocity(self) -> float:
        return self._angular_velocity

    def set_angular_velocity(self, value: float) -> None:
        self._angular_velocity = value

    @property
    def angular_velocity(self) -> float:
        """Angular velocity in rad/s."""
        return self.get_angular_velocity()

    @angular_velocity.setter
    def angular_velocity(self, value: float) -> None:
        self.set_angular_velocity(value)

    def get_force(self) -> tuple[float, float]:
        return self._force_x, self._force_y

    def set_force(self, fx: float, fy: float) -> None:
        self._force_x = fx
        self._force_y = fy

    @property
    def force(self) -> tuple[float, float]:
        """Accumulated force (fx, fy) in Newtons."""
        return self.get_force()

    @force.setter
    def force(self, value: tuple[float, float]) -> None:
        self.set_force(value[0], value[1])

    def get_torque(self) -> float:
        return self._torque

    def set_torque(self, value: float) -> None:
        self._torque = value

    @property
    def torque(self) -> float:
        """Accumulated torque in N⋅m."""
        return self.get_torque()

    @torque.setter
    def torque(self, value: float) -> None:
        self.set_torque(value)

    def apply_force(self, fx: float, fy: float) -> None:
        self._force_x += fx
        self._force_y += fy

    def apply_impulse(self, jx: float, jy: float) -> None:
        if self.inverse_mass > 0:
            self._velocity_x += jx * self.inverse_mass
            self._velocity_y += jy * self.inverse_mass

    def apply_torque(self, torque: float) -> None:
        self._torque += torque

    def clear_forces(self) -> None:
        self._force_x = 0.0
        self._force_y = 0.0
        self._torque = 0.0


class IPhysicsBody2D(IRigidBody2D):
    """Protocol for complete physics body with collision and dynamics."""
    _body_type: BodyType
    _collider: ICollider2D
    _enabled: bool
    _material: IMaterial
    _rigid_body: IRigidBody2D
    _sleeping: bool

    def get_body_type(self) -> BodyType:
        return self._body_type

    def set_body_type(self, value: BodyType) -> None:
        if not isinstance(value, BodyType):
            raise ValueError(f"Invalid body type: {value}")
        self._body_type = value

    @property
    def body_type(self) -> BodyType:
        """The type of physics body."""
        return self.get_body_type()

    @body_type.setter
    def body_type(self, value: BodyType) -> None:
        self.set_body_type(value)

    def get_collider(self) -> ICollider2D:
        return self._collider

    def set_collider(self, collider: ICollider2D) -> None:
        if not isinstance(collider, ICollider2D):
            raise ValueError("Collider must implement ICollider2D protocol")
        self._collider = collider

    @property
    def collider(self) -> ICollider2D:
        """The collider associated with this physics body."""
        return self.get_collider()

    @collider.setter
    def collider(self, value: ICollider2D) -> None:
        self.set_collider(value)

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        if not isinstance(enabled, bool):
            raise ValueError("Enabled must be a boolean value")
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        """Whether physics simulation is enabled for this body."""
        return self.get_enabled()

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        self.set_enabled(enabled)

    def get_material(self) -> IMaterial:
        return self._material

    def set_material(self, material: IMaterial) -> None:
        if not isinstance(material, IMaterial):
            raise ValueError("Material must implement IMaterial protocol")
        self._material = material

    @property
    def material(self) -> IMaterial:
        """The material properties of this physics body."""
        return self.get_material()

    @material.setter
    def material(self, value: IMaterial) -> None:
        self.set_material(value)

    def get_rigid_body(self) -> IRigidBody2D:
        return self._rigid_body

    def set_rigid_body(self, rigid_body: IRigidBody2D) -> None:
        if not isinstance(rigid_body, IRigidBody2D):
            raise ValueError("Rigid body must implement IRigidBody2D protocol")
        self._rigid_body = rigid_body

    @property
    def rigid_body(self) -> IRigidBody2D:
        """The rigid body component of this physics body."""
        return self.get_rigid_body()

    @rigid_body.setter
    def rigid_body(self, value: IRigidBody2D) -> None:
        self.set_rigid_body(value)

    def get_sleeping(self) -> bool:
        return self._sleeping

    def set_sleeping(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Sleeping must be a boolean value")
        self._sleeping = value

    @property
    def sleeping(self) -> bool:
        """Whether the body is sleeping (optimization for stationary objects)."""
        return self.get_sleeping()

    @sleeping.setter
    def sleeping(self, value: bool) -> None:
        self.set_sleeping(value)

    def update(self, dt: float) -> None: pass
    def on_collision_enter(self, other: 'IPhysicsBody2D') -> None: pass
    def on_collision_stay(self, other: 'IPhysicsBody2D') -> None: pass
    def on_collision_exit(self, other: 'IPhysicsBody2D') -> None: pass

    def is_on_top_of(self, other: 'IPhysicsBody2D') -> bool:
        # Get bounding boxes
        min_x, min_y, max_x, max_y = self.get_bounds()
        other_min_x, other_min_y, other_max_x, other_max_y = other.get_bounds()

        # Check if horizontally aligned (overlapping in X)
        if max_x < other_min_x or min_x > other_max_x:
            return False

        if max_y < other_min_y or min_y > other_max_y:
            return False

        return True

    # ------------------------------------------------------------------
    # ICollider2D delegation for convenience access to collider properties directly from the physics body
    # ------------------------------------------------------------------

    def get_collider_type(self) -> ColliderType:
        return self._collider.get_collider_type()

    def set_collider_type(self, value: ColliderType) -> None:
        self._collider.set_collider_type(value)

    @property
    def collider_type(self) -> ColliderType:
        """The type of collider shape."""
        return self.get_collider_type()

    @collider_type.setter
    def collider_type(self, value: ColliderType) -> None:
        self.set_collider_type(value)

    def get_collision_layer(self) -> CollisionLayer:
        return self._collider.get_collision_layer()

    def set_collision_layer(self, value: CollisionLayer) -> None:
        self._collider.set_collision_layer(value)

    @property
    def collision_layer(self) -> CollisionLayer:
        """The collision layer this object belongs to."""
        return self.get_collision_layer()

    @collision_layer.setter
    def collision_layer(self, value: CollisionLayer) -> None:
        self.set_collision_layer(value)

    def get_collision_mask(self) -> list[CollisionLayer]:
        return self._collider.get_collision_mask()

    def set_collision_mask(self, value: list[CollisionLayer]) -> None:
        self._collider.set_collision_mask(value)

    @property
    def collision_mask(self) -> list[CollisionLayer]:
        """Which layers this object can collide with."""
        return self.get_collision_mask()

    @collision_mask.setter
    def collision_mask(self, value: list[CollisionLayer]) -> None:
        self.set_collision_mask(value)

    def get_is_trigger(self) -> bool:
        return self._collider.get_is_trigger()

    def set_is_trigger(self, value: bool) -> None:
        self._collider.set_is_trigger(value)

    @property
    def is_trigger(self) -> bool:
        """Whether this collider is a trigger (no physics response, only detection)."""
        return self.get_is_trigger()

    @is_trigger.setter
    def is_trigger(self, value: bool) -> None:
        self.set_is_trigger(value)

    def check_collision(self, other: ICollider2D) -> bool:
        return self._collider.check_collision(other)

    def get_bounds(self) -> tuple[float, float, float, float]:
        return self._collider.get_bounds()

    # ------------------------------------------------------------------
    # IMaterial delegation for convenience access to material properties directly from the physics body
    # ------------------------------------------------------------------

    def get_density(self) -> float:
        return self._material.get_density()

    def set_density(self, value: float) -> None:
        self._material.set_density(value)

    @property
    def density(self) -> float:
        """Mass per unit area (kg/m²) or volume (kg/m³)."""
        return self.get_density()

    @density.setter
    def density(self, value: float) -> None:
        self.set_density(value)

    def get_restitution(self) -> float:
        return self._material.get_restitution()

    def set_restitution(self, value: float) -> None:
        self._material.set_restitution(value)

    @property
    def restitution(self) -> float:
        """Bounciness (0.0 = no bounce, 1.0 = perfect bounce)."""
        return self.get_restitution()

    @restitution.setter
    def restitution(self, value: float) -> None:
        self.set_restitution(value)

    def get_friction(self) -> float:
        return self._material.get_friction()

    def set_friction(self, value: float) -> None:
        self._material.set_friction(value)

    @property
    def friction(self) -> float:
        """Surface friction coefficient (0.0 = ice, 1.0 = rubber)."""
        return self.get_friction()

    @friction.setter
    def friction(self, value: float) -> None:
        self.set_friction(value)

    def get_drag(self) -> float:
        return self._material.get_drag()

    def set_drag(self, value: float) -> None:
        self._material.set_drag(value)

    @property
    def drag(self) -> float:
        """Air/fluid resistance coefficient."""
        return self.get_drag()

    @drag.setter
    def drag(self, value: float) -> None:
        self.set_drag(value)


class IPhysicsEngine(Protocol):
    """Protocol for the physics simulation engine."""

    @property
    def gravity(self) -> tuple[float, float]:
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

    def get_gravity(self) -> tuple[float, float]: ...
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
    'IRigidBody2D',
    'IPhysicsBody2D',
    'IPhysicsEngine',
]
