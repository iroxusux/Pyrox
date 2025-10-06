"""Connection parameters and commands for a PLC
"""
from enum import Enum
from typing import Callable
from pyrox.models.abc.network import Ipv4Address


class ConnectionParameters:

    def __init__(
        self,
        ip_address: Ipv4Address,
        slot: int,
        rpi: int = 250
    ) -> None:
        self.ip_address = ip_address
        self.slot = slot
        self.rpi = rpi

    @property
    def rpi(self) -> float:
        return self._rpi

    @rpi.setter
    def rpi(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError('rpi must be a number')
        if value < 1:
            raise ValueError('rpi must be a positive number')
        self._rpi = float(value)

    @property
    def slot(self) -> int:
        return self._slot

    @slot.setter
    def slot(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError('slot must be an integer')
        if value < 0:
            raise ValueError('slot must be a non-negative integer')
        if value > 16:
            raise ValueError('slot must be between 0 and 16')
        self._slot = value


class ConnectionCommandType(Enum):
    NA = 0
    READ = 1
    WRITE = 2


class ConnectionCommand:
    """Connection Command for a PLC
    """

    def __init__(self,
                 type: ConnectionCommandType,
                 tag_name: str,
                 tag_value: int,
                 data_type: int,
                 response_cb: Callable):
        self._type = type
        self._tag_name = tag_name
        self._tag_value = tag_value
        self._data_type = data_type
        self._response_cb = response_cb

    @property
    def type(self) -> ConnectionCommandType:
        return self._type

    @property
    def tag_name(self) -> str:
        return self._tag_name

    @property
    def tag_value(self) -> int:
        return self._tag_value

    @property
    def data_type(self) -> int:
        return self._data_type

    @property
    def response_cb(self) -> Callable:
        return self._response_cb


class ControllerConnection:
    """Controller Connection for a PLC
    """

    def __init__(
        self,
        parameters: ConnectionParameters
    ) -> None:
        self.parameters = parameters
        self.is_connected = False
