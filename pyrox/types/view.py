""" This class represents a view (Frame or LabelFrame).
    """
from __future__ import annotations


from tkinter import Tk, Toplevel, Frame, LabelFrame
from typing import Optional, TYPE_CHECKING, Union


from .abc.meta import PartialView
from .loggable import Loggable


if TYPE_CHECKING:
    from .viewmodel import ViewModel


__all__ = (
    'View',
)


class View(PartialView, Loggable):
    """A view for use in an application.

    .. ------------------------------------------------------------

    .. package:: types.view

    .. ------------------------------------------------------------

    Attributes
    -----------
    view_model: Optional[:class:`ViewModel`]
        The parent :class:`ViewModel` this :class:`View`. Defaults to `None`.

    """

    def __init__(self,
                 view_model: Optional[ViewModel] = None,
                 parent: Optional[Union[Tk, Toplevel, Frame, LabelFrame]] = None):
        PartialView.__init__(self,
                             view_type=3,
                             config={'parent': parent})
        Loggable.__init__(self)
        self._view_model: Optional[ViewModel] = view_model

    @property
    def view_model(self) -> Optional[ViewModel]:
        """The parent :class:`ViewModel` this :class:`View`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view_model: :class:`ViewModel` | None
        """
        return self._view_model

    def set_view_model(self,
                       view_model: ViewModel) -> None:
        """ Set a :class:`ViewModel` for this :class:`View`

        .. ------------------------------------------------------------

        Arguments
        -----------

        view_model: :class:`ViewModel`
            ViewModel to set as this view's `ViewModel`.
        """
        self._view_model = view_model
