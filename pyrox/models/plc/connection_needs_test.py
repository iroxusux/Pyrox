"""Connection parameters and commands for a PLC
"""
from enum import Enum
from typing import Callable


class ConnectionParameters:
    """connection parameters for connecting to a plc
    """

    def __init__(self,
                 ip_address: str,
                 slot: int,
                 rpi: int = 50):
        # explicit type-casting to enform type protection for this class
        slot = int(slot)
        rpi = int(rpi)

        if len(ip_address.split('.')) != 4:
            raise ValueError('Ip addresses must be specified in groups of 4 - e.g. 192.168.1.2')

        self._ip_address: str = ip_address  # PLC IP Address
        self._slot: int = slot              # PLC Slot
        self._rpi: float = rpi              # PLC Requested Packet Interval

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def rpi(self) -> int:
        return self._rpi

    @property
    def slot(self) -> int:
        return self._slot


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
