"""Turck Module Meta Defintions for controls integrations.
"""

from __future__ import annotations

from typing import Self
from pyrox.models.abc import FactoryTypeMeta

from .mod import IntrospectiveModule, ModuleWarehouse


__all__ = (
    'TurckModule',
    'TurckModuleFactory',
)


class TurckModuleFactory(ModuleWarehouse):
    """Factory for creating Turck module instances."""


class TurckModule(IntrospectiveModule, metaclass=FactoryTypeMeta[Self, TurckModuleFactory]):
    """Turck Module ABC.
    """
    supports_registering = False  # Turck modules do not support registering directly

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True  # Subclasses can support registering
        return super().__init_subclass__(**kwargs)

    @classmethod
    def get_factory(cls):
        return TurckModuleFactory
