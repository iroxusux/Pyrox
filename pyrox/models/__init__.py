"""models for pyrox"""

# ABCs, protocols and base classes
from .protocols import (
    # Protocol components
    # Meta components
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
    # Coordinate components
    Coord2D,
    Area2D,
    Coord3D,
    Area3D,
    # Spacial components
    Spatial2D,
    Spatial3D,
    Rotatable,
    Zoomable,
)

from .meta import (
    PyroxObject,
    SupportsFileLocation,
    SupportsMetaData,
)

from .list import (
    HashList,
    SafeList,
    Subscribable,
)

from .factory import (
    FactoryTypeMeta,
    MetaFactory,
)

from . import gui  # Must come second to register GUI components

# GUI components
from .gui import (
    LogFrame,
    PyroxFrameContainer,
    PyroxGuiObject,
    SceneViewerFrame,
)


# Services components
from .services import (
    SupportsEnvServices,
    SupportsLoggingServices,
    SupportsGUIServices,
    PlatformDirectoryService,
    ServicesRunnableMixin,
)

# Task components
from .task import ApplicationTask, ApplicationTaskFactory

# Scene components
from .scene import Scene, SceneObject, SceneObjectFactory, PhysicsSceneObject

# Physics components from protocols
from .protocols.physics import Material, Collider2D, RigidBody2D, PhysicsBody2D


__all__ = [
    # ABCs and base classes
    # Protocol components
    # Meta protocols
    'Configurable',
    'Authored',
    'Versioned',
    'HasId',
    'Buildable',
    'Nameable',
    'Describable',
    'Refreshable',
    'Resettable',
    'Runnable',
    'CoreMixin',
    'CoreRunnableMixin',
    # Coordinate protocols
    'Coord2D',
    'Area2D',
    'Coord3D',
    'Area3D',
    # Spatial protocols
    'Spatial2D',
    'Spatial3D',
    'Rotatable',
    'Zoomable',

    # Base classes
    'PyroxObject',
    'SupportsFileLocation',
    'SupportsMetaData',

    # Factory components
    'FactoryTypeMeta',
    'MetaFactory',

    # List components
    'HashList',
    'SafeList',
    'Subscribable',

    # GUI components
    'gui',
    'LogFrame',
    'PyroxFrameContainer',
    'PyroxGuiObject',
    'SceneViewerFrame',

    # Services components
    'SupportsEnvServices',
    'SupportsLoggingServices',
    'SupportsGUIServices',
    'PlatformDirectoryService',
    'ServicesRunnableMixin',

    # Task components
    'ApplicationTask',
    'ApplicationTaskFactory',

    # Scene components
    'Scene',
    'SceneObject',
    'SceneObjectFactory',
    'PhysicsSceneObject',

    # Physics components
    'Material',
    'Collider2D',
    'RigidBody2D',
    'PhysicsBody2D',
]
