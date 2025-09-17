"""Allen Bradley Module Meta Defintions for controls integrations.
"""
from typing import Self
from pyrox.models.abc.factory import FactoryTypeMeta

from .imodule import IntrospectiveModule, ModuleWarehouse


__all__ = (
    'AllenBradleyModule',
    'AllenBradleyModuleFactory',
)


class AllenBradleyModuleFactory(ModuleWarehouse):
    """Factory for creating Allen Bradley module instances."""


class AllenBradleyModule(IntrospectiveModule, metaclass=FactoryTypeMeta[Self, AllenBradleyModuleFactory]):
    """Allen Bradley Module ABC.
    """

    supports_registering = False  # Allen Bradley modules do not support registering directly

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True  # Subclasses can support registering
        return super().__init_subclass__(**kwargs)

    @classmethod
    def get_factory(cls):
        return AllenBradleyModuleFactory
