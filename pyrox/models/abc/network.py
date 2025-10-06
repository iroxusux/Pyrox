"""Network abc module
"""
from typing import Union


class Ipv4Address:
    """IPv4 Address representation
    """

    def __init__(
            self,
            address: Union[str, bytes, bytearray, memoryview]
    ):
        if isinstance(address, str):
            parts = address.split('.')
            if len(parts) != 4:
                raise ValueError('IPv4 address must have exactly 4 octets')
            self.octects = bytes(int(part) for part in parts)
        elif isinstance(address, (bytes, bytearray, memoryview)):
            if len(address) != 4:
                raise ValueError('IPv4 address must have exactly 4 octets')
            self.octects = bytes(address)
        else:
            raise TypeError('address must be str, bytes, bytearray, or memoryview')

    def __str__(self) -> str:
        return '.'.join(str(octet) for octet in self.octects)

    def __repr__(self) -> str:
        return f"Ipv4Address('{str(self)}')"

    @property
    def octects(self) -> bytes:
        return self._octets

    @octects.setter
    def octects(self, value: bytes) -> None:
        if not isinstance(value, (bytes, bytearray, memoryview)):
            raise TypeError('octets must be bytes, bytearray, or memoryview')
        if len(value) != 4:
            raise ValueError('IPv4 address must have exactly 4 octets')
        self._octets = bytes(value)
