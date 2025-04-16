"""view-model abc
    """
from __future__ import annotations


from typing import TYPE_CHECKING


from .meta import SnowFlake


if TYPE_CHECKING:
    from .model import Model
    from .view import View


__all__ = (
    'ViewModel',
)


class ViewModel(SnowFlake):
    """A view-model for logical interchange of ui/backend in an application.

    .. ------------------------------------------------------------

    .. package:: types.abc.viewmodel

    .. ------------------------------------------------------------

    Attributes
    -----------
    model: :class:`Model`
        The parent :class:`Model` this :class:`ViewModel`.

    view: :class:`View`
        The child :class:`View` this :class:`ViewModel`.
    """
    model: Model
    view: View
