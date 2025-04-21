"""base model
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING


from .buildable import Buildable
from .meta import SnowFlake


if TYPE_CHECKING:
    from .application import PartialApplication
    from .viewmodel import PartialViewModel


__all__ = (
    'PartialModel',
)


class PartialModel(SnowFlake, Buildable):
    """A partial model for use in an application.

    .. ------------------------------------------------------------

    .. package:: types.abc.model

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: Optional[:class:`PartialApplication`]
        The parent application of this :class:`Model`, if any.

    view_model: Optional[:class:`PartialViewModel`]
        The :class:`PartialViewModel` this :class:`Model` is associated with, if any.
    """

    def __init__(self,
                 application: Optional[PartialApplication] = None,
                 view_model: Optional[PartialViewModel] = None):
        SnowFlake.__init__(self)
        Buildable.__init__(self)
        self._application: Optional[PartialApplication] = application
        self._view_model: Optional[PartialViewModel] = view_model

    @property
    def application(self) -> PartialApplication:
        """The parent application of this :class:`Model`, if any.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Optional[:class:`PartialApplication`]
        """
        return self._application

    @property
    def view_model(self) -> PartialViewModel:
        """The :class:`PartialViewModel` this :class:`Model` is associated with, if any.

        .. ------------------------------------------------------------

        Returns
        -----------
            view_model: Optional[:class:`PartialViewModel`]
        """
        return self._view_model
