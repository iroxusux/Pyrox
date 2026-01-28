"""Coordinate protocol definitions.
"""
from typing import Generic, TypeVar
from pyrox.interfaces import ICoord2D, IArea2D, ICoord3D, IArea3D

T = TypeVar("T", bound=tuple[float, ...])


class Coord2D(
    ICoord2D,
    Generic[T]
):
    """Protocol for 2D coordinates."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
    ) -> None:
        self._x = x
        self._y = y

    def get_x(self) -> float:
        """Get the X coordinate.

        Returns:
            float: The X coordinate.
        """
        return self._x

    def set_x(self, x: float) -> None:
        """Set the X coordinate.

        Args:
            x (float): The X coordinate.
        """
        self._x = x

    def get_y(self) -> float:
        """Get the Y coordinate.

        Returns:
            float: The Y coordinate.
        """
        return self._y

    def set_y(self, y: float) -> None:
        """Set the Y coordinate.

        Args:
            y (float): The Y coordinate.
        """
        self._y = y

    def get_position(self) -> T:
        """Get the position as (x, y) tuple.

        Returns:
            tuple[float, float]: The position as (x, y) tuple.
        """
        return self._x, self._y  # type: ignore[return-value]

    def set_position(self, position: T) -> None:
        """Set the position as (x, y) tuple.

        Args:
            position (tuple[float, float]): The position as (x, y) tuple.
        """
        self._x, self._y = position


class Area2D(
    IArea2D,
    Coord2D,
    Generic[T],
):
    """Protocol for 2D areas."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
    ) -> None:
        Coord2D.__init__(
            self,
            x=x,
            y=y,
        )
        self._width = width
        self._height = height

    def get_width(self) -> float:
        """Get the width of the area.

        Returns:
            float: The width of the area.
        """
        return self._width

    def set_width(self, width: float) -> None:
        """Set the width of the area.

        Args:
            width (float): The width of the area.
        """
        self._width = width

    def get_height(self) -> float:
        """Get the height of the area.

        Returns:
            float: The height of the area.
        """
        return self._height

    def set_height(self, height: float) -> None:
        """Set the height of the area.

        Args:
            height (float): The height of the area.
        """
        self._height = height

    def get_size(self) -> T:
        """Get the size as (width, height) tuple.

        Returns:
            tuple[float, float]: The size as (width, height) tuple.
        """
        return self._width, self._height  # type: ignore[return-value]

    def set_size(self, size: T) -> None:
        """Set the size as (width, height) tuple.

        Args:
            size (tuple[float, float]): The size as (width, height) tuple.
        """
        self._width, self._height = size

    def get_center(self) -> T:
        """Get the center coordinate as (x, y) tuple.

        Returns:
            tuple[float, float]: The center (x, y) coordinate.
        """
        return self.get_center_x(), self.get_center_y()  # type: ignore[return-value]

    def get_center_x(self) -> float:
        """Get the center X coordinate.

        Returns:
            float: The center X coordinate.
        """
        center_x = self.get_x() + self._width / 2
        return center_x

    def get_center_y(self) -> float:
        """Get the center Y coordinate.

        Returns:
            float: The center Y coordinate.
        """
        center_y = self.get_y() + self._height / 2
        return center_y


class Coord3D(
    Coord2D,
    ICoord3D,
):
    """Protocol for 3D coordinates."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ) -> None:
        Coord2D.__init__(
            self,
            x=x,
            y=y,
        )
        self._z = z

    def get_z(self) -> float:
        """Get the Z coordinate.

        Returns:
            float: The Z coordinate.
        """
        return self._z

    def set_z(self, z: float) -> None:
        """Set the Z coordinate.

        Args:
            z (float): The Z coordinate.
        """
        self._z = z

    def get_position(self) -> tuple[float, float, float]:
        """Get the position as (x, y, z) tuple.

        Returns:
            tuple[float, float, float]: The position as (x, y, z) tuple.
        """
        x, y = super().get_position()
        return x, y, self._z

    def set_position(self, position: tuple[float, float, float]) -> None:
        """Set the position as (x, y, z) tuple.

        Args:
            position (tuple[float, float, float]): The position as (x, y, z) tuple.
        """
        x, y, z = position
        super().set_position((x, y))
        self._z = z


class Area3D(
    Coord3D,
    Area2D,
    IArea3D,
):
    """Protocol for 3D areas."""

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        depth: float = 0.0,
    ) -> None:
        Coord3D.__init__(
            self,
            x=x,
            y=y,
            z=z,
        )
        Area2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        self._depth = depth

    def get_depth(self) -> float:
        """Get the depth of the area.

        Returns:
            float: The depth of the area.
        """
        return self._depth

    def set_depth(self, depth: float) -> None:
        """Set the depth of the area.

        Args:
            depth (float): The depth of the area.
        """
        self._depth = depth

    def get_size(self) -> tuple[float, float, float]:
        """Get the size as (width, height, depth) tuple.

        Returns:
            tuple[float, float, float]: The size as (width, height, depth) tuple.
        """
        return self._width, self._height, self._depth

    def set_size(self, size: tuple[float, float, float]) -> None:
        """Set the size as (width, height, depth) tuple.

        Args:
            size (tuple[float, float, float]): The size as (width, height, depth) tuple.
        """
        self._width, self._height, self._depth = size

    def get_center_z(self) -> float:
        """Get the center Z coordinate.

        Returns:
            float: The center Z coordinate.
        """
        center_z = self.get_z() + self._depth / 2
        return center_z

    def get_center(self) -> tuple[float, float, float]:
        """Get the center coordinate as (x, y, z) tuple.

        Returns:
            tuple[float, float, float]: The center (x, y, z) coordinate.
        """
        center_x, center_y = super().get_center()
        center_z = self.get_center_z()
        return center_x, center_y, center_z


__all__ = [
    "Coord2D",
    "Area2D",
    "Coord3D",
    "Area3D",
]
