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
]
