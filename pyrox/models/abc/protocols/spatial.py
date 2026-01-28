"""Spacial object protocols that extend coordinate protocols.
"""
from pyrox.models.abc.protocols.coord import Area2D, Area3D
from pyrox.interfaces import IRotatable, ISpatial2D, ISpatial3D


class Rotatable(
    IRotatable
):
    """Protocol for rotatable spatial objects."""

    def __init__(
        self,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        super().__init__()
        self._pitch = pitch
        self._yaw = yaw
        self._roll = roll

    def get_rotation(self) -> tuple[float, float, float]:
        """Get the rotation of this object in degrees.

        Returns:
            float: The rotation of this object in degrees.
        """
        return (self._pitch, self._yaw, self._roll)

    def set_rotation(
        self,
        pitch: float,
        yaw: float,
        roll: float
    ) -> None:
        """Set the rotation of this object in degrees.

        Args:
            pitch (float): The pitch rotation to set in degrees.
            yaw (float): The yaw rotation to set in degrees.
            roll (float): The roll rotation to set in degrees.
        """
        self._pitch = pitch
        self._yaw = yaw
        self._roll = roll

    def get_pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        return self._pitch

    def get_yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        return self._yaw

    def get_roll(self) -> float:
        """Get the roll rotation of the scene object."""
        return self._roll

    def set_pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        self._pitch = pitch

    def set_yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        self._yaw = yaw

    def set_roll(self, roll: float) -> None:
        """Set the roll rotation of the scene object."""
        self._roll = roll


class Spatial2D(
    ISpatial2D,
    Area2D,
    Rotatable,
):
    """Protocol for 2D spatial objects."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        Area2D.__init__(
            self,
            x=x,
            y=y,
        )
        Rotatable.__init__(
            self,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )


class Spatial3D(
    ISpatial3D,
    Area3D,
    Rotatable,
):
    """Protocol for 3D spatial objects."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ) -> None:
        Area3D.__init__(
            self,
            x=x,
            y=y,
            z=z,
        )
        Rotatable.__init__(
            self,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )


__all__ = [
    "Spatial2D",
    "Spatial3D",
    "Rotatable",
]
