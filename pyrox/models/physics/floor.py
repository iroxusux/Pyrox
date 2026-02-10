"""Floor physics body implementation.

Provides a static floor surface with configurable friction properties,
ideal for top-down environments where objects should slide and stop naturally.
"""
from typing import Any, List
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class FloorBody(BasePhysicsBody):
    """Floor surface for top-down or side-scrolling games.

    A static body that provides a surface with configurable friction
    and drag properties. Objects on the floor experience realistic
    sliding and stopping behavior.

    **For Top-Down Games (default):**
        - Set `is_trigger=True` (default) - objects move through the floor
        - Floor applies direct velocity damping via `on_collision_stay` callback
        - Objects slide and stop based on material's friction/drag values
        - Damping is applied every frame while objects overlap the floor
        - More realistic stopping behavior than force-based friction

    **For Side-Scrolling/Platformer Games:**
        - Set `is_trigger=False` - floor acts as solid collision boundary
        - Objects stand on top and cannot pass through
        - Use "Solid Platform Floor" template
        - Normal collision resolution applies friction

    **Important:** For collisions to work, objects must have
    `CollisionLayer.TERRAIN` in their `collision_mask`.

    **Physics Behavior (Top-Down Mode):**
        - Velocity damping: `velocity *= damping_factor` each frame
        - Damping factor based on friction: high friction = low retention (stops fast)
        - Additional drag reduces velocity: high drag = more resistance
        - Snap to zero when velocity < 0.5 units/s to prevent drift

    Attributes:
        surface_type: Type of floor surface (concrete, ice, mud, etc.)
        friction_coefficient: How much friction the surface provides
    """

    # Preset surface types with their material properties
    SURFACE_PRESETS = {
        'concrete': {
            'friction': 0.8,
            'drag': 3.0,
            'restitution': 0.1,
            'description': 'Rough concrete - high friction, objects stop quickly'
        },
        'wood': {
            'friction': 0.6,
            'drag': 2.0,
            'restitution': 0.2,
            'description': 'Wooden floor - moderate friction'
        },
        'ice': {
            'friction': 0.1,
            'drag': 0.5,
            'restitution': 0.05,
            'description': 'Slippery ice - very low friction, slides far'
        },
        'mud': {
            'friction': 0.9,
            'drag': 5.0,
            'restitution': 0.0,
            'description': 'Thick mud - very high friction, objects stop immediately'
        },
        'carpet': {
            'friction': 0.7,
            'drag': 2.5,
            'restitution': 0.1,
            'description': 'Carpet - good friction, dampens movement'
        },
        'metal': {
            'friction': 0.4,
            'drag': 1.5,
            'restitution': 0.3,
            'description': 'Smooth metal - low friction, some bounce'
        },
    }

    def __init__(
        self,
        name: str = "Floor",
        template_name: str = "Floor",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 1000.0,
        height: float = 1000.0,
        surface_type: str = "concrete",
        body_type: BodyType = BodyType.STATIC,
        collision_layer: CollisionLayer = CollisionLayer.TERRAIN,
        collision_mask: List[CollisionLayer] | None = None,
        is_trigger: bool = True,  # Default to trigger for top-down games
        material: Material | None = None,
        *args,
        **kwargs
    ):
        """Initialize floor body.

        Args:
            name: Name of the floor
            x: X position (typically 0 for full coverage)
            y: Y position (typically 0 for full coverage)
            width: Width of the floor area
            height: Height of the floor area
            surface_type: Type of surface ('concrete', 'wood', 'ice', 'mud', 'carpet', 'metal')
            body_type: Typically STATIC
            collision_layer: Collision layer
            collision_mask: Which layers can collide with this floor
            is_trigger: True for top-down (objects move through), False for side-view (solid floor)
            material: Material properties (overrides surface_type if provided)
        """
        # Default collision mask includes all dynamic objects
        if collision_mask is None:
            collision_mask = [
                CollisionLayer.DEFAULT,
                CollisionLayer.PLAYER,
                CollisionLayer.ENEMY,
            ]

        # Get material from surface preset if not explicitly provided
        if material is None:
            surface_preset = self.SURFACE_PRESETS.get(surface_type.lower(), self.SURFACE_PRESETS['concrete'])
            material = Material(
                density=1.0,
                restitution=surface_preset['restitution'],
                friction=surface_preset['friction'],
                drag=surface_preset['drag']
            )

        self._surface_type = surface_type.lower() if surface_type.lower() in self.SURFACE_PRESETS else 'concrete'

        BasePhysicsBody.__init__(
            self=self,
            name=name,
            template_name=template_name,
            tags=["floor", "terrain", "static"],
            body_type=body_type,
            enabled=True,
            sleeping=False,
            mass=0.0,  # Static bodies have zero mass
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

    @property
    def surface_type(self) -> str:
        """Get the surface type.

        Returns:
            Surface type name
        """
        return self._surface_type

    @surface_type.setter
    def surface_type(self, surface_type: str) -> None:
        """Set the surface type and update material properties.

        Args:
            surface_type: New surface type
        """
        surface_lower = surface_type.lower()
        if surface_lower not in self.SURFACE_PRESETS:
            raise ValueError(
                f"Unknown surface type: {surface_type}. "
                f"Available types: {list(self.SURFACE_PRESETS.keys())}"
            )

        self._surface_type = surface_lower
        preset = self.SURFACE_PRESETS[surface_lower]

        # Update material properties
        self.material.set_friction(preset['friction'])
        self.material.set_drag(preset['drag'])
        self.material.set_restitution(preset['restitution'])

    def get_surface_description(self) -> str:
        """Get description of current surface type.

        Returns:
            Description of the surface behavior
        """
        preset = self.SURFACE_PRESETS.get(self._surface_type, self.SURFACE_PRESETS['concrete'])
        mode = "trigger (top-down)" if self.collider.is_trigger else "solid (platformer)"
        return f"{preset['description']} [{mode}]"

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when an object starts colliding with the floor.

        Args:
            other: The colliding physics body
        """
        # Floor is passive - doesn't need special collision behavior
        pass

    def on_collision_stay(self, other: IPhysicsBody2D) -> None:
        """Called each frame while an object is colliding with the floor.

        For trigger floors (top-down games), this uses direct velocity damping
        for more realistic stopping behavior instead of force-based friction.

        Args:
            other: The colliding physics body
        """
        # Only apply if this is a trigger floor and the other body is dynamic
        if not self.collider.is_trigger or other.body_type != BodyType.DYNAMIC:
            return

        # Get the other body's velocity
        vx, vy = other.linear_velocity

        # Calculate velocity magnitude
        speed = (vx**2 + vy**2)**0.5
        if speed < 0.01:  # Skip if nearly stationary
            return

        # For top-down games, use direct velocity damping instead of forces
        # This provides more immediate and realistic stopping behavior
        # Damping rate is based on friction (higher friction = faster stop)

        # Calculate per-frame damping factor from friction coefficient
        # friction 0.0 = no damping, friction 1.0 = very strong damping
        # We use exponential decay: velocity *= damping_factor
        # For 60fps: damping_factor^60 should give us significant slowdown per second

        # Map friction (0.0-1.0) to damping factor (1.0-0.0):
        # - friction=0.1 (ice): ~97% retention per frame (slides far)
        # - friction=0.5: ~92% retention per frame
        # - friction=0.8 (concrete): ~88% retention per frame (stops quickly)
        # - friction=0.9 (mud): ~85% retention per frame (stops immediately)
        friction_coefficient = self.material.friction
        damping_factor = 1.0 - (friction_coefficient * 0.15)  # Maps 0.0-1.0 friction to 1.0-0.85 retention

        # Apply additional drag-based damping
        # Higher drag = more resistance
        drag_coefficient = self.material.drag
        drag_damping = 1.0 - (drag_coefficient * 0.01)  # Maps 0-5 drag to 1.0-0.95 retention

        # Combine both damping effects (multiplicative)
        combined_damping = damping_factor * drag_damping

        # Apply damping to velocity
        new_vx = vx * combined_damping
        new_vy = vy * combined_damping

        # Snap to zero if very slow (prevents infinite asymptotic decay and oscillation)
        if abs(new_vx) < 1.0:
            new_vx = 0.0
        if abs(new_vy) < 1.0:
            new_vy = 0.0

        other.set_linear_velocity(new_vx, new_vy)

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when an object stops colliding with the floor.

        Args:
            other: The physics body that left
        """
        pass

    def update(self, dt: float) -> None:
        """Update the floor each physics step.

        Args:
            dt: Delta time in seconds
        """
        # Static floor doesn't need updates
        pass

    def get_properties(self) -> dict[str, Any]:
        """Get properties that can be edited in the properties panel.

        Returns:
            Dictionary mapping property names to their metadata
        """
        # Get base properties from parent
        properties = super().get_properties()

        # Add floor-specific properties
        properties.update({
            "surface_type": self.surface_type
        })

        return properties

    @classmethod
    def from_dict(cls, data: dict) -> 'FloorBody':
        """Create a FloorBody from a dictionary representation.

        Args:
            data: Dictionary with body properties
        Returns:
            Instance of FloorBody
        """
        return cls(
            name=data.get('name', 'Floor'),
            id=data.get('id', ''),
            template_name=data.get('template_name', 'Floor'),
            tags=data.get('tags', ['floor', 'terrain', 'static']),
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
            width=data.get('width', 1000.0),
            height=data.get('height', 1000.0),
            roll=data.get('roll', 0.0),
            pitch=data.get('pitch', 0.0),
            yaw=data.get('yaw', 0.0),
            surface_type=data.get('surface_type', 'concrete'),
            material=Material.from_dict(data['material']) if data.get('material') else None,
        )

    def to_dict(self) -> dict:
        """Convert floor to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        # Get base body dict
        base_dict = super().to_dict()

        # Add floor-specific fields
        base_dict.update({
            "surface_type": self._surface_type,
        })

        return base_dict

    def __repr__(self) -> str:
        """String representation."""
        return (f"<FloorBody '{self.name}' surface={self._surface_type} "
                f"pos=({self.x:.1f}, {self.y:.1f}) "
                f"size=({self.width:.1f}x{self.height:.1f}) "
                f"friction={self.material.friction:.2f} "
                f"drag={self.material.drag:.2f}>")


# Register floor templates in factory

# Concrete floor preset (default - high friction)
PhysicsSceneFactory.register_template(
    template_name="Concrete Floor",
    template=PhysicsSceneTemplate(
        name="Concrete Floor",
        body_class=FloorBody,
        default_kwargs={
            "width": 1000.0,
            "height": 1000.0,
            "surface_type": "concrete",
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Terrain",
        description="Rough concrete floor with high friction - objects stop quickly.",
    )
)

# Ice floor preset (low friction)
PhysicsSceneFactory.register_template(
    template_name="Ice Floor",
    template=PhysicsSceneTemplate(
        name="Ice Floor",
        body_class=FloorBody,
        default_kwargs={
            "width": 1000.0,
            "height": 1000.0,
            "surface_type": "ice",
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Terrain",
        description="Slippery ice floor with very low friction - objects slide far.",
    )
)

# Wood floor preset (moderate friction)
PhysicsSceneFactory.register_template(
    template_name="Wood Floor",
    template=PhysicsSceneTemplate(
        name="Wood Floor",
        body_class=FloorBody,
        default_kwargs={
            "width": 1000.0,
            "height": 1000.0,
            "surface_type": "wood",
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Terrain",
        description="Wooden floor with moderate friction.",
    )
)

# Mud floor preset (very high friction)
PhysicsSceneFactory.register_template(
    template_name="Mud Floor",
    template=PhysicsSceneTemplate(
        name="Mud Floor",
        body_class=FloorBody,
        default_kwargs={
            "width": 1000.0,
            "height": 1000.0,
            "surface_type": "mud",
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
        },
        category="Terrain",
        description="Thick mud floor - objects stop almost immediately.",
    )
)

# Solid floor for side-scrolling/platformer games
PhysicsSceneFactory.register_template(
    template_name="Solid Platform Floor",
    template=PhysicsSceneTemplate(
        name="Solid Platform Floor",
        body_class=FloorBody,
        default_kwargs={
            "width": 1000.0,
            "height": 50.0,
            "surface_type": "concrete",
            "body_type": BodyType.STATIC,
            "collision_layer": CollisionLayer.TERRAIN,
            "is_trigger": False,  # Solid floor for platformers
        },
        category="Terrain",
        description="Solid floor platform for side-scrolling games - objects collide and stand on it.",
    )
)
