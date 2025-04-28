"""built-in tasks for emulation preparation project
    """
from .exit import ExitTask
from .help import HelpTask
from .preferences import PreferencesTask

ALL_TASKS = [
    ExitTask,
    HelpTask,
    PreferencesTask,
]


__version__ = "1.0.0"

__all__ = (
    'ExitTask',
    'HelpTask',
    'PreferencesTask',
    'ALL_TASKS',
)
