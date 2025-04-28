"""base model
    """
from __future__ import annotations


from typing import Optional, Type


from .abc import PartialModel, PartialApplication, PartialApplicationConfiguration
from .viewmodel import ViewModel


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

    def __init__(self,
                 app: Optional[PartialApplication] = None,
                 view_model: Optional[ViewModel] = None):
        super().__init__(application=app,
                         view_model=view_model)

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
        mdl = cls(application, None)
        v = cls.get_view_class(cls)(None, application.frame)
        vm = cls.get_view_model_class(cls)(mdl, v)

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
                 app: Optional[PartialApplication] = None,
                 view_model: Optional[ViewModel] = None):
        super().__init__(app=app,
                         view_model=view_model)
        self._sub_app: PartialApplication = None

    @property
    def loop_time(self) -> int:
        """millisecond loop time for this looping model
        """
        return 100  # default 1/10th of a second

    @property
    def sub_app(self) -> PartialApplication:
        """The sub-application of this `LaunchableModel`.

        .. ------------------------------------------------------------

        Returns
        ----------
        sub_app: :class:`Application`
        """
        return self._sub_app

    @property
    def sub_app_name(self) -> str:
        """Name for the sub-application this model will launch with.

        .. ------------------------------------------------------------

        Raises
        ----------
        NotImplimentedError:
            Inheriting class did not override this method

        .. ------------------------------------------------------------

        Returns
        ----------
            sub_app_name: :class:`str`
        """
        raise NotImplementedError()

    @property
    def sub_app_size(self) -> str:
        """Size for the sub-application window this model will launch with.

        (e.g. '400x400')

        .. ------------------------------------------------------------

        Raises
        ----------
        NotImplimentedError:
            Inheriting class did not override this method

        .. ------------------------------------------------------------

        Returns
        ----------
            sub_app_size: :class:`str`
        """
        raise NotImplementedError()

    def get_application_class(self) -> Type:
        """Get class constructor for the `Application` of this model.

        .. ------------------------------------------------------------

        Raises
        ----------
        NotImplimentedError:
            Inheriting class did not override this method

        .. ------------------------------------------------------------

        Returns
        ----------
            application_class: :class:`Application`
        """
        raise NotImplementedError()

    def launch(self):
        """Launch Sub-Application Window.
        """
        if self._sub_app:
            if self._sub_app.parent.winfo_exists():
                self._sub_app.parent.focus()  # at least bring it into focus
                return  # this app is already running!

        # create the sub-application configuration
        cfg: PartialApplicationConfiguration = PartialApplicationConfiguration.toplevel(self.sub_app_name)
        cfg.view_config.win_size = self.sub_app_size

        # create the objects (sub-app, viewmodel, view)
        self._sub_app = self.get_application_class()(None, cfg)
        view = self.get_view_class()(None, self._sub_app.frame)
        self._view_model = self.get_view_model_class()(self, view)

        # build
        self.build()

        # start
        self._sub_app.start()
        self.start()

        # send to loop
        self.loop()

    def loop(self):
        """Manage the loop for the running of this launchable model
        """
        if self.running:
            self.run()

        self.application.parent.after(self.loop_time, self.loop)
