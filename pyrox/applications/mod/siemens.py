"""Siemens specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import IntrospectiveModule


class G115Drive(IntrospectiveModule):
    """G115 Drive Module for Siemens PLCs.

    This module represents a G115 drive in a Siemens PLC system.
    It is used to control and monitor the drive's operation.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return 'ETHERNET-MODULE'

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
