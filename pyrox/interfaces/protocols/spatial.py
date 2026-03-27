"""Spacial object protocols that extend coordinate protocols.
"""
from pyrox.interfaces import CardinalDirection
from pyrox.interfaces.protocols.coord import IArea2D


class IDirectional2D(IArea2D):
    """Protocol for 2D directional objects. (Cardinal directions only)"""
    _direction: CardinalDirection | None

    # ------------------------------------------------------------------
    # Resize methods
    # ------------------------------------------------------------------

    def rotate_area(self, prev_direction: CardinalDirection) -> None:
        """Rotate the area dimensions (swap width and height).
        Additionally, move components to maintain their relative positions within the bounding box.
        """
        if CardinalDirection.is_perpendicular(self.direction, prev_direction):
            # Swap width and height
            current_width = self.get_width()
            current_height = self.get_height()
            self.set_width(current_height)
            self.set_height(current_width)

    # ------------------------------------------------------------------
    # Direction and rotation
    # ------------------------------------------------------------------

    def get_direction(self) -> CardinalDirection:
        """Get the direction of this object in degrees."""
        if not self._direction:
            self._direction = CardinalDirection.NORTH  # Default to NORTH if not set
        return self._direction  # type: ignore[return-value]

    def set_direction(
        self,
        direction: CardinalDirection | str | int | None,
    ) -> None:
        """Set the direction of this object."""
        if direction:
            direction = CardinalDirection.try_parse(direction)
            assert direction is not None, f"Invalid direction: {direction}"
            if self.direction == direction:
                return  # No change, skip

            _last_dir = self.direction  # Store last direction for area rotation logic
            self._direction = direction
            self.rotate_area(_last_dir)  # Rotate area dimensions when direction changes
        else:
            self._direction = None

    @property
    def direction(self) -> CardinalDirection:
        """Get the rotation of this object in degrees."""
        return self.get_direction()

    @direction.setter
    def direction(self, direction: CardinalDirection) -> None:
        """Set the rotation of this object in degrees."""
        self.set_direction(direction)

    # ------------------------------------------------------------------
    # Rotation convenience methods
    # ------------------------------------------------------------------

    def rotate_clockwise(self) -> None:
        """Rotate the object 90 degrees clockwise."""
        if self.direction:
            self.set_direction(CardinalDirection.next_clockwise(self.direction))

    def rotate_counterclockwise(self) -> None:
        """Rotate the object 90 degrees counterclockwise."""
        if self.direction:
            self.set_direction(CardinalDirection.next_counterclockwise(self.direction))

    def rotate_180(self) -> None:
        """Rotate the object 180 degrees."""
        if self.direction:
            self.set_direction(CardinalDirection(((self.direction.value + 1) % 4) + 1))

    def rotate_to(self, direction: CardinalDirection | str | int) -> None:
        """Rotate the object to a specific cardinal direction."""
        self.set_direction(CardinalDirection.try_parse(direction))


class IRotatable:
    """Protocol for rotatable spatial objects."""
    _pitch: float
    _yaw: float
    _roll: float

    def get_pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        return self._pitch

    def set_pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        self._pitch = pitch

    @property
    def pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        return self.get_pitch()

    @pitch.setter
    def pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        self.set_pitch(pitch)

    def get_yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        return self._yaw

    def set_yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        self._yaw = yaw

    @property
    def yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        return self.get_yaw()

    @yaw.setter
    def yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        self.set_yaw(yaw)

    def get_roll(self) -> float:
        """Get the roll rotation of the scene object."""
        return self._roll

    def set_roll(self, roll: float) -> None:
        """Set the roll rotation of the scene object."""
        self._roll = roll

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
        return self.get_pitch(), self.get_yaw(), self.get_roll()

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
        self.set_pitch(pitch)
        self.set_yaw(yaw)
        self.set_roll(roll)


class IZoomable:
    """Protocol for zoomable spatial objects."""
    _zoom: float

    def get_zoom(self) -> float:
        """Get the zoom level of the spatial object."""
        return self._zoom

    def set_zoom(self, zoom: float) -> None:
        """Set the zoom level of the spatial object."""
        self._zoom = zoom

    @property
    def zoom(self) -> float:
        """Get the zoom level of the spatial object."""
        return self.get_zoom()

    @zoom.setter
    def zoom(self, zoom: float) -> None:
        """Set the zoom level of the spatial object."""
        self.set_zoom(zoom)


class ISpatial2D(
    IDirectional2D,
    IRotatable,
):
    """Protocol for 2D spatial objects."""


__all__ = [
    "ISpatial2D",
    "IRotatable",
    "IDirectional2D",
    "IZoomable",
]
