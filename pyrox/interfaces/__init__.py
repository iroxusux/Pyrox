"""Pure interface definitions for Pyrox framework.

This module provides abstract interfaces that eliminate circular dependencies
between services and models while maintaining clean architectural boundaries.

The interfaces follow the Interface Segregation Principle (ISP) and Dependency
Inversion Principle (DIP) to create a loosely-coupled, extensible system.

Key Design Principles:
    - Interfaces contain only method signatures, no implementations
    - No imports from pyrox.services or pyrox.models modules
    - Pure abstractions with minimal external dependencies
    - Support for dependency injection and plugin architectures
    - Forward-compatible design for future enhancements

Interface Categories:
    - GUI: Backend, window, menu, and component abstractions
    - Services: Environment, logging, configuration, and utility interfaces
    - Application: Task, factory, and application lifecycle interfaces
    - Configuration: Settings, environment, and state management interfaces
    - Events: Observer patterns, subscriptions, and notification interfaces
    - Integration: Dependency injection and registration patterns
"""
# Environment constants
from .constants import EnvironmentKeys

# Protocols
from .protocols import (
    IConfigurable,
    INameable,
    IDescribable,
    IBuildable,
    IRefreshable,
    IResettable,
    IRunnable,
    ICoreRunnableMixin,
    IHasFileLocation,
    IHasDictMetaData,
    ISupportsItemAccess,
)

# Service interfaces
from .services import (
    IEnvironmentManager,
    ILogger,
    ILoggingManager,
    IThemeManager,
    IConfigurationManager,
)

# Application interfaces
from .application import (
    IApplication,
    IApplicationTask,
)

# Event interfaces
from .events import (
    IObserver,
    ISubscribable,
    IEventPublisher,
    INotificationService,
)

# Integration interfaces
from .integration import (
    IServiceRegistry,
    IBackendRegistry,
    IDependencyInjector,
    IPluginManager,
)

# GUI interfaces
from .gui import (
    IApplicationGuiMenu,
    GuiFramework,
    IGuiBackend,
    IGuiComponent,
    IGuiFrame,
    ITaskFrame,
    IGuiMenu,
    IGuiWidget,
    IGuiWindow,
    IWorkspace,
)

# Scene interfaces
from .scene import IScene, ISceneObject, ISceneObjectFactory


__all__ = (
    # Environment Constants
    'EnvironmentKeys',

    # Protocols
    'IConfigurable',
    'INameable',
    'IDescribable',
    'IBuildable',
    'IRefreshable',
    'IResettable',
    'IRunnable',
    'ICoreRunnableMixin',
    'IHasFileLocation',
    'IHasDictMetaData',
    'ISupportsItemAccess',

    # GUI Interfaces
    'GuiFramework',
    'IGuiBackend',
    'IGuiWidget',
    'IGuiWindow',
    'IGuiMenu',
    'IGuiFrame',
    'ITaskFrame',
    'IGuiComponent',
    'IApplicationGuiMenu',
    'IWorkspace',

    # Service Interfaces
    'IEnvironmentManager',
    'ILogger',
    'ILoggingManager',
    'IThemeManager',
    'IConfigurationManager',

    # Application Interfaces
    'IApplication',
    'IApplicationTask',

    # Event Interfaces
    'IObserver',
    'ISubscribable',
    'IEventPublisher',
    'INotificationService',

    # Integration Interfaces
    'IServiceRegistry',
    'IBackendRegistry',
    'IDependencyInjector',
    'IPluginManager',

    # Scene Interfaces
    'IScene',
    'ISceneObject',
    'ISceneObjectFactory',
)
