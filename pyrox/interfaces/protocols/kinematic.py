"""Kinematic protocols for motion representation.
Defines interfaces for velocity and acceleration in 2D and 3D space.
"""
from typing import (Protocol)
from pyrox.interfaces.protocols.spatial import ISpatial2D


class IVelocity2D(ISpatial2D):
    """Protocol for 2D velocity (linear motion)."""
    _velocity_x: float
    _velocity_y: float

    def get_velocity_x(self) -> float:
        return self._velocity_x

    def set_velocity_x(self, value: float) -> None:
        self._velocity_x = value

    @property
    def velocity_x(self) -> float:
        """Get the X component of velocity."""
        return self.get_velocity_x()

    @velocity_x.setter
    def velocity_x(self, value: float) -> None:
        """Set the X component of velocity.

        Args:
            value (float): The X component of velocity.
        """
        self.set_velocity_x(value)

    def get_velocity_y(self) -> float:
        return self._velocity_y

    def set_velocity_y(self, value: float) -> None:
        self._velocity_y = value

    @property
    def velocity_y(self) -> float:
        """Get the Y component of velocity."""
        return self.get_velocity_y()

    @velocity_y.setter
    def velocity_y(self, value: float) -> None:
        """Set the Y component of velocity.

        Args:
            value (float): The Y component of velocity.
        """
        self.set_velocity_y(value)

    def get_linear_velocity(self) -> tuple[float, float]:
        return self.get_velocity_x(), self.get_velocity_y()

    def set_linear_velocity(self, vx: float, vy: float) -> None:
        self.set_velocity_x(vx)
        self.set_velocity_y(vy)

    @property
    def linear_velocity(self) -> tuple[float, float]:
        """Get velocity as (vx, vy)."""
        return self.get_linear_velocity()

    @linear_velocity.setter
    def linear_velocity(self, value: tuple[float, float]) -> None:
        """Set velocity as (vx, vy).

        Args:
            value (tuple[float, float]): Velocity tuple.
        """
        self.set_linear_velocity(value[0], value[1])

    def get_speed(self) -> float:
        """Get scalar speed (magnitude of velocity)."""
        vx, vy = self.get_linear_velocity()
        return (vx**2 + vy**2) ** 0.5

    @property
    def speed(self) -> float:
        """Get scalar speed (magnitude of velocity)."""
        return self.get_speed()


class IAngularVelocity(Protocol):
    """Protocol for rotational velocity."""

    @property
    def angular_velocity(self) -> tuple[float, float, float]:
        """Get angular velocity as (pitch, yaw, roll) rates."""
        return self.get_angular_velocity()

    def get_angular_velocity(self) -> tuple[float, float, float]: ...
    def set_angular_velocity(self, velocity: tuple[float, float, float]) -> None: ...


class IKinematic2D(IVelocity2D):
    """Protocol for full 2D kinematic state (velocity + acceleration)."""
    _acceleration_x: float
    _acceleration_y: float

    def get_acceleration_x(self) -> float:
        return self._acceleration_x

    def set_acceleration_x(self, value: float) -> None:
        self._acceleration_x = value

    @property
    def acceleration_x(self) -> float:
        return self.get_acceleration_x()

    @acceleration_x.setter
    def acceleration_x(self, value: float) -> None:
        self.set_acceleration_x(value)

    def get_acceleration_y(self) -> float:
        return self._acceleration_y

    def set_acceleration_y(self, value: float) -> None:
        self._acceleration_y = value

    @property
    def acceleration_y(self) -> float:
        return self.get_acceleration_y()

    @acceleration_y.setter
    def acceleration_y(self, value: float) -> None:
        self.set_acceleration_y(value)

    def get_acceleration(self) -> float:
        """Get scalar acceleration (magnitude of acceleration vector)."""
        ax, ay = self.get_linear_acceleration()
        return (ax**2 + ay**2) ** 0.5

    @property
    def acceleration(self) -> float:
        return self.get_acceleration()

    def get_linear_acceleration(self) -> tuple[float, float]:
        return self.get_acceleration_x(), self.get_acceleration_y()

    def set_linear_acceleration(self, ax: float, ay: float) -> None:
        self.set_acceleration_x(ax)
        self.set_acceleration_y(ay)

    @property
    def linear_acceleration(self) -> tuple[float, float]:
        """Linear acceleration (ax, ay) in m/s²."""
        return self.get_linear_acceleration()


__all__ = [
    "IVelocity2D",
    "IAngularVelocity",
    "IKinematic2D",
]
