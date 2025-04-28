"""built-in tasks for emulation preparation project
    """
from .exit import ExitTask


ALL_TASKS = [
    ExitTask,
]


__version__ = "1.0.0"

__all__ = (
    'ExitTask',
    'ALL_TASKS',
)
