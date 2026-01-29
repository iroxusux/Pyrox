"""Kinematic protocols for motion representation.
Defines interfaces for velocity and acceleration in 2D and 3D space.
"""
from pyrox.interfaces import IVelocity2D, IVelocity3D, IAngularVelocity, IKinematic2D, IKinematic3D
from pyrox.models.protocols.spatial import Spatial2D, Spatial3D


class Velocity2D(IVelocity2D):
    """Protocol for 2D velocity (linear motion)."""

    def __init__(
        self,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
    ) -> None:
        self._velocity_x: float = velocity_x
        self._velocity_y: float = velocity_y

    def get_velocity_x(self) -> float:
        return self._velocity_x

    def set_velocity_x(self, value: float) -> None:
        self._velocity_x = value

    def get_velocity_y(self) -> float:
        return self._velocity_y

    def set_velocity_y(self, value: float) -> None:
        self._velocity_y = value

    def get_velocity(self) -> tuple[float, float]:
        return (self._velocity_x, self._velocity_y)

    def get_speed(self) -> float:
        return (self._velocity_x ** 2 + self._velocity_y ** 2) ** 0.5


class Velocity3D(
    Velocity2D,
    IVelocity3D,
):
    """Protocol for 3D velocity."""

    def __init__(
        self,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        velocity_z: float = 0.0,
    ) -> None:
        super().__init__(
            velocity_x=velocity_x,
            velocity_y=velocity_y,
        )
        self._velocity_z: float = velocity_z

    def get_velocity_z(self) -> float:
        return self._velocity_z

    def set_velocity_z(self, value: float) -> None:
        self._velocity_z = value

    def get_velocity(self) -> tuple[float, float, float]:  # type: ignore
        return (self._velocity_x, self._velocity_y, self._velocity_z)

    def get_speed(self) -> float:
        return (self._velocity_x ** 2 + self._velocity_y ** 2 + self._velocity_z ** 2) ** 0.5


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


class Kinematic2D(
    Spatial2D,
    Velocity2D,
    IKinematic2D,
):
    """Protocol for full 2D kinematic state (velocity + acceleration)."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
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
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )
        Velocity2D.__init__(
            self,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
        )
        self._acceleration_x: float = acceleration_x
        self._acceleration_y: float = acceleration_y

    def get_acceleration_x(self) -> float:
        return self._acceleration_x

    def set_acceleration_x(self, value: float) -> None:
        self._acceleration_x = value

    def get_acceleration_y(self) -> float:
        return self._acceleration_y

    def set_acceleration_y(self, value: float) -> None:
        self._acceleration_y = value

    def get_acceleration(self) -> tuple[float, float]:
        return (self._acceleration_x, self._acceleration_y)

    def set_acceleration(self, acceleration: tuple[float, float]) -> None:
        self._acceleration_x = acceleration[0]
        self._acceleration_y = acceleration[1]


class Kinematic3D(
    Spatial3D,
    Velocity3D,
    IKinematic3D,
):
    """Protocol for full 3D kinematic state."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        depth: float = 0.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        velocity_x: float = 0.0,
        velocity_y: float = 0.0,
        velocity_z: float = 0.0,
        acceleration_x: float = 0.0,
        acceleration_y: float = 0.0,
        acceleration_z: float = 0.0,
    ) -> None:
        Spatial3D.__init__(
            self,
            x=x,
            y=y,
            z=z,
            width=width,
            height=height,
            depth=depth,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
        )
        Velocity3D.__init__(
            self,
            velocity_x=velocity_x,
            velocity_y=velocity_y,
            velocity_z=velocity_z,
        )
        self._acceleration_x: float = acceleration_x
        self._acceleration_y: float = acceleration_y
        self._acceleration_z: float = acceleration_z

    def get_acceleration_x(self) -> float:
        return self._acceleration_x

    def set_acceleration_x(self, value: float) -> None:
        self._acceleration_x = value

    def get_acceleration_y(self) -> float:
        return self._acceleration_y

    def set_acceleration_y(self, value: float) -> None:
        self._acceleration_y = value

    def get_acceleration_z(self) -> float:
        return self._acceleration_z

    def set_acceleration_z(self, value: float) -> None:
        self._acceleration_z = value

    def get_acceleration(self) -> tuple[float, float, float]:  # type: ignore
        return (self._acceleration_x, self._acceleration_y, self._acceleration_z)

    def set_acceleration(self, acceleration: tuple[float, float, float]) -> None:  # type: ignore
        self._acceleration_x = acceleration[0]
        self._acceleration_y = acceleration[1]
        self._acceleration_z = acceleration[2]


__all__ = [
    "IVelocity2D",
    "IVelocity3D",
    "IAngularVelocity",
    "IKinematic2D",
    "IKinematic3D",
]
