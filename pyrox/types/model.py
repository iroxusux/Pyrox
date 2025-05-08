"""base model
    """
from __future__ import annotations


import gc
from typing import Optional, Type


from .abc import (
    PartialModel,
    PartialApplication,
    PartialViewConfiguration,
)
from .viewmodel import ViewModel
from .view import View


__all__ = (
    'Model',
    'SupportsAssembly',
    'LaunchableModel',
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

    @property
    def application(self) -> PartialApplication:
        """Parent `Application` of this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        --------
            app: Optional[:class:`Application`]
        """
        return self._application

    @application.setter
    def application(self, value: PartialApplication) -> None:
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


class SupportsAssembly(Model):
    """A model for use in an application that can support classmethod `as_assembled`.

        This class exposes inherited view and view-model types from custom classes

        .. ------------------------------------------------------------

        .. package:: types.model

        .. ------------------------------------------------------------

        Attributes
        -----------
        view_class: :class:`Type`
            Class constructor for the `View` of this model.

        view_model_class: :class:`Type`
            Class constructor for the `ViewModel` of this model.
        """

    def get_view_class(self) -> Type:
        """Get class constructor for the `View` of this model.

        .. ------------------------------------------------------------

        Raises
        ----------
        NotImplimentedError:
            Inheriting class did not override this method

        .. ------------------------------------------------------------

        Returns
        ----------
            view_class: :class:`type`
        """
        raise NotImplementedError()

    def get_view_model_class(self) -> Type:
        """Get class constructor for the `ViewModel` of this model.

        .. ------------------------------------------------------------

        Raises
        ----------
        NotImplimentedError:
            Inheriting class did not override this method

        .. ------------------------------------------------------------

        Returns
        ----------
            view_model_class: :class:`type`
        """
        raise NotImplementedError()

    @classmethod
    def as_assembled(cls,
                     application: PartialApplication):
        """Build this model and automatically link the relationship

        for the mvvm workflow

        .. ------------------------------------------------------------

        Arguments
        ----------
        viewmodel: :class:`Type`
            :class:`ViewModel` to create this model with.

        view: :class:`Type`
            :class:`View` to create the :class:`ViewModel` with.

        .. ------------------------------------------------------------

        Returns
        --------
        A :class:`Model` with an assmebled :class:`ViewModel` and :class:`View`.

        """

        # create the model, view model, and view
        mdl = cls(application=application, view_model=None)
        v = cls.get_view_class(cls)(view_model=None, config=PartialViewConfiguration(parent=application.frame))
        vm = cls.get_view_model_class(cls)(model=mdl, view=v)

        # set relationships
        mdl.set_view_model(vm)
        v.set_view_model(vm)

        return mdl


class LaunchableModel(SupportsAssembly):
    """A model for use in an application that can launch a sub-application.

    This sub application exists as a top-level window with a separate 'alive' status.

    This separate 'alive' status allows for deeper integration and control of the call stack.

    .. ------------------------------------------------------------

    .. package:: types.model

    .. ------------------------------------------------------------

    Arguments
    -----------

    app: Optional[:class:`Application`]
        Parent `Application` of this :class:`Model`. Defaults to `None`.

    view_model: Optional[:class:`ViewModel`]
        Child `ViewModel` of this :class:`Model`. Defaults to `None`.

    .. ------------------------------------------------------------

    Attributes
    -----------
    sub_app: :class:`Application`
        Sub application launched by this model.

    sub_app_name: :class:`str`
        Name for the sub-application this model will launch with.

    sub_app_size: :class:`str`
        Size for the sub-application window this model will launch with.
    """

    __slots__ = ('_sub_app',)

    def __init__(self,
                 application: Optional[PartialApplication],
                 view_model: type[ViewModel],
                 view: type[View],
                 view_config: PartialViewConfiguration):

        self._view_model_type: type[ViewModel] = view_model
        self._view_type: type[View] = view
        self._view_config: PartialViewConfiguration = view_config

        super().__init__(application=application)

    @property
    def loop_time(self) -> int:
        """millisecond loop time for this looping model
        """
        return 100  # default 1/10th of a second

    def launch(self):
        """Launch Sub-Application Window.
        """
        if self.view_model:
            if self.view_model.view.parent.winfo_exists():
                self.view_model.view.parent.focus()  # bring it into focus
                return  # this app is already running!
            else:
                self.view_model.view.close()

        del self._view_model
        gc.collect()

        self._view_model = self._view_model_type(self, self._view_type, self._view_config)

        # build
        self.build()

        # start
        self.start()

        # loop
        self.loop()

    def loop(self):
        """Manage the loop for the running of this launchable model
        """
        if self.running:
            self.run()

        self.view_model.view.parent.after(self.loop_time, self.loop)
