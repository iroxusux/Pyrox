"""Allen Bradley Module Meta Defintions for controls integrations.
"""

from __future__ import annotations

from typing import Type
from pyrox.models.abc import FactoryTypeMeta

from ..plc import IntrospectiveModule, ModuleWarehouseFactory, ModuleVendorFactory


__all__ = (
    'SewModule',
)


class SewModuleFactory(ModuleVendorFactory):
    """Factory for creating Allen Bradley module instances."""

    _registered_types: dict = {}


class SewModuleMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Warehouse subclasses."""

    @classmethod
    def get_class(cls) -> Type['SewModule']:
        try:
            return SewModule
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return SewModuleFactory


class SewModule(IntrospectiveModule, metaclass=SewModuleMeta):
    """Allen Bradley Module ABC.
    """


ModuleWarehouseFactory.register_type(SewModuleFactory)
