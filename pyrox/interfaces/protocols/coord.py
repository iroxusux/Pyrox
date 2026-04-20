"""Coordinate protocol definitions.
"""


class ICoord2D:
    """Protocol for 2D coordinates."""
    _x: float
    _y: float

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
    def position(self) -> tuple[float, float]:
        """Get the position as (x, y) tuple.

        Returns:
            tuple[float, float]: The (x, y) position.
        """
        return self.get_position()

    def get_position(self) -> tuple[float, float]:
        """Get the position as (x, y) tuple.

        Returns:
            tuple[float, float]: The (x, y) position.
        """
        return self.get_x(), self.get_y()

    def set_position(self, position: tuple[float, float]) -> None:
        """Set the position as (x, y) tuple.

        Args:
            position (tuple[float, float]): The (x, y) position.
        """
        self.set_x(position[0])
        self.set_y(position[1])


class IArea2D(ICoord2D):
    """Protocol for 2D area defined by width and height."""
    _width: float
    _height: float

    def get_width(self) -> float:
        """Get the width.

        Returns:
            float: The width.
        """
        return self._width

    def set_width(self, width: float) -> None:
        """Set the width.

        Args:
            width (float): The width.
        """
        self._width = width

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

    def get_height(self) -> float:
        """Get the height.

        Returns:
            float: The height.
        """
        return self._height

    def set_height(self, height: float) -> None:
        """Set the height.

        Args:
            height (float): The height.
        """
        self._height = height

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

    def get_size(self) -> tuple[float, float]:
        """Get the size as (width, height) tuple.

        Returns:
            tuple[float, float]: The (width, height) size.
        """
        return self.get_width(), self.get_height()

    def set_size(self, size: tuple[float, float]) -> None:
        """Set the size as (width, height) tuple.

        Args:
            size (tuple[float, float]): The (width, height) size.
        """
        self.set_width(size[0])
        self.set_height(size[1])

    @property
    def size(self) -> tuple[float, float]:
        """Get the size as (width, height) tuple.

        Returns:
            tuple[float, float]: The (width, height) size.
        """
        return self.get_size()

    @size.setter
    def size(self, value: tuple[float, float]) -> None:
        """Set the size as (width, height) tuple.

        Args:
            value (tuple[float, float]): The (width, height) size.
        """
        self.set_size(value)

    def get_center_x(self) -> float:
        """Get the center X coordinate.

        Returns:
            float: The center X coordinate.
        """
        return self.get_x() + self.get_width() / 2

    def get_center_y(self) -> float:
        """Get the center Y coordinate.

        Returns:
            float: The center Y coordinate.
        """
        return self.get_y() + self.get_height() / 2

    def get_center(self) -> tuple[float, float]:
        """Get the center coordinate as (x, y) tuple.

        Returns:
            tuple[float, float]: The center (x, y) coordinate.
        """
        return self.get_center_x(), self.get_center_y()

    @property
    def center(self) -> tuple[float, float]:
        """Get the center coordinate as (x, y) tuple.

        Returns:
            tuple[float, float]: The center (x, y) coordinate.
        """
        return self.get_center()

    def get_bounds(self) -> tuple[float, float, float, float]:
        """Get the bounding box as (left, top, right, bottom).

        Returns:
            tuple[float, float, float, float]: The bounding box.
        """
        left = self.get_x()
        top = self.get_y()
        right = left + self.get_width()
        bottom = top + self.get_height()
        return (left, top, right, bottom)


__all__ = [
    'ICoord2D',
    'IArea2D',
]
