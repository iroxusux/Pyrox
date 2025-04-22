"""base model
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING


from .abc import PartialModel
from .viewmodel import ViewModel


if TYPE_CHECKING:
    from .application import Application
    from .view import View


__all__ = (
    'Model',
)


class Model(PartialModel):
    """A model for use in an application.

    .. ------------------------------------------------------------

    .. package:: types.model

    .. ------------------------------------------------------------

    Arguments
    -----------

    app: Optional[:class:`Application`]
        Parent `Application` of this :class:`Model`. Defaults to `None`.

    view_model: Optional[:class:`ViewModel`]
        Child `ViewModel` of this :class:`Model`. Defaults to `None`.

    Attributes
    -----------
    app: Optional[:class:`Application`]
        Parent `Application` of this :class:`Model`.

    view_model: Optional[:class:`ViewModel`]
        Child `ViewModel` of this :class:`Model`.
    """

    def __init__(self,
                 app: Optional[Application] = None,
                 view_model: Optional[ViewModel] = None):
        super().__init__(application=app,
                         view_model=view_model)

    @property
    def application(self) -> Application:
        """Parent `Application` of this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        --------
            app: Optional[:class:`Application`]
        """
        return self._application

    @application.setter
    def application(self, value: Application) -> None:
        self._application = value

    @property
    def view_model(self) -> ViewModel:
        """Child `ViewModel` of this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        --------
            view_model: Optional[:class:`ViewModel`]
        """
        return self._view_model

    @classmethod
    def as_assembled(cls,
                     application: Application,
                     viewmodel: type[ViewModel],
                     view: type[View]):
        """Build this model and automatically link the relationship

        for the mvvm workflow

        .. ------------------------------------------------------------

        Arguments
        ----------
        viewmodel: :class:`ViewModel`
            :class:`ViewModel` to create this model with.

        view: :class:`View`
            :class:`View` to create the :class:`ViewModel` with.

        .. ------------------------------------------------------------

        Returns
        --------
        A :class:`Model` with an assmebled :class:`ViewModel` and :class:`View`.

        """

        # create the model, view model, and view
        mdl = cls(application, None)
        v = view(None, application.frame)
        vm = viewmodel(mdl, v)

        # set relationships
        mdl.set_view_model(vm)
        v.set_view_model(vm)

        return mdl

    def build(self):
        if self.view_model:
            self.view_model.build()
        super().build()

    def refresh(self):
        if self.view_model:
            self.view_model.refresh()
        super().refresh()

    def set_view_model(self,
                       view_model: ViewModel) -> None:
        """ Set a :class:`ViewModel` for this :class:`Model`

        .. ------------------------------------------------------------

        Arguments
        -----------

        view: :class:`ViewModel`
            View Model to set as this model's `ViewModel`.
        """
        self._view_model = view_model
