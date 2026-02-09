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
# Environment constants
from .constants import EnvironmentKeys

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
    ISupportsItemAccess,

    # Coordinate imports for protocols that support points in a space.
    ICoord2D,
    IArea2D,
    ICoord3D,
    IArea3D,

    # Spatial imports for protocols that support spatial objects.
    ISpatial2D,
    ISpatial3D,
    IRotatable,
    IZoomable,

    # Kinematic imports for protocols that support kinematic objects.
    IVelocity2D,
    IVelocity3D,
    IAngularVelocity,
    IKinematic2D,
    IKinematic3D,

    # Physics imports for protocols that support physical objects.
    BodyType,
    ColliderType,
    CollisionLayer,
    IMaterial,
    ICollider2D,
    IPhysicsBody2D,
    IRigidBody2D,
    IRigidBody3D,
    IPhysicsEngine,

    # Property imports for protocols that support properties.
    IHasProperties,

    # Connectable protocols
    IConnectable,
    Connection,

    # GUI protocols
    IHasCanvas,
)

# Physics interfaces
from .physics import IBasePhysicsBody

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
    IViewport,
)

# Connection interfaces
from .connection import (
    IConnectionRegistry,
)

# Scene interfaces
from .scene import (
    IScene,
    ISceneObject,
    ISceneObjectFactory,
    ISceneRunnerService
)


__all__ = (
    # Environment Constants
    'EnvironmentKeys',

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
    'ISupportsItemAccess',
    # Coordinate protocols
    'ICoord2D',
    'IArea2D',
    'ICoord3D',
    'IArea3D',
    # Spatial protocols
    'ISpatial2D',
    'ISpatial3D',
    'IRotatable',
    'IZoomable',
    # Kinematic protocols
    'IVelocity2D',
    'IVelocity3D',
    'IAngularVelocity',
    'IKinematic2D',
    'IKinematic3D',
    # Physics protocols
    'BodyType',
    'ColliderType',
    'CollisionLayer',
    'IMaterial',
    'ICollider2D',
    'IPhysicsBody2D',
    'IRigidBody2D',
    'IRigidBody3D',
    'IPhysicsEngine',
    # Property protocols
    'IHasProperties',
    # Connectable protocols
    'IConnectable',
    'Connection',
    # Gui Protocols
    'IHasCanvas',

    # Physics Interfaces
    'IBasePhysicsBody',

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
    'IViewport',

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

    # Connection Interfaces
    'IConnectionRegistry',

    # Scene Interfaces
    'IScene',
    'ISceneObject',
    'ISceneObjectFactory',
    'ISceneRunnerService',
)
