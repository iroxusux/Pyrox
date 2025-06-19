"""Main emulation model
    """
from __future__ import annotations


import time
from tkinter import (
    BOTH,
    DISABLED,
    END,
    Frame,
    LabelFrame,
    LEFT,
    NORMAL,
    TOP,
)
from typing import Optional


from ..services.plc_services import l5x_dict_from_file, dict_to_xml_file
from ..models import Application, Model, ProgressBar, ViewModel, View, ViewConfiguration, ViewType
from ..models.plc import Controller, ConnectionParameters
from ..models.utkinter import DecoratedListboxFrame, TreeViewGridFrame


DEF_WIN_TITLE = 'Indicon LLC Emulation Manager Frame'


class EmulationView(View):
    """Emulation View class
    """

    def __init__(self,
                 view_model=None,
                 config=None):
        super().__init__(view_model, config)

        self._plccfgframe: Optional[Frame] = None

        self._tags_frame: Optional[DecoratedListboxFrame] = None
        self._datatypes_frame: Optional[DecoratedListboxFrame] = None
        self._aois_frame: Optional[DecoratedListboxFrame] = None
        self._mods_frame: Optional[DecoratedListboxFrame] = None
        self._programs_frame: Optional[DecoratedListboxFrame] = None
        self._routines_frame: Optional[DecoratedListboxFrame] = None
        self._progtag_frame: Optional[DecoratedListboxFrame] = None
        self._rungs_frame: Optional[DecoratedListboxFrame] = None

    @property
    def aois_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get AddOn Instructions Frame.
        """
        return self._aois_frame

    @property
    def tags_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get controller tags Frame.
        """
        return self._tags_frame

    @property
    def datatypes_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get datatypes Frame.
        """
        return self._datatypes_frame

    @property
    def l5x_frame(self) -> Frame | LabelFrame:
        """
        Get L5X Frame.
        """
        return self._l5xframe

    @property
    def mods_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get modules Frame.
        """
        return self._mods_frame

    @property
    def programs_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get programs Frame.
        """
        return self._programs_frame

    @property
    def progtag_frame(self) -> Optional[DecoratedListboxFrame]:
        """Get program tags Frame.
        """
        return self._progtag_frame

    @property
    def routines_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get routines Frame.
        """
        return self._routines_frame

    @property
    def rungs_frame(self) -> Optional[DecoratedListboxFrame]:
        """ Get rungs Frame.
        """
        return self._rungs_frame

    def _build_l5x_frame(self) -> None:

        self._l5xframe = LabelFrame(self.parent, text='L5X')
        self._l5xframe.pack(fill=BOTH, side=TOP)

        assets_frame = Frame(self._l5xframe)
        assets_frame.pack(fill=BOTH, side=LEFT, expand=True)

        progs_frame = Frame(self._l5xframe)
        progs_frame.pack(fill=BOTH, side=LEFT, expand=True)

        self._tags_frame = DecoratedListboxFrame(assets_frame, text='Tags')
        self._tags_frame.pack(side=TOP, fill=BOTH)

        self._datatypes_frame = DecoratedListboxFrame(assets_frame, text='Datatypes')
        self._datatypes_frame.pack(side=TOP, fill=BOTH)

        self._aois_frame = DecoratedListboxFrame(assets_frame, text='AddOn Instructions')
        self._aois_frame.pack(side=TOP, fill=BOTH)

        self._mods_frame = DecoratedListboxFrame(assets_frame, text='Modules')
        self._mods_frame.pack(side=TOP, fill=BOTH)

        self._programs_frame = DecoratedListboxFrame(progs_frame, text='Programs')
        self._programs_frame.pack(side=TOP, fill=BOTH)

        self._routines_frame = DecoratedListboxFrame(progs_frame, text='Routines')
        self._routines_frame.pack(side=TOP, fill=BOTH)

        self._progtag_frame = DecoratedListboxFrame(progs_frame, text='Program Tags')
        self._progtag_frame.pack(side=TOP, fill=BOTH)

        self._rungs_frame = DecoratedListboxFrame(progs_frame, text='Logic Rungs')
        self._rungs_frame.pack(side=TOP, fill=BOTH)

    def build(self):
        self.clear()
        self._build_l5x_frame()
        super().build()

    def refresh(self):
        self.tags_frame.listbox.delete(0, END)
        self._datatypes_frame.listbox.delete(0, END)
        self._aois_frame.listbox.delete(0, END)
        self._mods_frame.listbox.delete(0, END)
        self._programs_frame.listbox.delete(0, END)
        self._routines_frame.listbox.delete(0, END)
        self._progtag_frame.listbox.delete(0, END)
        self._rungs_frame.listbox.delete(0, END)


