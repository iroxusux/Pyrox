"""Siemens Module Meta Defintions for controls integrations.
"""

from __future__ import annotations

from typing import Self
from pyrox.models.abc import FactoryTypeMeta

from .imodule import IntrospectiveModule, ModuleWarehouse


__all__ = (
    'SiemensModule',
    'SiemensModuleFactory',
)


class SiemensModuleFactory(ModuleWarehouse):
    """Factory for creating Siemens module instances."""


class SiemensModule(IntrospectiveModule, metaclass=FactoryTypeMeta[Self, SiemensModuleFactory]):
    """Siemens Module ABC.
    """
    supports_registering = False  # Siemens modules do not support registering directly

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True  # Subclasses can support registering
        return super().__init_subclass__(**kwargs)

    @classmethod
    def get_factory(cls):
        return SiemensModuleFactory
