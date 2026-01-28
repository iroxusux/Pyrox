"""models for pyrox"""
from . import abc  # Must come first to register ABCs

# ABCs, protocols and base classes
from .abc import (
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

    FactoryTypeMeta,
    HashList,
    MetaFactory,
    PyroxObject,
    SafeList,
    Subscribable,
    SupportsFileLocation,
    SupportsMetaData,
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
from .scene import Scene, SceneObject, SceneObjectFactory


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

    'abc',
    'FactoryTypeMeta',
    'HashList',
    'MetaFactory',
    'PyroxObject',
    'SafeList',
    'Subscribable',
    'SupportsFileLocation',
    'SupportsMetaData',

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
]
