"""Spacial object protocols that extend coordinate protocols.
"""
from typing import Protocol, runtime_checkable
from pyrox.interfaces.protocols.coord import IArea2D, IArea3D


@runtime_checkable
class IRotatable(
    Protocol
):
    """Protocol for rotatable spatial objects."""

    @property
    def pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        return self.get_pitch()

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        self.set_pitch(pitch)

    @property
    def yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        return self.get_yaw()

    @yaw.setter
    def yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        self.set_yaw(yaw)

    @property
    def roll(self) -> float:
        """Get the roll rotation of the scene object."""
        return self.get_roll()

    @roll.setter
    def roll(self, roll: float) -> None:
        """Set the roll rotation of the scene object."""
        self.set_roll(roll)

    @property
    def rotation(self) -> tuple[float, float, float]:
        """Get the rotation of this object in degrees.

        Returns:
            float: The rotation of this object in degrees.
        """
        return self.get_rotation()

    def get_rotation(self) -> tuple[float, float, float]:
        """Get the rotation of this object in degrees.

        Returns:
            tuple[float, float, float]: The rotation of this object in degrees.
        """
        ...

    def set_rotation(
        self,
        pitch: float,
        yaw: float,
        roll: float,
    ) -> None:
        """Set the rotation of this object in degrees.

        Args:
            pitch (float): The pitch rotation to set in degrees.
            yaw (float): The yaw rotation to set in degrees.
            roll (float): The roll rotation to set in degrees.
        """
        ...

    def get_pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        ...

    def get_yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        ...

    def get_roll(self) -> float:
        """Get the roll rotation of the scene object."""
        ...

    def set_pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        ...

    def set_yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        ...

    def set_roll(self, roll: float) -> None:
        """Set the roll rotation of the scene object."""
        ...


class ISpatial2D(
    IArea2D,
    IRotatable,
):
    """Protocol for 2D spatial objects."""


class ISpatial3D(
    IArea3D,
    ISpatial2D,
):
    """Protocol for 3D spatial objects."""


__all__ = [
    "ISpatial2D",
    "ISpatial3D",
    "IRotatable"
]
