"""base model
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING, Union


from .meta import Runnable, PartialViewConfiguration
from .viewmodel import PartialViewModel


if TYPE_CHECKING:
    from .application import PartialApplication, View


__all__ = (
    'PartialModel',
)


class PartialModel(Runnable):
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

    __slots__ = ('_application', '_view_model')

    def __init__(self,
                 application: Optional[PartialApplication] = None,
                 view_model: Optional[Union[PartialViewModel, type[PartialViewModel]]] = None,
                 view: Optional[type[View]] = None,
                 view_config: Optional[PartialViewConfiguration] = None):
        super().__init__()

        self._application: Optional[PartialApplication] = application

        # either construct from a constructor, or set the already constructed value
        # if a bogus value was passed, raise a value error.
        self._view_model: Optional[PartialViewModel] = None
        if isinstance(view_model, type):
            self._view_model = view_model(model=self, view=view)
        elif isinstance(view_model, PartialViewModel):
            self._view_model = view_model
        elif view_model is not None:
            raise ValueError('Could not discern type of %s!' % view_model)

    def __str__(self):
        return self.__class__.__name__

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

    @view_model.deleter
    def view_model(self):
        if self._view_model:
            if self._view_model.view:
                del self._view_model.view

        self._view_model = None

    def set_application(self,
                        application: PartialApplication) -> bool:
        """Set the :class:`Application` for this :class:`Model`

        Returns
        ----------
            :class:`bool`: Status of success
        """
        if self.application:
            return False

        self._application = application
        return True
