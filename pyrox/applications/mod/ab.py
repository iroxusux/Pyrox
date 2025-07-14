"""Allen Bradley specific PLC Modules.
"""
from __future__ import annotations
from pyrox.models.plc import IntrospectiveModule


class AB_1732EsSafetyBlock(IntrospectiveModule):
    """Allen Bradley 1732ES Safety Block Module.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the G115 drive module."""
        return '1732ES-IB'


class AB_1734IB8S(IntrospectiveModule):
    """Allen Bradley 1734-IB8S Module.

    This module represents an Allen Bradley 1734-IB8S input module.
    It is used to control and monitor the input operations in a PLC system.
    """
    @property
    def catalog_number(self) -> str:
        """The catalog number of the 1734-IB8S module."""
        return '1734-IB8S'
