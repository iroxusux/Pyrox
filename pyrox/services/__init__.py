"""services module for pyrox
"""
# Environment imports
from .env import (  # MUST COME FIRST, loading env affects logging for global logging level
    EnvManager,
    get_env,
    set_env,
    set_key,
    get_default_date_format,
    get_default_formatter
)

# Logging imports
from .logging import (  # MUST COME SECOND, logging must be configured before other imports
    log,
    LoggingManager
)

# Id imports
from .id import IdGeneratorService

# Theme imports
from .theme import ThemeManager

# GUI imports
from .gui import GuiManager

# File imports
from .file import (
    get_open_file,
    get_save_file,
    PlatformDirectoryService
)

# Process imports
from .process import execute_file_as_subprocess

# Collision imports
from .collision import (
    CollisionService,
    SpatialGrid
)

# Environment imports
from .environment import EnvironmentService

# Physics imports
from .physics import PhysicsEngineService

# Scene imports
from .scene import (
    HasSceneMixin,
    SceneRunnerService,
    SceneEvent,
    SceneEventType,
    SceneEventBus,
)

# Menu registry imports
from .menu_registry import (
    MenuRegistry,
    MenuItemDescriptor
)

# Canvas imports
from .canvas import CanvasObjectManagmenentService

# Viewport imports
from .viewport import (
    ViewportPanningService,
    ViewportZoomingService,
    ViewportGriddingService,
    ViewportStatusService
)

# Timer imports
from .timer import TimerService

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
    # Logging imports
    'log',
    'LoggingManager',
    # Id imports
    'IdGeneratorService',
    # Theme imports
    'ThemeManager',
    # GUI imports
    'GuiManager',
    # File imports
    'get_open_file',
    'get_save_file',
    'PlatformDirectoryService',
    # Process imports
    'execute_file_as_subprocess',
    # Collision imports
    'CollisionService',
    'SpatialGrid',
    # Environment imports
    'EnvironmentService',
    # Physics imports
    'PhysicsEngineService',
    # Scene imports
    'HasSceneMixin',
    'SceneRunnerService',
    # Scene events imports
    'SceneEvent',
    'SceneEventType',
    'SceneEventBus',
    # Menu registry imports
    'MenuRegistry',
    'MenuItemDescriptor',
    # Canvas imports
    'CanvasObjectManagmenentService',
    # Viewport imports
    'ViewportPanningService',
    'ViewportZoomingService',
    'ViewportGriddingService',
    'ViewportStatusService',
    # Timer imports
    'TimerService',
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
