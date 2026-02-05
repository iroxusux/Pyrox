# Meta imports to describe the base of everything
from .meta import (
    Configurable,
    Authored,
    Versioned,
    HasId,
    Buildable,
    Nameable,
    Describable,
    Runnable,
    Refreshable,
    Resettable,
    CoreMixin,
    CoreRunnableMixin,
    HasFileLocation,
    HasMetaDictData,
    SupportsItemAccess,
)

# Coordinate imports for protocols that support points in a space.
from .coord import (
    Coord2D,
    Area2D,
    Coord3D,
    Area3D,
)

# Spatial imports for protocols that support spatial objects.
from .spatial import (
    Spatial2D,
    Spatial3D,
    Rotatable,
    Zoomable,
)

# Physics imports for physics simulation
from .physics import (
    Material,
    Collider2D,
    RigidBody2D,
    PhysicsBody2D,
)

# Connectable protocol for objects that can connect to each other
from .connection import Connectable

__all__ = [
    # Meta protocols
    "Configurable",
    "Authored",
    "Versioned",
    "HasId",
    "Buildable",
    "Nameable",
    "Describable",
    "Runnable",
    "Refreshable",
    "Resettable",
    "CoreMixin",
    "CoreRunnableMixin",
    "HasFileLocation",
    "HasMetaDictData",
    "SupportsItemAccess",

    # Coordinate protocols
    "Coord2D",
    "Area2D",
    "Coord3D",
    "Area3D",

    # Spatial protocols
    "Spatial2D",
    "Spatial3D",
    "Rotatable",
    "Zoomable",

    # Physics implementations
    "Material",
    "Collider2D",
    "RigidBody2D",
    "PhysicsBody2D",

    # Connectable protocol
    "Connectable",
]
