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
    ISupportsItemAccess,
)

# Coordinate imports for protocols that support points in a space.
from .coord import (
    ICoord2D,
    IArea2D,
    ICoord3D,
    IArea3D,
)

# Spatial imports for protocols that support spatial objects.
from .spatial import (
    ISpatial2D,
    ISpatial3D,
    IRotatable,
    IZoomable,
)

# Kinematic imports for protocols that support kinematic objects.
from .kinematic import (
    IVelocity2D,
    IVelocity3D,
    IAngularVelocity,
    IKinematic2D,
    IKinematic3D,
)

# Physics imports for protocols that support physical objects.
from .physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IMaterial,
    ICollider2D,
    ICollider3D,
    IPhysicsBody2D,
    IRigidBody2D,
    IRigidBody3D,
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
    "ISupportsItemAccess",

    # Coordinate protocols
    "ICoord2D",
    "IArea2D",
    "ICoord3D",
    "IArea3D",

    # Spatial protocols
    "ISpatial2D",
    "ISpatial3D",
    "IRotatable",
    "IZoomable",

    # Kinematic protocols
    "IVelocity2D",
    "IVelocity3D",
    "IAngularVelocity",
    "IKinematic2D",
    "IKinematic3D",

    # Physics protocols
    "BodyType",
    "ColliderType",
    "CollisionLayer",
    "IMaterial",
    "ICollider2D",
    "ICollider3D",
    "IRigidBody2D",
    "IRigidBody3D",
    "IPhysicsBody2D",
    "IPhysicsEngine",

    # Property protocols
    "IHasProperties",

    # Connectable protocols
    "IConnectable",
    "Connection",
]
