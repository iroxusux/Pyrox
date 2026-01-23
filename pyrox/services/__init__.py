"""services module for pyrox
"""

from . import env  # MUST COME FIRST, loading env affects logging for global logging level
from .env import EnvManager, get_env, set_env, set_key, get_default_date_format, get_default_formatter

from . import logging  # MUST COME SECOND, logging must be configured before other imports
from .logging import log, LoggingManager

from . import theme  # MUST COME THIRD, theme may be needed by gui on initialization
from .theme import ThemeManager

from . import gui  # MUST COME FOURTH, gui imports sub-systems which on some systems needs to be loaded early
from .gui import GuiManager

from . import file
from .file import get_open_file, PlatformDirectoryService

from . import (
    archive,
    bit,
    byte,
    decorate,
    dict,
    factory,
    logic,
    notify_services,
    object,
    progress,
    search,
    stream,
    test,
    timer,
    xml,
)


__all__ = (
    'env',
    'logging',
    'archive',
    'bit',
    'byte',
    'decorate',
    'dict',
    'EnvManager',
    'factory',
    'file',
    'get_default_date_format',
    'get_default_formatter',
    'get_env',
    'gui',
    'GuiManager',
    'log',
    'LoggingManager',
    'logic',
    'notify_services',
    'object',
    'progress',
    'search',
    'set_env',
    'set_key',
    'stream',
    'test',
    'theme',
    'ThemeManager',
    'timer',
    'xml',
    'get_open_file',
    'PlatformDirectoryService',
)
