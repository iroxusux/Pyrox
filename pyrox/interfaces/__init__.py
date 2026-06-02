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

Interface Categories:
    - GUI: Backend, window, menu, and component abstractions
    - Services: Environment, logging, configuration, and utility interfaces
    - Application: Task, factory, and application lifecycle interfaces
    - Configuration: Settings, environment, and state management interfaces
    - Events: Observer patterns, subscriptions, and notification interfaces
"""

# TODO: refactor inerfaces to properly be structural contracts without any implementation details,
# and move any shared implementation details to mixin classes in pyrox.models.protocols.meta

# Environment constants
from .constants import EnvironmentKeys

# Enums
from .enums import CardinalDirection

# Protocols
from .protocols import (
    # Meta imports to describe the base of everything
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

    # Property imports for protocols that support properties.
    IHasProperties,

    # Connectable protocols
    IConnectable,
    Connection,

    # GUI protocols
    IHasCanvas,
)

# Service interfaces
from .services import (
    IEnvironmentManager,
    ILogger,
    ILoggingManager,
    IHasViewableServiceAttributes,
    ISupportsServiceStatus,
)

# Application interfaces
from .application import (
    IApplication,
    IApplicationTask,
)

# GUI interfaces
from .gui import (
    IWorkspace,
)

# Connection interfaces
from .connection import (
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
    'ICoreMixin',
    'ICoreRunnableMixin',
    'IHasFileLocation',
    'IHasDictMetaData',
    # Property protocols
    'IHasProperties',
    # Connectable protocols
    'IConnectable',
    'Connection',
    # Gui Protocols
    'IHasCanvas',

    # GUI Interfaces
    'IWorkspace',

    # Service Interfaces
    'IEnvironmentManager',
    'ILogger',
    'ILoggingManager',
    'IHasViewableServiceAttributes',
    'ISupportsServiceStatus',

    # Application Interfaces
    'IApplication',
    'IApplicationTask',

    # Connection Interfaces
    'IConnectionRegistry',
)
