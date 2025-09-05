"""Allen Bradley Module Meta Defintions for controls integrations.
"""

from __future__ import annotations

from typing import Type
from pyrox.models.abc import FactoryTypeMeta

from ..plc import IntrospectiveModule, ModuleWarehouseFactory, ModuleVendorFactory


__all__ = (
    'AllenBradleyModule',
)


class AllenBradleyModuleFactory(ModuleVendorFactory):
    """Factory for creating Allen Bradley module instances."""

    _registered_types: dict = {}


class AllenBradleyModuleMeta(FactoryTypeMeta):
    """Metaclass for auto-registering Warehouse subclasses."""

    @classmethod
    def get_class(cls) -> Type['AllenBradleyModule']:
        try:
            return AllenBradleyModule
        except NameError:
            return None

    @classmethod
    def get_factory(cls):
        return AllenBradleyModuleFactory


class AllenBradleyModule(IntrospectiveModule, metaclass=AllenBradleyModuleMeta):
    """Allen Bradley Module ABC.
    """


ModuleWarehouseFactory.register_type(AllenBradleyModuleFactory)
