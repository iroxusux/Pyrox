"""Siemens Module Meta Defintions for controls integrations.
"""

from __future__ import annotations

from typing import Type
from pyrox.models.abc import FactoryTypeMeta

from ..plc import IntrospectiveModule, ModuleWarehouseFactory, ModuleVendorFactory


__all__ = (
    'SiemensModule',
)


class SiemensModuleFactory(ModuleVendorFactory):
    """Factory for creating Siemens module instances."""

    _registered_types: dict = {}


class SiemensModuleMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Warehouse subclasses."""

    @classmethod
    def get_class(cls) -> Type['SiemensModule']:
        try:
            return SiemensModule
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return SiemensModuleFactory


class SiemensModule(IntrospectiveModule, metaclass=SiemensModuleMeta):
    """Siemens Module ABC.
    """


ModuleWarehouseFactory.register_type(SiemensModuleFactory)
