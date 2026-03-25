"""Protocol interfaces for various capabilities within the Pyrox environment.
"""

# Meta imports to describe the base of everything
from .meta import (
    IConfigurable,
    IAuthored,
    IVersioned,
    IHasId,
    INameable,
    IDescribable,
    IRefreshable,
    IResettable,
    IBuildable,
    IRunnable,
    ICoreMixin,
    ICoreRunnableMixin,
    IHasFileLocation,
    IHasDictMetaData,
)

# Coordinate imports for protocols that support points in a space.
from .coord import (
    ICoord2D,
    IArea2D,
)

# Spatial imports for protocols that support spatial objects.
from .spatial import (
    ISpatial2D,
    IRotatable,
    IDirectional2D,
    IZoomable,
)

# Kinematic imports for protocols that support kinematic objects.
from .kinematic import (
    IVelocity2D,
    IAngularVelocity,
    IKinematic2D,
)

# Physics imports for protocols that support physical objects.
from .physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IMaterial,
    ICollider2D,
    IPhysicsBody2D,
    IRigidBody2D,
    IPhysicsEngine,
)

# Property imports for protocols that support properties.
from .property import (
    IHasProperties,
)

# Connectable protocols
from .connection import (
    IConnectable,
    Connection,
)

# GUI protocols
from .gui import (
    IHasCanvas,
)

__all__ = [
    # Meta protocols
    "IAuthored",
    "IVersioned",
    "IHasId",
    "IConfigurable",
    "INameable",
    "IDescribable",
    "IBuildable",
    "IRefreshable",
    "IResettable",
    "IRunnable",
    "ICoreMixin",
    "ICoreRunnableMixin",
    "IHasFileLocation",
    "IHasDictMetaData",

    # Coordinate protocols
    "ICoord2D",
    "IArea2D",

    # Spatial protocols
    "ISpatial2D",
    "IRotatable",
    "IDirectional2D",
    "IZoomable",

    # Kinematic protocols
    "IVelocity2D",
    "IAngularVelocity",
    "IKinematic2D",

    # Physics protocols
    "BodyType",
    "ColliderType",
    "CollisionLayer",
    "IMaterial",
    "ICollider2D",
    "IRigidBody2D",
    "IPhysicsBody2D",
    "IPhysicsEngine",

    # Property protocols
    "IHasProperties",

    # Connectable protocols
    "IConnectable",
    "Connection",

    # GUI protocols
    "IHasCanvas",
]
