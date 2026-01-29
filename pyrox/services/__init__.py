"""services module for pyrox
"""
# Environment imports
from . import env  # MUST COME FIRST, loading env affects logging for global logging level
from .env import EnvManager, get_env, set_env, set_key, get_default_date_format, get_default_formatter

# Logging imports
from . import logging  # MUST COME SECOND, logging must be configured before other imports
from .logging import log, LoggingManager

# Theme imports
from . import theme  # MUST COME THIRD, theme may be needed by gui on initialization
from .theme import ThemeManager

# GUI imports
from . import gui  # MUST COME FOURTH, gui imports sub-systems which on some systems needs to be loaded early
from .gui import GuiManager

# File imports
from . import file
from .file import get_open_file, PlatformDirectoryService

# Collision imports
from .collision import CollisionService, SpatialGrid

# Environment imports
from .environment import EnvironmentService

# Physics imports
from .physics import PhysicsEngineService

# Scene imports
from .scene import SceneRunnerService

# Other service imports
from . import (
    archive,
    bit,
    byte,
    collision,
    decorate,
    dict,
    environment,
    factory,
    logic,
    notify_services,
    object,
    physics,
    progress,
    scene,
    search,
    stream,
    timer,
    xml,
)


__all__ = (
    # Environment imports
    'EnvManager',
    'get_env',
    'set_env',
    'set_key',
    'get_default_date_format',
    'get_default_formatter',
    'env',
    # Logging imports
    'log',
    'LoggingManager',
    'logging',
    # Theme imports
    'ThemeManager',
    'theme',
    # GUI imports
    'GuiManager',
    'gui',
    # File imports
    'get_open_file',
    'PlatformDirectoryService',
    'file',
    # Collision imports
    'CollisionService',
    'SpatialGrid',
    # Environment imports
    'EnvironmentService',
    # Physics imports
    'PhysicsEngineService',
    # Scene imports
    'SceneRunnerService',
    # Other service imports
    'archive',
    'bit',
    'byte',
    'collision',
    'decorate',
    'dict',
    'environment',
    'factory',
    'logic',
    'notify_services',
    'object',
    'physics',
    'progress',
    'scene',
    'search',
    'stream',
    'timer',
    'xml',
)
