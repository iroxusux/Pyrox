"""built-in tasks for pyrox.
tasks operate as plugins to the main application menubar.
each directory and file is scanned by pyrox to discover tasks and automatically inject them into the application.
    """
from . import (
    edit,
    file,
    help,
    tools,
    view
)


__all__ = (
    'edit',
    'file',
    'help',
    'tools',
    'view',
)
