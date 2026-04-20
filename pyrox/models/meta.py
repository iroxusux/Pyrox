"""Meta module for Pyrox framework base classes."""
from pathlib import Path
import uuid


__all__ = (
    'DEF_ICON',
    'PyroxObject',
    'SnowFlake',
)

DEF_ICON = Path(__file__).resolve().parents[2] / "ui" / "icons" / "_def.ico"


class SnowFlake:
    """A meta class for all classes to derive from to obtain unique IDs.

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


class PyroxObject(SnowFlake):
    """A base class for all Pyrox objects."""
    __slots__ = ()

    def __init__(
        self,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return self.__class__.__name__
