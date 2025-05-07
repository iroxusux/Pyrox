"""view-model abc
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING, Union


from .meta import Buildable, PartialView, PartialViewConfiguration


if TYPE_CHECKING:
    from .model import PartialModel


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
                 view: Optional[Union[PartialView, type[PartialView]]]):
        super().__init__()
        self._model = model

        try:
            cfg = PartialViewConfiguration(parent=model.application.frame)
        except AttributeError:
            cfg = PartialViewConfiguration()

        # either construct from a constructor, or set the already constructed value
        # if a bogus value was passed, raise a value error.
        self._view: Optional[PartialView] = None
        if isinstance(view, type):
            self._view = view(view_model=self,
                              config=cfg)
        elif isinstance(view, PartialView):
            self._view = view
        elif view is not None:
            raise ValueError('Could not discern type of %s!' % view)

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
    def view(self) -> PartialView:
        """The child :class:`View` this :class:`PartialViewModel`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view: :class:`View`
        """
        return self._view
