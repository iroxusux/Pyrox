"""SEW Euro specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.abc.factory import FactoryTypeMeta
from typing import Self
from pyrox.models.plc import (
    IntrospectiveModule,
    ModuleControlsType,
    ModuleWarehouse,
    Rung
)


class SewModuleFactory(ModuleWarehouse):
    """Factory for creating SEW module instances."""


class SewModule(IntrospectiveModule, metaclass=FactoryTypeMeta[Self, SewModuleFactory]):
    """SEW Module ABC.
    """
    supports_registering = False  # SEW modules do not support registering directly

    def __init_subclass__(cls, **kwargs):
        cls.supports_registering = True  # Subclasses can support registering
        return super().__init_subclass__(**kwargs)

    @classmethod
    def get_factory(cls):
        return SewModuleFactory


class SewSafeMoviDrive(SewModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-SAFETY-STANDARD-MODULE'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.DRIVE

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        return '130'

    @property
    def input_size(self) -> str:
        """The input size of the module."""
        return '16'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        return '120'

    @property
    def output_size(self) -> str:
        """The output size of the module."""
        return '16'

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return [
            (r'docs\controls\emu\Demo3D_MoviMotAdv_DataType.L5X', ['DataTypes']),
        ]

    def get_required_standard_rungs(
        self,
        **__,
    ) -> list[Rung]:
        rungs = []
        rungs.append(Rung(
            controller=self.module.controller,
            text=f'COP(zz_Demo3D_{self.module.name}.I,{self.module.name}:I,1)COP({self.module.name}:O,zz_Demo3D_{self.module.name}.O,1);',
            comment='Standard Emulation Logic for SEW Safe MoviDrive'
        ))

        return rungs

    def get_required_tags(
        self,
        **__,
    ) -> list[dict]:
        tags = []
        tags.append({
            'tag_name': self.get_standard_input_tag_name(),
            'datatype': 'Demo3D_MoviMotAdv',
        })
        return tags

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'
