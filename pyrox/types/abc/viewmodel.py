"""view-model abc
    """
from __future__ import annotations


from typing import TYPE_CHECKING


from .meta import Buildable


if TYPE_CHECKING:
    from .model import PartialModel
    from .. import View


__all__ = (
    'PartialViewModel',
)


class PartialViewModel(Buildable):
    """A partial view-model for logical interchange of ui/backend in an application.

    .. ------------------------------------------------------------

    .. package:: types.abc.viewmodel

    .. ------------------------------------------------------------

    Attributes
    -----------
    model: :class:`PartialModel`
        The parent :class:`Model` this :class:`PartialViewModel`.

    view: :class:`View`
        The child :class:`View` this :class:`PartialViewModel`.
    """

    __slots__ = ('_model', '_view')

    def __init__(self,
                 model: PartialModel,
                 view: View):
        super().__init__()
        self._model = model
        self._view = view

    @property
    def model(self) -> PartialModel:
        """The parent :class:`Model` this :class:`PartialViewModel`.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`PartialModel`
        """
        return self._model

    @property
    def view(self) -> View:
        """The child :class:`View` this :class:`PartialViewModel`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view: :class:`View`
        """
        return self._view
