"""Pure interface definitions for Pyrox framework.

This module provides abstract interfaces that eliminate circular dependencies
between services and models while maintaining clean architectural boundaries.

The interfaces follow the Interface Segregation Principle (ISP) and Dependency
Inversion Principle (DIP) to create a loosely-coupled, extensible system.

Key Design Principles:
    - Interfaces contain only method signatures, no implementations
    - No imports from pyrox.services or pyrox.models modules
    - Pure abstractions with minimal external dependencies
    - Forward-compatible design for future enhancements
    - Properties used and implimented for attribute access where appropriate
"""

# TODO: refactor inerfaces to properly be structural contracts without any implementation details,
# and move any shared implementation details to mixin classes in pyrox.models.protocols.meta

# Environment constants
from .constants import EnvironmentKeys

# Enums
from .enums import CardinalDirection

# Base ABCs
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
    IHasFileLocation,
    IHasDictMetaData,
    IHasProperties,
)

# Service interfaces
from .services import (
    IHasViewableServiceAttributes,
    ISupportsServiceStatus,
    IStatusServiceMixin,
)

# Application interfaces
from .application import (
    IApplication,
    IApplicationTask,
)

# GUI interfaces
from .gui import (
    IHasCanvas,
    IWorkspace,
)

# Connection interfaces
from .connection import (
    Connection,
    IConnectable,
    IConnectionRegistry,
)


__all__ = (
    # Environment Constants
    'EnvironmentKeys',

    # Enums
    'CardinalDirection',

    # Protocols
    # Meta protocols
    'IConfigurable',
    'IAuthored',
    'IVersioned',
    'IHasId',
    'INameable',
    'IDescribable',
    'IBuildable',
    'IRefreshable',
    'IResettable',
    'IRunnable',
    'IHasFileLocation',
    'IHasDictMetaData',
    # Property protocols
    'IHasProperties',

    # GUI Interfaces
    'IWorkspace',
    'IHasCanvas',

    # Service Interfaces
    'IHasViewableServiceAttributes',
    'ISupportsServiceStatus',
    'IStatusServiceMixin',

    # Application Interfaces
    'IApplication',
    'IApplicationTask',

    # Connection Interfaces
    'Connection',
    'IConnectable',
    'IConnectionRegistry',
)
