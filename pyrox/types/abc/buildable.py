"""module for classes that support a 'buildable' state (models, views, etc.)
    """
from __future__ import annotations


__all__ = (
    'Buildable',
)


class Buildable:
    """Denotes object is 'buildable' and supports `build` and `refresh` methods.

    Also, supports `built` property.

    .. ------------------------------------------------------------

    .. package:: types.abc.buildable

    .. ------------------------------------------------------------

    Attributes
    -----------
    built: :type:`bool`
        The object has previously been built.
    """

    def __init__(self):
        self._built: bool = False

    @property
    def built(self) -> bool:
        """The object has previously been built.

        Returns
        -----------
            built: :type:`bool`
        """

    def build(self):
        """Build this object
        """
        self._built = True

    def refresh(self):
        """Refresh this object.
        """
