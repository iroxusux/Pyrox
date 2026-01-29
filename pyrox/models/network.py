"""Network ABC module for Pyrox framework.

This module provides network-related abstract base classes and utilities,
including IPv4 address representation and network operation interfaces.
"""
from typing import Union


class Ipv4Address:
    """IPv4 Address representation.

    This class provides a robust representation of IPv4 addresses with validation,
    supporting construction from strings, bytes, bytearrays, and memoryviews.

    Args:
        address: The IPv4 address as a string (e.g., "192.168.1.1") or
                4-byte sequence.

    Attributes:
        octects: The four octets of the IPv4 address as bytes.

    Raises:
        ValueError: If the address format is invalid or has wrong number of octets.
        TypeError: If address type is not supported.
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
        """Get the four octets of the IPv4 address.

        Returns:
            bytes: The four octets as a bytes object.
        """
        return self._octets

    @octects.setter
    def octects(self, value: bytes) -> None:
        """Set the four octets of the IPv4 address.

        Args:
            value: The four octets as bytes, bytearray, or memoryview.

        Raises:
            TypeError: If value is not bytes, bytearray, or memoryview.
            ValueError: If value doesn't have exactly 4 octets.
        """
        if not isinstance(value, (bytes, bytearray, memoryview)):
            raise TypeError('octets must be bytes, bytearray, or memoryview')
        if len(value) != 4:
            raise ValueError('IPv4 address must have exactly 4 octets')
        self._octets = bytes(value)