class EmulationViewModel(ViewModel):
    """emulation manager viewmodel
    """

    @property
    def controller(self) -> Optional[Controller]:
        return self.model.controller

    @property
    def model(self) -> EmulationModel:
        return self._model

    @property
    def view(self) -> EmulationView:
        return self._view

    @property
    def window_title(self) -> str:
        return DEF_WIN_TITLE if self.controller is None\
            else f'{self.controller.name} - {self.controller.major_revision}.{self.controller.minor_revision}'

    def _on_connect(self):
        if not self.model.application:
            self.logger.error('Cannot connect to PLC. Parent model is not associated with an application...')
            return

        try:
            on_connection = self.model.application.connection_model.on_connection
            if self._on_connection not in on_connection:
                on_connection.append(self._on_connection)
            self.model.application.connection_model.on_connection.append(self._on_connection)
            params = ConnectionParameters(self.view.ip_addr_entry.get(), self.view.slot_entry.get(), 500)
            self.model.application.connection_model.connect(params)
            self.view.connect_pb.configure(state=DISABLED)

        except ValueError as e:
            self.logger.error('Invalid Connection Parameters -> %s', e)

    def _on_connection(self,
                       connected: bool) -> None:
        if connected:
            self.view.connect_pb.configure(state=DISABLED)
            self.view.disconnect_pb.configure(state=NORMAL)

        else:
            self.view.connect_pb.configure(state=NORMAL)
            self.view.disconnect_pb.configure(state=DISABLED)

    def _on_disconnect(self):
        if not self.model.application:
            self.logger.error('Cannot disconnect from PLC. Parent model is not associated with an application...')
            return

        self.model.application.connection_model.disconnect()

    def log(self,
            message: str):
        """Post a message to this :class:`ViewModel`'s view's logger frame.

        Arguments
        ----------
        message: :type:`str`
            Message to be sent to this :class:`View`'s log frame.
        """
        if not self.model.application.running:
            return
        self.view.log(message)

    def refresh(self):
        controller = self.model.controller
        # setup a progress bar to show what's going on
        prog_bar = ProgressBar('Open L5X Controller',
                               'Decompiling Controller...')

        # clear the view to rebuild
        # then, setup to regen hooks
        prog_bar.update('Rebuilding view...', 50)
        self.view.refresh()

        prog_bar.update('Setting up view model...', 55)

        # rebuild and place data
        prog_bar.update('Setting window info...', 60)
        self.view.title = self.window_title

        prog_bar.update('Compiling controller tags...', 65)
        ctags = [x['@Name'] for x in controller.tags]
        self.view._tags_frame.listbox.fill(ctags)

        prog_bar.update('Compiling datatypes...', 70)
        dtypes = [x['@Name'] for x in controller.datatypes]
        self.view.datatypes_frame.listbox.fill(dtypes)

        prog_bar.update('Compiling add on instructions...', 75)
        aois = [x['@Name'] for x in controller.aois]
        self.view.aois_frame.listbox.fill(aois)

        prog_bar.update('Compiling modules...', 80)
        mods = [x['@Name'] for x in controller.modules]
        self.view.mods_frame.listbox.fill(mods)

        prog_bar.update('Compiling programs...', 85)
        progs = [x['@Name'] for x in controller.programs]
        self.view.programs_frame.listbox.fill(progs)

        prog_bar.update('Compiling...', 100)
        time.sleep(0.5)  # sneaky to make people think stuff is happening kek
        prog_bar.stop()
        del prog_bar


class EmulationModel(Model):
    """Emulation :class:`Model`.

    .. ------------------------------------------------------------

    .. package:: emulation_preparation

    .. ------------------------------------------------------------

    Attributes
    -----------
    controller: Optional[:class:`Controller`]
        Allen Bradley L5X Controller Object associated with this :class:`Model`.

    """

    def __init__(self,
                 application: Application = None,
                 view_model: ViewModel = EmulationViewModel,
                 view: View = EmulationView,
                 view_config: ViewConfiguration = ViewConfiguration()):

        if not view_model:
            view_model = EmulationViewModel

        if not view:
            view = EmulationView

        view_config.title = 'Emulation Model'
        view_config.parent = application.view.frame

        super().__init__(application=application,
                         view_model=view_model,
                         view=view,
                         view_config=view_config)

        self._controller: Optional[Controller] = None

    @property
    def controller(self) -> Optional[Controller]:
        """Allen Bradley L5X Controller Object associated with this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller`]
        """
        return self._controller

    @controller.setter
    def controller(self,
                   value: Controller):
        if self.controller is not value:
            self._controller = value
            self.refresh()

    @property
    def view_model(self) -> EmulationViewModel:
        return self._view_model

    def build(self):
        super().build()
        if self.controller:    # after being built, if we've previously had a controller...
            super().refresh()  # set the refresh request to rebuild the page properly.

    def load_controller(self,
                        file_location: str) -> None:
        """Attempt to load a :class:`Controller` from a provided .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to open :class:`Controller` from.

        """
        ctrl_dict = xml_dict_from_file(file_location)
        if not ctrl_dict:
            self.error('no controller was parsable from passed file location: %s...', file_location)
            return
        ctrl = Controller(xml_dict_from_file(file_location))
        if not ctrl:
            self.logger.error('no controller was passed...')
            return
        ctrl.file_location = file_location

        self.logger.info('new ctrl loaded -> %s', ctrl.name)
        self.controller = ctrl

    def refresh(self):
        if self.application:
            pass
        return super().refresh()

    def save_controller(self,
                        file_location: str) -> None:
        """Save a :class:`Controller` back to a .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to save :class:`Controller` to.

        """
        if not file_location or not self.controller:
            return
        dict_to_xml_file(self.controller.root_meta_data,
                         file_location)

    def verify_controller(self):
        """verify plc l5x controller
        """
        if not self.controller:
            self.logger.warning('No controller loaded...')
            return

        dups, coils = self.controller.find_redundant_otes(True)
        self.logger.info('Found %s duplicates' % len(dups))
        self.logger.info('Found %s coils in total' % len(coils))

        class _ReportView(View):
            def __init__(self,
                         data_dict: dict):
                super().__init__(config=ViewConfiguration(title='Controller Verify',
                                                          type_=ViewType.TOPLEVEL))

                x = TreeViewGridFrame(self.frame, data_dict=data_dict)
                x.pack(fill=BOTH, expand=True)

        x = _ReportView(dups)
        x.parent.focus()
