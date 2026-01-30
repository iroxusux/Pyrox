"""Physics body models and mixins.

Provides concrete implementations of physics protocols that can be mixed
into scene objects to add physics simulation capabilities.
"""
from typing import Tuple, List
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
from pyrox.models.protocols.coord import Area2D
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

    def get_density(self) -> float:
        return self._density

    def set_density(self, value: float) -> None:
        if value < 0:
            raise ValueError("Density must be non-negative")
        self._density = value

    def get_restitution(self) -> float:
        return self._restitution

    def set_restitution(self, value: float) -> None:
        self._restitution = max(0.0, min(1.0, value))

    def get_friction(self) -> float:
        return self._friction

    def set_friction(self, value: float) -> None:
        self._friction = max(0.0, min(1.0, value))

    def get_drag(self) -> float:
        return self._drag

    def set_drag(self, value: float) -> None:
        if value < 0:
            raise ValueError("Drag must be non-negative")
        self._drag = value


class Collider2D(
    ICollider2D,
    Area2D,
):
    """Standalone collider implementation.

    Can be used independently or composed into other objects.
    """

    def __init__(
        self,
        parent: ISpatial2D | None = None,
        collider_type: ColliderType = ColliderType.RECTANGLE,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: List[CollisionLayer] | None = None,
        is_trigger: bool = False,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
    ):
        """Initialize collider.

        Args:
            collider_type: Shape of collision bounds
            collision_layer: Which layer this collider is on
            collision_mask: Which layers this collider can collide with
            is_trigger: Whether this is a trigger (no physics response)
            x, y: Position coordinates
            width, height: Size dimensions
        """
        self._parent = parent
        self._collider_type = collider_type
        self._collision_layer = collision_layer
        self._collision_mask = collision_mask or []
        self._is_trigger = is_trigger
        Area2D.__init__(
            self,
            x=x if parent is None else parent.x,
            y=y if parent is None else parent.y,
            width=width,
            height=height,
        )

    def get_x(self) -> float:
        if self.parent:
            return self.parent.x
        return self._x

    def set_x(self, x: float) -> None:
        if not self.parent:
            self._x = x

    def get_y(self) -> float:
        if self.parent:
            return self.parent.y
        return self._y

    def set_y(self, y: float) -> None:
        if not self.parent:
            self._y = y

    def get_width(self) -> float:
        if self.parent:
            return self.parent.width
        return self._width

    def set_width(self, width: float) -> None:
        if not self.parent:
            self._width = width

    def get_height(self) -> float:
        if self.parent:
            return self.parent.height
        return self._height

    def set_height(self, height: float) -> None:
        if not self.parent:
            self._height = height

    def get_collider_type(self) -> ColliderType:
        return self._collider_type

    def set_collider_type(self, value: ColliderType) -> None:
        self._collider_type = value

    def get_collision_layer(self) -> CollisionLayer:
        return self._collision_layer

    def set_collision_layer(self, value: CollisionLayer) -> None:
        self._collision_layer = value

    def get_collision_mask(self) -> List[CollisionLayer]:
        return self._collision_mask

    def set_collision_mask(self, value: List[CollisionLayer]) -> None:
        self._collision_mask = value

    def get_is_trigger(self) -> bool:
        return self._is_trigger

    def set_is_trigger(self, value: bool) -> None:
        self._is_trigger = value

    def check_collision(self, other: ICollider2D) -> bool:
        """Check if this collider intersects with another."""
        my_bounds = self.get_bounds()
        other_bounds = other.get_bounds()

        min_ax, min_ay, max_ax, max_ay = my_bounds
        min_bx, min_by, max_bx, max_by = other_bounds

        # AABB intersection test
        return not (max_ax < min_bx or min_ax > max_bx or max_ay < min_by or min_ay > max_by)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (min_x, min_y, max_x, max_y)."""
        return (
            self.x,
            self.y,
            self.x + self.width,
            self.y + self.height
        )

    # Properties for convenience

    @property
    def parent(self) -> ISpatial2D | None:
        return self._parent

    @property
    def collider_type(self) -> ColliderType:
        return self.get_collider_type()

    @collider_type.setter
    def collider_type(self, value: ColliderType) -> None:
        self.set_collider_type(value)

    @property
    def collision_layer(self) -> CollisionLayer:
        return self.get_collision_layer()

    @collision_layer.setter
    def collision_layer(self, value: CollisionLayer) -> None:
        self.set_collision_layer(value)

    @property
    def collision_mask(self) -> List[CollisionLayer]:
        return self.get_collision_mask()

    @collision_mask.setter
    def collision_mask(self, value: List[CollisionLayer]) -> None:
        self.set_collision_mask(value)

    @property
    def is_trigger(self) -> bool:
        return self.get_is_trigger()

    @is_trigger.setter
    def is_trigger(self, value: bool) -> None:
        self.set_is_trigger(value)


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
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
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
            roll=roll,
            pitch=pitch,
            yaw=yaw,
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

    def get_mass(self) -> float:
        return self._mass

    def set_mass(self, value: float) -> None:
        if value < 0:
            raise ValueError("Mass must be non-negative")
        self._mass = value
        self._inverse_mass = 1.0 / value if value > 0 else 0.0
        # Clear accumulated forces when mass changes to prevent numerical instability
        # This is critical when changing from mass=0 to mass>0
        self.clear_forces()

    def get_inverse_mass(self) -> float:
        return self._inverse_mass

    def get_moment_of_inertia(self) -> float:
        return self._moment_of_inertia

    def set_moment_of_inertia(self, value: float) -> None:
        self._moment_of_inertia = value

    def get_angular_velocity(self) -> float:
        return self._angular_velocity

    def set_angular_velocity(self, value: float) -> None:
        self._angular_velocity = value

    def get_force(self) -> Tuple[float, float]:
        return (self._force_x, self._force_y)

    def set_force(self, fx: float, fy: float) -> None:
        self._force_x = fx
        self._force_y = fy

    def get_torque(self) -> float:
        return self._torque

    def set_torque(self, value: float) -> None:
        self._torque = value

    def apply_force(self, fx: float, fy: float) -> None:
        """Apply a force to the center of mass."""
        self._force_x += fx
        self._force_y += fy

    def apply_impulse(self, jx: float, jy: float) -> None:
        """Apply an instantaneous impulse (immediate velocity change)."""
        if self._inverse_mass > 0:
            self._velocity_x += jx * self._inverse_mass
            self._velocity_y += jy * self._inverse_mass

    def apply_torque(self, torque: float) -> None:
        """Apply a rotational force."""
        self._torque += torque

    def clear_forces(self) -> None:
        """Clear all accumulated forces and torques."""
        self._force_x = 0.0
        self._force_y = 0.0
        self._torque = 0.0

    # Properties for convenience

    @property
    def mass(self) -> float:
        return self.get_mass()

    @mass.setter
    def mass(self, value: float) -> None:
        self.set_mass(value)

    @property
    def inverse_mass(self) -> float:
        return self.get_inverse_mass()

    @property
    def moment_of_inertia(self) -> float:
        return self.get_moment_of_inertia()

    @moment_of_inertia.setter
    def moment_of_inertia(self, value: float) -> None:
        self.set_moment_of_inertia(value)

    @property
    def angular_velocity(self) -> float:
        return self.get_angular_velocity()

    @angular_velocity.setter
    def angular_velocity(self, value: float) -> None:
        self.set_angular_velocity(value)

    @property
    def force(self) -> Tuple[float, float]:
        return self.get_force()

    @force.setter
    def force(self, value: Tuple[float, float]) -> None:
        self.set_force(value[0], value[1])

    @property
    def torque(self) -> float:
        return self.get_torque()

    @torque.setter
    def torque(self, value: float) -> None:
        self.set_torque(value)


class PhysicsBody2D(
    IPhysicsBody2D,
    ICollider2D,
    IMaterial,
    RigidBody2D
):
    """Complete standalone physics body implementation (2Dimensional).

    Combines all physics components (rigid body, collider, material) into
    a single object. Can be used independently without mixing into other classes.
    """

    def __init__(
        self,
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
        collision_mask: List[CollisionLayer] | None = None,
        is_trigger: bool = False,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        # Material parameters
        material: Material | None = None,
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
        Kinematic2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            acceleration_x=acceleration_x,
            acceleration_y=acceleration_y,
        )

        # Physics body state
        self._body_type = body_type
        self._enabled = enabled
        self._sleeping = sleeping

        RigidBody2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            mass=mass,
            moment_of_inertia=moment_of_inertia,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            acceleration_x=acceleration_x,
            acceleration_y=acceleration_y,
            angular_velocity=angular_velocity,
        )

        self._collider = Collider2D(
            parent=self,
            collider_type=collider_type,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=is_trigger,
            x=x,
            y=y,
            width=width,
            height=height,
        )

        self._material = material or Material()

    # IPhysicsBody implementation

    def get_body_type(self) -> BodyType:
        return self._body_type

    def set_body_type(self, value: BodyType) -> None:
        self._body_type = value
        # Update inverse mass for static bodies
        if value == BodyType.STATIC:
            self._inverse_mass = 0.0
        elif self._mass > 0:
            self._inverse_mass = 1.0 / self._mass

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = value

    def get_sleeping(self) -> bool:
        return self._sleeping

    def set_sleeping(self, value: bool) -> None:
        self._sleeping = value

    def get_collider(self) -> ICollider2D:
        return self._collider

    def set_collider(self, collider: ICollider2D) -> None:
        self._collider = collider

    def get_material(self) -> IMaterial:
        return self._material

    def set_material(self, material: IMaterial) -> None:
        self._material = material

    def update(self, dt: float) -> None:
        """Update physics state. Override for custom behavior."""
        pass

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when collision starts. Override for custom behavior."""
        pass

    def on_collision_stay(self, other: IPhysicsBody2D) -> None:
        """Called each frame while colliding. Override for custom behavior."""
        pass

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when collision ends. Override for custom behavior."""
        pass

    # ICollider delegation

    def get_collider_type(self) -> ColliderType:
        return self._collider.get_collider_type()

    def set_collider_type(self, value: ColliderType) -> None:
        self._collider.set_collider_type(value)

    def get_collision_layer(self) -> CollisionLayer:
        return self._collider.get_collision_layer()

    def set_collision_layer(self, value: CollisionLayer) -> None:
        self._collider.set_collision_layer(value)

    def get_collision_mask(self) -> List[CollisionLayer]:
        return self._collider.get_collision_mask()

    def set_collision_mask(self, value: List[CollisionLayer]) -> None:
        self._collider.set_collision_mask(value)

    def get_is_trigger(self) -> bool:
        return self._collider.get_is_trigger()

    def set_is_trigger(self, value: bool) -> None:
        self._collider.set_is_trigger(value)

    def check_collision(self, other: ICollider2D) -> bool:
        return self._collider.check_collision(other)

    def get_bounds(self) -> Tuple[float, float, float, float]:
        return self._collider.get_bounds()

    # IMaterial delegation

    def get_density(self) -> float:
        return self._material.get_density()

    def set_density(self, value: float) -> None:
        self._material.set_density(value)

    def get_restitution(self) -> float:
        return self._material.get_restitution()

    def set_restitution(self, value: float) -> None:
        self._material.set_restitution(value)

    def get_friction(self) -> float:
        return self._material.get_friction()

    def set_friction(self, value: float) -> None:
        self._material.set_friction(value)

    def get_drag(self) -> float:
        return self._material.get_drag()

    def set_drag(self, value: float) -> None:
        self._material.set_drag(value)

    # Properties for convenience
    def get_inverse_mass(self) -> float:
        if self._body_type == BodyType.STATIC:
            return 0.0
        return super().get_inverse_mass()
