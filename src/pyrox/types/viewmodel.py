"""view-model abc
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING


from .abc import PartialViewModel


if TYPE_CHECKING:
    from .model import Model
    from .view import View


__all__ = (
    'ViewModel',
)


class ViewModel(PartialViewModel):
    """A view-model for logical interchange of ui/backend in an application.

    .. ------------------------------------------------------------

    .. package:: types.viewmodel

    .. ------------------------------------------------------------

    Attributes
    -----------
    model: :class:`Model`
        The parent :class:`Model` this :class:`ViewModel`. Defaults to `None`.

    view: :class:`View`
        The child :class:`View` this :class:`ViewModel`. Defaults to `None`.
    """

    def __init__(self,
                 model: Optional[Model] = None,
                 view: Optional[View] = None):
        super().__init__(model=model,
                         view=view)

    @property
    def model(self) -> Optional[Model]:
        """The parent :class:`Model` this :class:`ViewModel`.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`Model` | None
        """
        return self._model

    @property
    def view(self) -> Optional[View]:
        """The child :class:`View` this :class:`ViewModel`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view: :class:`View` | None
        """
        return self._view

    def build(self):
        if self.view:
            self.view.build()
        super().build()

    def refresh(self):
        if self.view:
            self.view.refresh()
        super().refresh()

    def set_view(self,
                 view: View) -> None:
        """ Set a :class:`View` for this :class:`ViewModel`

        .. ------------------------------------------------------------

        Arguments
        -----------

        view: :class:`View`
            View to set as this view model's `View`.
        """
        self._view = view
