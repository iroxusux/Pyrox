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

from .gui import (
    IApplicationGuiMenu,
    GuiFramework,
    IGuiBackend,
    IGuiComponent,
    IGuiFrame,
    IGuiMenu,
    IGuiWidget,
    IGuiWindow,
)

from .services import (
    IEnvironmentManager,
    ILogger,
    ILoggingManager,
    IThemeManager,
    IConfigurationManager,
)

from .application import (
    IApplication,
    IApplicationTask,
    ITaskFactory,
    ILifecycleManager,
)

from .events import (
    IObserver,
    ISubscribable,
    IEventPublisher,
    INotificationService,
)

from .integration import (
    IServiceRegistry,
    IBackendRegistry,
    IDependencyInjector,
    IPluginManager,
)


__all__ = (
    # GUI Interfaces
    'GuiFramework',
    'IGuiBackend',
    'IGuiWidget',
    'IGuiWindow',
    'IGuiMenu',
    'IGuiFrame',
    'IGuiComponent',
    'IApplicationGuiMenu',
    # Service Interfaces
    'IEnvironmentManager',
    'ILogger',
    'ILoggingManager',
    'IThemeManager',
    'IConfigurationManager',

    # Application Interfaces
    'IApplication',
    'IApplicationTask',
    'ITaskFactory',
    'ILifecycleManager',

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
)
