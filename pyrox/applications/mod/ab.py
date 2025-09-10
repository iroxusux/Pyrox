"""Allen Bradley specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import AllenBradleyModule, ModuleControlsType


class AllenBradleyGenericSafetyBlock(AllenBradleyModule):
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'GENERIC-SAFETY-BLOCK'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.SAFETY_BLOCK

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return [
            (r'docs\controls\emu\Demo3D_WDint_DataType.L5X', ['DataTypes']),
            (r'docs\controls\emu\Demo3D_CommOK_SBK_DataType.L5X', ['DataTypes'])
        ]

    def get_required_safety_rungs(self):
        rungs = []
        module = self.module
        controller = module.controller
        constructor = module.controller.config.rung_type
        rungs.append(constructor(
            controller=controller,
            text=f'COP(sz_Demo3D_{module.name}_I,{module.name}:I,1);',
            comment='Copy the input data from the emulation tag to the safety block.'
        ))
        return rungs

    def get_required_standard_rungs(self):
        rungs = []
        module = self.module
        controller = module.controller
        constructor = module.controller.config.rung_type
        rungs.append(constructor(
            controller=controller,
            text=f'[XIO(zz_Demo3D_{module.name}_I.Word1.0),XIC(zz_Demo3D_{module.name}_I.Word1.1)]FLL(0,zz_Demo3D_{module.name}_I.Word2,2);',  # noqa: E501
            comment='If communication status is lost to the SBK via the emulation model, zero out the SBK words.'
        ))

        rungs.append(constructor(
            controller=controller,
            text=f'COP({module.name}:O,zz_Demo3D_{module.name}_O,1);',
            comment='Copy the output data from the safety block to the emulation tag.'
        ))

        return rungs

    def get_required_tags(self) -> list[dict]:
        tags = []
        tags.append({
            'tag_name': self.get_standard_input_tag_name(),
            'datatype': 'Demo3D_WDint',
        })
        tags.append({
            'tag_name': self.get_safety_input_tag_name(),
            'class_': 'Safety',
            'datatype': 'Demo3D_WDint',
        })
        tags.append({
            'tag_name': self.get_standard_output_tag_name(),
            'datatype': 'DINT',
        })
        return tags

    def get_safety_input_tag_name(self):
        return f'sz_Demo3D_{self.module.name}_I'

    def get_standard_input_tag_name(self):
        return f'zz_Demo3D_{self.module.name}_I'

    def get_standard_output_tag_name(self):
        return f'zz_Demo3D_{self.module.name}_O'


class AB_1732Es(AllenBradleyGenericSafetyBlock):
    """Allen Bradley 1732ES Safety Block Module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return '1732ES-IB'


class AB_1734IB8S(AllenBradleyGenericSafetyBlock):
    """Allen Bradley 1734-IB8S Module.

    This module represents an Allen Bradley 1734-IB8S input module.
    It is used to control and monitor the input operations in a PLC system.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the 1734-IB8S module."""
        return '1734-IB8S'


class AB_1756ENT(AllenBradleyModule):
    """Allen Bradley 1756-EN*T Module.

    This module represents an Allen Bradley 1756-EN*T Ethernet module.
    It is used to control and monitor the Ethernet communication in a PLC system.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the 1756-EN*T module."""
        return '1756-EN'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.ETHERNET


class AB_1756L8ES(AllenBradleyModule):
    """Allen Bradley 1756L8*ES Module.

    This module represents an Allen Bradley 1756-L8*ES PLC module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the 1756-L8*ES module."""
        return '1756-L8'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.PLC


class AB_1791ES(AllenBradleyGenericSafetyBlock):
    """Allen Bradley 1791ES Safety Block Module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return '1791ES-IB'
