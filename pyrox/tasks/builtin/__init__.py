"""built-in tasks for emulation preparation project
    """
from .file import FileTask
from .help import HelpTask
from .preferences import PreferencesTask

ALL_TASKS = [
    FileTask,
    HelpTask,
    PreferencesTask,
]


__version__ = "1.0.0"

__all__ = (
    'ControllerVerifyTask',
    'ExitTask',
    'FileTask',
    'HelpTask',
    'PreferencesTask',
    'ALL_TASKS',
)
