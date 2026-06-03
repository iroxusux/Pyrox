"""services module for pyrox
"""
# Service imports
from .service import ServiceManager

# File imports
from .file import (
    get_open_file,
    get_save_file,
    is_file_readable,
    PlatformDirectoryService
)

# Environment imports
from .env import (
    EnvManager,
    get_env,
    set_env,
    set_key,
    get_default_date_format,
    get_default_formatter
)

# Logging imports
from .logging import (
    log,
    LoggingManager
)

# Theme imports
from .theme import ThemeManager

# Bus imports
from .bus import (
    EventType,
    Event,
    EventBus,
)

# Menu registry imports
from .menu_registry import (
    MenuRegistry,
    MenuItemDescriptor
)

# GUI imports
from .gui import GuiManager
from .gui_state import GuiStateService


# Process imports
from .process import execute_file_as_subprocess

# Status imports
from .status import (
    StatusUpdateEventType,
    StatusUpdateEvent,
    StatusUpdateEventBus
)

# Timer imports
from .timer import TimerService

# Other service imports
from . import (
    archive,
    byte,
    decorate,
    dict,
    logic,
    object,
    progress,
    search,
    status,
    stream,
    timer,
    xml,
)


__all__ = (
    # Service imports
    'ServiceManager',
    # File imports
    'get_open_file',
    'get_save_file',
    'is_file_readable',
    'PlatformDirectoryService',
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
    # Bus imports
    'EventType',
    'Event',
    'EventBus',
    # Theme imports
    'ThemeManager',
    # GUI imports
    'GuiManager',
    'GuiStateService',
    # Process imports
    'execute_file_as_subprocess',
    # Status imports
    'StatusUpdateEventType',
    'StatusUpdateEvent',
    'StatusUpdateEventBus',
    # Menu registry imports
    'MenuRegistry',
    'MenuItemDescriptor',
    # Timer imports
    'TimerService',
    # Other service imports
    'archive',
    'byte',
    'decorate',
    'dict',
    'logic',
    'status',
    'object',
    'progress',
    'search',
    'stream',
    'timer',
    'xml',
)
