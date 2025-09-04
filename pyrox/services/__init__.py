"""services module for pyrox
"""

from . import (
    class_services,
    eplan,
    file,
    notify_services,
    plc_services,
    reg,
    test_services,
    utkinter,
)

from .reg import register_generator


__all__ = (
    'class_services',
    'eplan',
    'file',
    'notify_services',
    'plc_services',
    'reg',
    'register_generator',
    'test_services',
    'utkinter',
)
