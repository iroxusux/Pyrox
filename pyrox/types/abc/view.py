""" This class represents a view (Frame or LabelFrame).
    """
from __future__ import annotations


from typing import TYPE_CHECKING


from .meta import PartialView


if TYPE_CHECKING:
    from .viewmodel import ViewModel


__all__ = (
    'View',
)


class View(PartialView):
    """A view for use in an application.

    .. ------------------------------------------------------------

    .. package:: types.abc.view

    .. ------------------------------------------------------------

    Attributes
    -----------
    view_model: :class:`ViewModel`
        The parent :class:`ViewModel` this :class:`View`.
    """
    view_model: ViewModel
