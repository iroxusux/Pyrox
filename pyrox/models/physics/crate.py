"""Crate physics body implementation.

Provides a simple dynamic physics body representing a movable crate
or box that can be pushed, fall, and interact with other physics objects.
"""
from typing import List
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class CrateBody(BasePhysicsBody):
    """A simple dynamic crate/box physics body.

    Represents a movable object that responds to forces, gravity,
    and collisions. Useful for testing physics interactions like
    conveyor belts, stacking, pushing, etc.

    Attributes:
        crate_type: Type identifier (e.g., "wooden", "metal", "cardboard")
    """

    def __init__(
        self,
        name: str = "Crate",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 20.0,
        height: float = 20.0,
        mass: float = 10.0,
        crate_type: str = "wooden",
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: List[CollisionLayer] | None = None,
        material: Material | None = None,
    ):
        """Initialize crate body.

        Args:
            name: Name of the crate
            x: X position
            y: Y position
            width: Width of the crate
            height: Height of the crate
            mass: Mass in kilograms
            crate_type: Type of crate (affects material if not provided)
            collision_layer: Collision layer
            collision_mask: Which layers this crate collides with
            material: Material properties (auto-selected based on type if None)
        """
        # Default collision mask includes most common layers
        if collision_mask is None:
            collision_mask = [
                CollisionLayer.DEFAULT,
                CollisionLayer.TERRAIN,
                CollisionLayer.PLAYER,
                CollisionLayer.ENEMY,
            ]

        # Auto-select material based on crate type if not provided
        if material is None:
            material = self._get_material_for_type(crate_type)

        # Calculate moment of inertia for a rectangle: (1/12) * mass * (width² + height²)
        moment = (1.0 / 12.0) * mass * (width * width + height * height)

        super().__init__(
            name=name,
            tags=["crate", crate_type],
            body_type=BodyType.DYNAMIC,
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

        self.crate_type = crate_type

    @staticmethod
    def _get_material_for_type(crate_type: str) -> Material:
        """Get default material properties for a crate type.

        Args:
            crate_type: Type of crate

        Returns:
            Material with appropriate properties
        """
        materials = {
            "wooden": Material(
                density=0.6,
                restitution=0.3,
                friction=0.6,
                drag=0.1
            ),
            "metal": Material(
                density=7.8,
                restitution=0.2,
                friction=0.4,
                drag=0.05
            ),
            "cardboard": Material(
                density=0.2,
                restitution=0.1,
                friction=0.7,
                drag=0.15
            ),
            "plastic": Material(
                density=0.9,
                restitution=0.5,
                friction=0.3,
                drag=0.08
            ),
        }

        return materials.get(crate_type, materials["wooden"])

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when collision starts with another body.

        Args:
            other: The other physics body
        """
        # Add custom collision behavior here if needed
        # For example, sound effects, particle effects, etc.
        pass

    def on_collision_stay(self, other: IPhysicsBody2D) -> None:
        """Called each frame while colliding with another body.

        Args:
            other: The other physics body
        """
        # Add continuous collision behavior here if needed
        pass

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when collision ends with another body.

        Args:
            other: The other physics body
        """
        # Add collision exit behavior here if needed
        pass

    def update(self, dt: float) -> None:
        """Update the crate each physics step.

        Args:
            dt: Delta time in seconds
        """
        # Add custom update behavior here if needed
        # For example, visual effects, state transitions, etc.
        pass

    @classmethod
    def create_wooden(cls, name: str = "Wooden Crate", **kwargs) -> 'CrateBody':
        """Create a wooden crate with appropriate properties.

        Args:
            name: Name of the crate
            **kwargs: Additional constructor arguments

        Returns:
            CrateBody configured as wooden crate
        """
        return cls(name=name, crate_type="wooden", mass=10.0, **kwargs)

    @classmethod
    def create_metal(cls, name: str = "Metal Crate", **kwargs) -> 'CrateBody':
        """Create a metal crate with appropriate properties.

        Args:
            name: Name of the crate
            **kwargs: Additional constructor arguments

        Returns:
            CrateBody configured as metal crate
        """
        return cls(name=name, crate_type="metal", mass=50.0, **kwargs)

    @classmethod
    def create_cardboard(cls, name: str = "Cardboard Box", **kwargs) -> 'CrateBody':
        """Create a cardboard box with appropriate properties.

        Args:
            name: Name of the crate
            **kwargs: Additional constructor arguments

        Returns:
            CrateBody configured as cardboard box
        """
        return cls(name=name, crate_type="cardboard", mass=2.0, **kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return (f"<CrateBody '{self.name}' type={self.crate_type} "
                f"mass={self.mass:.1f}kg "
                f"pos=({self.x:.1f}, {self.y:.1f}) "
                f"size=({self.width:.1f}x{self.height:.1f})>")


# Register crate template in factory
PhysicsSceneFactory.register_template(
    template_name="Crate",
    template=PhysicsSceneTemplate(
        name="Crate",
        body_class=CrateBody,
        default_kwargs={
            "width": 20.0,
            "height": 20.0,
            "mass": 10.0,
            "crate_type": "wooden",
        },
        category="Objects"
    )
)
