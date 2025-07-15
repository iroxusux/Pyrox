"""built-in tasks for pyrox.
tasks operate as plugins to the main application menubar.
each directory and file is scanned by pyrox to discover tasks and automatically inject them into the application.
    """
from .file import FileTask
from .help import HelpTask
from .edit import PreferencesTask


__all__ = (
    'ControllerVerifyTask',
    'ExitTask',
    'FileTask',
    'HelpTask',
    'PreferencesTask',
    'ALL_TASKS',
)
