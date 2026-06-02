"""Protocol interfaces for various capabilities within the Pyrox environment.
"""

# Meta imports to describe the base of everything
from .base import (
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

    # Property protocols
    "IHasProperties",

    # Connectable protocols
    "IConnectable",
    "Connection",

    # GUI protocols
    "IHasCanvas",
]
