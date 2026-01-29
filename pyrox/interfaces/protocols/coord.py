"""Coordinate protocol definitions.
"""
from typing import (
    Generic,
    runtime_checkable,
    Protocol,
    TypeVar
)

T = TypeVar("T", bound=tuple[float, ...])
BT = TypeVar("BT", bound=tuple[float, float, float, float], covariant=True)


@runtime_checkable
class ICoord2D(
    Generic[T],
    Protocol
):
    """Protocol for 2D coordinates."""

    @property
    def x(self) -> float:
        """Get the X coordinate.

        Returns:
            float: The X coordinate.
        """
        return self.get_x()

    @x.setter
    def x(self, value: float) -> None:
        """Set the X coordinate.

        Args:
            value (float): The X coordinate.
        """
        self.set_x(value)

    @property
    def y(self) -> float:
        """Get the Y coordinate.

        Returns:
            float: The Y coordinate.
        """
        return self.get_y()

    @y.setter
    def y(self, value: float) -> None:
        """Set the Y coordinate.

        Args:
            value (float): The Y coordinate.
        """
        self.set_y(value)

    @property
    def position(self) -> T:
        """Get the position as (x, y) tuple.

        Returns:
            tuple[float, float]: The (x, y) position.
        """
        return self.get_position()

    def get_x(self) -> float:
        """Get the X coordinate.

        Returns:
            float: The X coordinate.
        """
        ...

    def set_x(self, x: float) -> None:
        """Set the X coordinate.

        Args:
            x (float): The X coordinate.
        """
        ...

    def get_y(self) -> float:
        """Get the Y coordinate.

        Returns:
            float: The Y coordinate.
        """
        ...

    def set_y(self, y: float) -> None:
        """Set the Y coordinate.

        Args:
            y (float): The Y coordinate.
        """
        ...

    def get_position(self) -> T:
        """Get the position as (x, y) tuple.

        Returns:
            tuple[float, float]: The (x, y) position.
        """
        ...

    def set_position(self, position: T) -> None:
        """Set the position as (x, y) tuple.

        Args:
            position (tuple[float, float]): The (x, y) position.
        """
        ...


@runtime_checkable
class IArea2D(
    Generic[T, BT],
    ICoord2D[T],
    Protocol
):
    """Protocol for 2D area defined by width and height."""

    @property
    def width(self) -> float:
        """Get the width.

        Returns:
            float: The width.
        """
        return self.get_width()

    @width.setter
    def width(self, value: float) -> None:
        """Set the width.

        Args:
            value (float): The width.
        """
        self.set_width(value)

    @property
    def height(self) -> float:
        """Get the height.

        Returns:
            float: The height.
        """
        return self.get_height()

    @height.setter
    def height(self, value: float) -> None:
        """Set the height.

        Args:
            value (float): The height.
        """
        self.set_height(value)

    @property
    def size(self) -> T:
        """Get the size as (width, height) tuple.

        Returns:
            tuple[float, float]: The (width, height) size.
        """
        return self.get_size()

    @property
    def center(self) -> T:
        """Get the center coordinate as (x, y) tuple.

        Returns:
            tuple[float, float]: The center (x, y) coordinate.
        """
        return self.get_center()

    def get_width(self) -> float:
        """Get the width.

        Returns:
            float: The width.
        """
        ...

    def set_width(self, width: float) -> None:
        """Set the width.

        Args:
            width (float): The width.
        """
        ...

    def get_height(self) -> float:
        """Get the height.

        Returns:
            float: The height.
        """
        ...

    def set_height(self, height: float) -> None:
        """Set the height.

        Args:
            height (float): The height.
        """
        ...

    def get_size(self) -> T:
        """Get the size as (width, height) tuple.

        Returns:
            tuple[float, float]: The (width, height) size.
        """
        ...

    def set_size(self, size: T) -> None:
        """Set the size as (width, height) tuple.

        Args:
            size (tuple[float, float]): The (width, height) size.
        """
        ...

    def get_center_x(self) -> float:
        """Get the center X coordinate.

        Returns:
            float: The center X coordinate.
        """
        ...

    def get_center_y(self) -> float:
        """Get the center Y coordinate.

        Returns:
            float: The center Y coordinate.
        """
        ...

    def get_center(self) -> T:
        """Get the center coordinate as (x, y) tuple.

        Returns:
            tuple[float, float]: The center (x, y) coordinate.
        """
        ...

    def get_bounds(self) -> BT:
        """Get the bounding box as (left, top, right, bottom).

        Returns:
            tuple[float, float, float, float]: The bounding box.
        """
        ...


@runtime_checkable
class ICoord3D(
    ICoord2D[tuple],
    Protocol,
):
    """Protocol for 3D coordinates."""

    @property
    def z(self) -> float:
        """Get the Z coordinate.

        Returns:
            float: The Z coordinate.
        """
        return self.get_z()

    @z.setter
    def z(self, value: float) -> None:
        """Set the Z coordinate.

        Args:
            value (float): The Z coordinate.
        """
        self.set_z(value)

    def get_z(self) -> float:
        """Get the Z coordinate.

        Returns:
            float: The Z coordinate.
        """
        ...

    def set_z(self, z: float) -> None:
        """Set the Z coordinate.

        Args:
            z (float): The Z coordinate.
        """
        ...

    def get_position(self) -> tuple[float, float, float]:
        """Get the position as (x, y, z) tuple.

        Returns:
            tuple[float, float, float]: The (x, y, z) position.
        """
        ...

    def set_position(self, position: tuple[float, float, float]) -> None:
        """Set the position as (x, y, z) tuple.

        Args:
            position (tuple[float, float, float]): The (x, y, z) position.
        """
        ...


@runtime_checkable
class IArea3D(
    IArea2D[tuple, tuple],
    ICoord3D,
    Protocol,
):
    """Protocol for 3D area defined by width, height, and depth."""

    @property
    def depth(self) -> float:
        """Get the depth.

        Returns:
            float: The depth.
        """
        return self.get_depth()

    def get_depth(self) -> float:
        """Get the depth.

        Returns:
            float: The depth.
        """
        ...

    def set_depth(self, depth: float) -> None:
        """Set the depth.

        Args:
            depth (float): The depth.
        """
        ...

    def get_size(self) -> tuple[float, float, float]:
        """Get the size as (width, height, depth) tuple.

        Returns:
            tuple[float, float, float]: The (width, height, depth) size.
        """
        ...

    def set_size(self, size: tuple[float, float, float]) -> None:
        """Set the size as (width, height, depth) tuple.

        Args:
            size (tuple[float, float, float]): The (width, height, depth) size.
        """
        ...

    def get_center_z(self) -> float:
        """Get the center Z coordinate.

        Returns:
            float: The center Z coordinate.
        """
        ...

    def get_center(self) -> tuple[float, float, float]:
        """Get the center coordinate as (x, y, z) tuple.

        Returns:
            tuple[float, float, float]: The center (x, y, z) coordinate.
        """
        ...

    def get_bounds(self) -> tuple[float, float, float, float, float, float]:
        """Get the bounding box as (left, top, front, right, bottom, back).

        Returns:
            tuple[float, float, float, float, float, float]: The bounding box.
        """
        ...


__all__ = [
    'ICoord2D',
    'IArea2D',
    'ICoord3D',
    'IArea3D',
]
