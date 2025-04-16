"""abc meta types
    """
from . import test_abc


from .application import (
    ApplicationTask,
    BaseMenu,
    PartialApplication,
    PartialApplicationConfiguration,
)

from .factory import (
    Factory
)

from .meta import (
    SnowFlake,
    PartialView,
    PartialViewConfiguration
)

from .model import (
    Model
)

from .view import (
    View
)

from .viewmodel import (
    ViewModel
)


__version__ = '1.0.0'

__all__ = (
    'ApplicationTask',
    'BaseMenu',
    'Factory',
    'Model',
    'PartialApplication',
    'PartialApplicationConfiguration',
    'PartialView',
    'PartialViewConfiguration',
    'SnowFlake',
    'test_abc',
    'View',
    'ViewModel',
)
