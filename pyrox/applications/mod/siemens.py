"""Siemens specific PLC Modules.
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


class G115Drive(SiemensModule):
    """G115 Drive Module for Siemens PLCs.

    This module represents a G115 drive in a Siemens PLC system.
    It is used to control and monitor the drive's operation.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

    @property
    def config_size(self) -> str:
        """The configuration size of the G115 drive module."""
        return '0'

    @property
    def controls_type(self) -> ModuleControlsType:
        """The controls type of the module."""
        return ModuleControlsType.DRIVE

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the G115 drive module."""
        return '101'

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the G115 drive module."""
        return '102'

    @property
    def input_size(self) -> str:
        """The input size of the G115 drive module."""
        return '26'

    @property
    def output_size(self) -> str:
        """The output size of the G115 drive module."""
        return '4'

    @classmethod
    def get_required_imports(cls) -> list[tuple[str, list[str]]]:
        """Get the required datatype imports for the module.

        Returns:
            list[tuple[str, str]]: List of tuples containing the module and class name to import.
        """
        return [
            (r'docs\controls\emu\Demo3D_G115D_Drive_DataType.L5X', ['DataTypes']),
        ]

    def get_required_standard_rungs(
        self,
        **kwargs,
    ) -> list[Rung]:
        index = kwargs.get('index', None)
        if index is None:
            raise ValueError("Index is required for generating standard rungs.")

        cname = self.module.controller.process_name
        pname = self.module.process_name

        i1 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.StatusWord1,{pname}:I.Data[0],1)'
        i2 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.RPMRef,{pname}:I.Data[1],1)'
        i3 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.AmpsRef,{pname}:I.Data[2],1)'
        i4 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.TorqueRef,{pname}:I.Data[3],1)'
        i5 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.FaultCode,{pname}:I.Data[5],1)'
        i6 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.StatusWord4,{pname}:I.Data[6],1)'
        i7 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.SpareInt1,{pname}:I.Data[7],1)'
        i8 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.PowerUnitTempC,{pname}:I.Data[8],1)'
        i9 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.StatusWord5,{pname}:I.Data[9],1)'
        i10 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.MotorTempC,{pname}:I.Data[10],1)'
        i11 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.SafetySTO_Out,{pname}:I.Data[11],1)'
        i12 = f'CPS(zz_Demo3D_{cname}_Siemens_Drives[{index}].Inputs.SafetySTOSts,{pname}:I.Data[12],1)'
        i13 = f'CPS({pname}:O.Data[0],zz_Demo3D_{cname}_Siemens_Drives[{index}].Outputs.ControlWord1,1)'
        i14 = f'CPS({pname}:O.Data[1],zz_Demo3D_{cname}_Siemens_Drives[{index}].Outputs.Setpoint,1)'

        return [Rung(
            controller=self.module.controller,
            text=f'[{i1}{i2}{i3},{i4}{i5},{i6}{i7}{i8},{i9}{i10}{i11},{i12},{i13}{i14}];',
            comment=f'Standard Emulation Logic for Siemens G115 Drive Module {self.module.name}'
        )]

    def get_required_tags(
        self,
        **__,
    ) -> list[dict]:
        tags = []
        cname = self.module.controller.process_name

        tags.append({
            'tag_name': f'zz_Demo3D_{cname}_Siemens_Drives',
            'datatype': 'Demo3D_G115D_Drive',
            'dimensions': '150',
            'description': 'Standard input tag for the G115 drive module.'
        })

        return tags
