"""built-in tasks for emulation preparation project
    """
from .generate import ControllerGenerateTask
from .verify import ControllerVerifyTask

__all__ = (
    'ControllerGenerateTask',
    'ControllerVerifyTask',
)
