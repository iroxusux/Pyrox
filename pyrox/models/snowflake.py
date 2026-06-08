"""Snowflake class for unique identifiers.
"""
import uuid


__all__ = (
    'SnowFlake',
)


class SnowFlake:
    """A base class for all classes to derive from to obtain unique IDs.

    Attributes:
        id: Unique identifier for this object.
    """
    __slots__ = ('_id',)

    def __eq__(self, other) -> bool:
        if issubclass(type(other), SnowFlake):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self._id)

    def __init__(
        self,
        **_
    ) -> None:
        self._id = uuid.uuid4()

    def __str__(self) -> str:
        return str(self.id)

    @property
    def id(self) -> int:
        """Unique identifier for this object.

        Returns:
            int: The unique ID.
        """
        return self._id.int
