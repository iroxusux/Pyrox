
class TrackedLine:
    """Tracked line for the CLI / Terminal Interface.
    Designed for alternate mode use.
    """

    def __repr__(self) -> str:
        return self.value

    def __init__(
        self,
        line_no: int,
        value: str
    ) -> None:
        if line_no < 1:
            raise ValueError(f'Line number must be positive! Got {line_no}')
        self._line_no = line_no
        self._value = value
        self._dirty = True

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def line_no(self) -> int:
        return self._line_no

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        if self._value != value:
            self._value = value
            self._dirty = True

    def clean(self) -> None:
        """Unmark this line from being dirty."""
        self._dirty = False

    def mark_dirty(self) -> None:
        """Mark this line as dirty / needs re-rendering."""
        self._dirty = True
