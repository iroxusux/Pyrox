"""Kinematic protocols for motion representation.
Defines interfaces for velocity and acceleration in 2D and 3D space.
"""
from pyrox.interfaces import IAngularVelocity, IKinematic2D
from pyrox.models.protocols.spatial import Spatial2D


class AngularVelocity(IAngularVelocity):
    """Protocol for rotational velocity."""

    def __init__(self) -> None:
        self._angular_velocity_x: float = 0.0
        self._angular_velocity_y: float = 0.0
        self._angular_velocity_z: float = 0.0

    def get_angular_velocity(self) -> tuple[float, float, float]:
        return (
            self._angular_velocity_x,
            self._angular_velocity_y,
            self._angular_velocity_z,
        )

    def set_angular_velocity(self, velocity: tuple[float, float, float]) -> None:
        self._angular_velocity_x = velocity[0]
        self._angular_velocity_y = velocity[1]
        self._angular_velocity_z = velocity[2]


class Kinematic2D(Spatial2D, IKinematic2D):
    """Protocol for full 2D kinematic state (velocity + acceleration)."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        acceleration_x: float = 0.0,
        acceleration_y: float = 0.0,
    ) -> None:
        Spatial2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        self._velocity_x: float = velocity_x
        self._velocity_y: float = velocity_y
        self._acceleration_x: float = acceleration_x
        self._acceleration_y: float = acceleration_y

    def get_acceleration_x(self) -> float:
        return self._acceleration_x

    def set_acceleration_x(self, value: float) -> None:
        self.set_linear_acceleration(value, self._acceleration_y)

    def get_acceleration_y(self) -> float:
        return self._acceleration_y

    def set_acceleration_y(self, value: float) -> None:
        self.set_linear_acceleration(self._acceleration_x, value)

    def get_linear_acceleration(self) -> tuple[float, float]:
        return (self._acceleration_x, self._acceleration_y)

    def set_linear_acceleration(self, ax: float, ay: float) -> None:
        self._acceleration_x = ax
        self._acceleration_y = ay

    def get_acceleration(self) -> float:
        return (self._acceleration_x ** 2 + self._acceleration_y ** 2) ** 0.5


__all__ = [
    "Kinematic2D",
    "AngularVelocity",
]
