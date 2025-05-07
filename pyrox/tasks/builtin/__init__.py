"""built-in tasks for emulation preparation project
    """
from .exit import ExitTask
from .file import FileTask
from .help import HelpTask
from .preferences import PreferencesTask
from .tools import ControllerVerifyTask

ALL_TASKS = [
    ControllerVerifyTask,
    ExitTask,
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
