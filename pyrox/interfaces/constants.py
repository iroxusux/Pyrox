"""Constants for ControlRox Applications.
"""
from enum import Enum


class EnvironmentKeysCore(Enum):
    """Environment keys for core settings.
    """
    APP_NAME = "APP_NAME"
    APP_AUTHOR = "APP_AUTHOR"
    APP_DESCRIPTION = "APP_DESCRIPTION"
    APP_URL = "APP_URL"
    APP_ICON = "APP_ICON"
    APP_DEBUG_MODE = "APP_DEBUG_MODE"
    APP_WINDOW_TITLE = "APP_WINDOW_TITLE"


class EnvironmentKeysDirectory(Enum):
    """Environment keys for directory settings.
    """
    DIR_DATA = "DIR_DATA"
    DIR_TEMP = "DIR_TEMP"
    DIR_BACKUP = "DIR_BACKUP"
    DIR_CONFIG = "DIR_CONFIG"
    DIR_PLUGINS = "DIR_PLUGINS"


class EnvironmentKeysLogging(Enum):
    """Environment keys for logging settings.
    """
    LOG_LEVEL = "LOG_LEVEL"
    LOG_FILE = "LOG_FILE"
    LOG_FORMAT = "LOG_FORMAT"
    LOG_DATE_FORMAT = "LOG_DATE_FORMAT"
    LOG_FILE_MAX_SIZE = "LOG_FILE_MAX_SIZE"
    LOG_FILE_BACKUP_COUNT = "LOG_FILE_BACKUP_COUNT"
    LOG_TO_CONSOLE = "LOG_TO_CONSOLE"
    LOG_TO_FILE = "LOG_TO_FILE"
    LOG_SUCCESS_TUPLE = "LOG_SUCCESS_TUPLE"
    LOG_FAILURE_TUPLE = "LOG_FAILURE_TUPLE"
    LOG_NOTICE_TUPLE = "LOG_NOTICE_TUPLE"


class EnvironmentKeysUI(Enum):
    """Environment keys for UI settings.
    """
    UI_AUTO_INIT = "UI_AUTO_INIT"
    UI_FRAMEWORK = "UI_FRAMEWORK"
    UI_THEME = "UI_THEME"
    UI_LANGUAGE = "UI_LANGUAGE"
    UI_WINDOW_SIZE = "UI_WINDOW_SIZE"
    UI_WINDOW_POSITION = "UI_WINDOW_POSITION"
    UI_WINDOW_FULLSCREEN = "UI_WINDOW_FULLSCREEN"
    UI_WINDOW_STATE = "UI_WINDOW_STATE"
    UI_FONT_FAMILY = "UI_FONT_FAMILY"
    UI_FONT_SIZE = "UI_FONT_SIZE"
    UI_LADDER_THEME = "UI_LADDER_THEME"
    UI_SIDEBAR_WIDTH = "UI_SIDEBAR_WIDTH"
    UI_LOG_WINDOW_HEIGHT = "UI_LOG_WINDOW_HEIGHT"


class EnvironmentKeys:
    """Environment keys for application settings.
    """
    core = EnvironmentKeysCore
    directory = EnvironmentKeysDirectory
    ui = EnvironmentKeysUI
    logging = EnvironmentKeysLogging
