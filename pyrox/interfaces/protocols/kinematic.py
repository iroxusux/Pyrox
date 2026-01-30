"""Kinematic protocols for motion representation.
Defines interfaces for velocity and acceleration in 2D and 3D space.
"""
from typing import (
    runtime_checkable,
    Protocol,
)
from .spatial import ISpatial2D, ISpatial3D


@runtime_checkable
class IVelocity2D(
    ISpatial2D,
    Protocol
):
    """Protocol for 2D velocity (linear motion)."""

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

    @property
    def linear_velocity(self) -> tuple[float, float]:
        """Get velocity as (vx, vy)."""
        return self.get_linear_velocity()

    @property
    def speed(self) -> float:
        """Get scalar speed (magnitude of velocity)."""
        return self.get_speed()

    def get_velocity_x(self) -> float: ...
    def set_velocity_x(self, value: float) -> None: ...
    def get_velocity_y(self) -> float: ...
    def set_velocity_y(self, value: float) -> None: ...
    def get_linear_velocity(self) -> tuple[float, float]: ...
    def set_linear_velocity(self, vx: float, vy: float) -> None: ...
    def get_speed(self) -> float: ...


class IVelocity3D(
    IVelocity2D,
    ISpatial3D
):
    """Protocol for 3D velocity."""

    @property
    def velocity_z(self) -> float:
        """Get the Z component of velocity."""
        return self.get_velocity_z()

    @velocity_z.setter
    def velocity_z(self, value: float) -> None:
        """Set the Z component of velocity.

        Args:
            value (float): The Z component of velocity.
        """
        self.set_velocity_z(value)

    def get_velocity_z(self) -> float: ...
    def set_velocity_z(self, value: float) -> None: ...
    def get_linear_velocity(self) -> tuple[float, float, float]: ...  # type: ignore


@runtime_checkable
class IAngularVelocity(Protocol):
    """Protocol for rotational velocity."""

    @property
    def angular_velocity(self) -> tuple[float, float, float]:
        """Get angular velocity as (pitch, yaw, roll) rates."""
        return self.get_angular_velocity()

    def get_angular_velocity(self) -> tuple[float, float, float]: ...
    def set_angular_velocity(self, velocity: tuple[float, float, float]) -> None: ...


@runtime_checkable
class IKinematic2D(
    IVelocity2D,
    Protocol,
):
    """Protocol for full 2D kinematic state (velocity + acceleration)."""

    @property
    def acceleration_x(self) -> float:
        return self.get_acceleration_x()

    @acceleration_x.setter
    def acceleration_x(self, value: float) -> None:
        self.set_acceleration_x(value)

    @property
    def acceleration_y(self) -> float:
        return self.get_acceleration_y()

    @acceleration_y.setter
    def acceleration_y(self, value: float) -> None:
        self.set_acceleration_y(value)

    @property
    def acceleration(self) -> float:
        return self.get_acceleration()

    @property
    def linear_acceleration(self) -> tuple[float, float]:
        """Linear acceleration (ax, ay) in m/s²."""
        return self.get_linear_acceleration()

    def get_acceleration_x(self) -> float: ...
    def set_acceleration_x(self, value: float) -> None: ...
    def get_acceleration_y(self) -> float: ...
    def set_acceleration_y(self, value: float) -> None: ...
    def get_linear_acceleration(self) -> tuple[float, float]: ...
    def set_linear_acceleration(self, ax: float, ay: float) -> None: ...
    def get_acceleration(self) -> float: ...


class IKinematic3D(
    IKinematic2D,
    IVelocity3D,
):
    """Protocol for full 3D kinematic state."""

    @property
    def acceleration_z(self) -> float:
        return self.get_acceleration_z()

    @acceleration_z.setter
    def acceleration_z(self, value: float) -> None:
        self.set_acceleration_z(value)

    @property
    def acceleration(self) -> tuple[float, float, float]:  # type: ignore
        return self.get_acceleration()

    def get_acceleration_z(self) -> float: ...
    def set_acceleration_z(self, value: float) -> None: ...
    def get_acceleration(self) -> tuple[float, float, float]: ...  # type: ignore


__all__ = [
    "IVelocity2D",
    "IVelocity3D",
    "IAngularVelocity",
    "IKinematic2D",
    "IKinematic3D",
]
