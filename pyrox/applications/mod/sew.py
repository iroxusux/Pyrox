"""SEW Euro specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import SewModule, ModuleControlsType


class SewSafeMoviDrive(SewModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-SAFETY-STANDARD-MODULE'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.DRIVE

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return [
            (r'docs\controls\emu\Demo3D_MoviMotAdv_DataType.L5X', ['DataTypes']),
        ]

    def get_required_standard_rungs(self):
        rungs = []

        return rungs

    def get_required_tags(self) -> list[dict]:
        tags = []
        tags.append({
            'tag_name': self.get_standard_input_tag_name(),
            'datatype': 'Demo3D_MoviMotAdv',
        })
        return tags

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}'
