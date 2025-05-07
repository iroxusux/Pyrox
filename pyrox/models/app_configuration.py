"""Main emulation model
    """
from __future__ import annotations


from tkinter import Tk, Toplevel, Frame, LabelFrame
from typing import Optional, TYPE_CHECKING, Union


from pyrox import Model, View, ViewModel


if TYPE_CHECKING:
    from ..app import EmulationApplication


class AppConfigurationView(View):
    """Connection View

    """

    def __init__(self,
                 view_model: Optional['AppConfigurationViewModel'] = None,
                 parent: Optional[Union[Tk, Toplevel, Frame, LabelFrame]] = None):
        super().__init__(view_model=view_model,
                         parent=parent)


class AppConfigurationViewModel(ViewModel):
    """Connection View Model

    """

    def __init__(self, model: Optional['AppConfigurationModel'] = None,
                 view: Optional[AppConfigurationView] = None):
        super().__init__(model, view)


class AppConfigurationModel(Model):
    """Ip Connection Model for PLC testing.

    Uses `pylogix` module for connections.

    .. ------------------------------------------------------------

    Attributes
    -----------
    controller: :class:`Controller`
        Main controller for the emulation application.

    """

    def __init__(self,
                 app: Optional[EmulationApplication] = None,
                 view_model: Optional[AppConfigurationViewModel] = None):
        super().__init__(app=app,
                         view_model=view_model)

        self._ctrl_save_location: str = None

    def register_save_location(self,
                               save_location: str):
        self._ctrl_save_location = save_location
