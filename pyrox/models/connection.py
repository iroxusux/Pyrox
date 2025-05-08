"""Main emulation model
    """
from __future__ import annotations


from enum import Enum
from tkinter import BOTH, Button, DISABLED, Entry, LabelFrame, LEFT, NORMAL, StringVar, TOP, X
from typing import Callable, Optional


from pylogix import PLC
from pylogix.lgx_response import Response


from ..types import Application, ApplicationTask, LaunchableModel, ViewConfiguration, View, ViewModel, ViewType

from pyrox.types.plc import ConnectionParameters


class ConnectionCommandType(Enum):
    NA = 0
    READ = 1
    WRITE = 2


class ConnectionCommand:
    def __init__(self,
                 type: ConnectionCommandType,
                 tag_name: str,
                 tag_value: int,
                 data_type: int,
                 response_cb: Callable):
        self._type = type
        self._tag_name = tag_name
        self._tag_value = tag_value
        self._data_type = data_type
        self._response_cb = response_cb

    @property
    def type(self) -> ConnectionCommandType:
        return self._type

    @property
    def tag_name(self) -> str:
        return self._tag_name

    @property
    def tag_value(self) -> int:
        return self._tag_value

    @property
    def data_type(self) -> int:
        return self._data_type

    @property
    def response_cb(self) -> Callable:
        return self._response_cb


class ConnectionView(View):
    """Connection View

    """

    def __init__(self,
                 view_model: Optional['ConnectionViewModel'] = None,
                 config: Optional[ViewConfiguration] = ViewConfiguration()):
        super().__init__(view_model=view_model,
                         config=config)

        self._liveframe: Optional[LabelFrame] = None
        self._plccfgframe: Optional[LabelFrame] = None
        self._ip_addr_entry: Optional[Entry] = None
        self._slot_entry: Optional[Entry] = None
        self._connect_pb: Optional[Button] = None
        self._disconnect_pb: Optional[Button] = None

    @property
    def connect_pb(self) -> Button:
        """
        Get plc connect Button.
        """
        return self._connect_pb

    @property
    def disconnect_pb(self) -> Button:
        """
        Get plc disconnect Button.
        """
        return self._disconnect_pb

    @property
    def ip_addr_entry(self) -> Entry:
        """
        Get plc ip address Entry.
        """
        return self._ip_addr_entry

    @property
    def slot_entry(self) -> Entry:
        """
        Get plc slot Entry.
        """
        return self._slot_entry

    def build(self):
        self._liveframe = LabelFrame(self.frame, text='Live View')
        self._liveframe.pack(fill=BOTH, side=TOP)

        self._plccfgframe = LabelFrame(self._liveframe, text='PLC Configuration')
        self._plccfgframe.pack(side=LEFT)

        _ip_addr = StringVar(self._plccfgframe, '120.15.35.60', 'PLC IP Address')
        self._ip_addr_entry = Entry(self._plccfgframe, textvariable=_ip_addr)
        self._ip_addr_entry.pack(side=LEFT)

        _slot = StringVar(self._plccfgframe, '1', 'PLC Slot Number')
        self._slot_entry = Entry(self._plccfgframe, textvariable=_slot)
        self._slot_entry.pack(side=LEFT)

        self._connect_pb = Button(self._plccfgframe, text='Connect')
        self._connect_pb.pack(side=LEFT, fill=X)

        self._disconnect_pb = Button(self._plccfgframe, text='Disconnect')
        self._disconnect_pb.pack(side=LEFT, fill=X)


class ConnectionViewModel(ViewModel):
    """Connection View Model

    """

    def __init__(self, model: Optional['ConnectionModel'] = None,
                 view: Optional[ConnectionView] = None):
        super().__init__(model, view)

    @property
    def model(self) -> 'ConnectionModel':
        return self._model

    @property
    def view(self) -> ConnectionView:
        return self._view

    def _on_connected(self, connected: bool):
        if connected:
            self.view.connect_pb.configure(state=DISABLED)
            self.view.disconnect_pb.configure(state=NORMAL)
        else:
            self.view.connect_pb.configure(state=NORMAL)
            self.view.disconnect_pb.configure(state=DISABLED)

    def _on_connect(self) -> None:
        ip_addr = self.view.ip_addr_entry.get()
        slot = self.view.slot_entry.get()
        self.model.connect(ConnectionParameters(ip_addr, slot, 500))

    def build(self):
        super().build()
        self.view.connect_pb.config(command=self._on_connect)
        self.view.disconnect_pb.config(command=self.model.disconnect)

        if self.model.connected:
            self.view.connect_pb.config(state=DISABLED)
            self.view.disconnect_pb.config(state=NORMAL)
        else:
            self.view.connect_pb.config(state=NORMAL)
            self.view.disconnect_pb.config(state=DISABLED)


class ConnectionModel(LaunchableModel):
    """Ip Connection Model for PLC testing.

    Uses `pylogix` module for connections.

    .. ------------------------------------------------------------

    Attributes
    -----------
    controller: :class:`Controller`
        Main controller for the emulation application.

    """

    def __init__(self,
                 app: Application):
        super().__init__(application=app,
                         view_model=ConnectionViewModel,
                         view=ConnectionView,
                         view_config=ViewConfiguration(name='PLC Connection',
                                                       parent=app.view.frame,
                                                       type_=ViewType))
        self._connected: bool = False
        self._connecting: bool = False
        self._params: ConnectionParameters = None
        self._on_connection: list[callable] = []
        self._commands: list[ConnectionCommand] = []

    @property
    def connected(self) -> bool:
        """_summary_

        Returns:
            bool: _description_
        """
        return self._connected

    @property
    def on_connection(self) -> list[callable]:
        return self._on_connection

    @property
    def params(self) -> ConnectionParameters:
        """_summary_

        Returns:
            ConnectionParameters: _description_
        """
        return self._params

    @property
    def view_model(self) -> ConnectionViewModel:
        return self._view_model

    def run(self):
        if self.connected is False:  # first check if there was a request to disconnect
            return

        self._strobe_plc()

        if self.connected is False:  # next, check if we lost the connection
            return

        self._run_commands()
        self._commands.clear()  # clear out commands to be processed next time

    def _run_commands(self):
        if not self.connected:
            return  # can't run commands without a connection...

        with PLC(ip_address=self.params.ip_address,
                 slot=self.params.slot) as comm:

            for command in self._commands:
                if command.type == ConnectionCommandType.READ:
                    command.response_cb(comm.Read(command.tag_name, datatype=command.data_type))
                elif command.type == ConnectionCommandType.WRITE:
                    command.response_cb(comm.Write(command.tag_name, command.tag_value, datatype=command.data_type))

    def _set_connected(self,
                       value: bool):
        self._connected = value
        _ = [x(self._connected) for x in self._on_connection]

        if self.view_model:
            self.view_model._on_connected(self._connected)

    def _strobe_plc(self) -> Response:
        with PLC(ip_address=self.params.ip_address,
                 slot=self.params.slot) as comm:
            sts = comm.GetPLCTime()

            if not sts.Value:
                self._set_connected(False)
                self.logger.error('Disonnected. PLC Status Error -> %s', sts.Status)
            elif self._connecting:
                self._connecting = False  # first time connecting status
                self.logger.info('Status -> %s | PlcTime -> %s', str(sts.Status), str(sts.Value))

    def add_command(self, command: ConnectionCommand) -> None:
        """Add a command into this connection model to send to the PLC.

        .. ----------------------------------------------------------------

        Arguments
        ----------
        command :class:`ConnectionCommand`
            Command to add to this model.
        """
        self._commands.append(command)

    def connect(self,
                params: ConnectionParameters):
        """Start connection process to PLC.
        """
        if self.connected:
            self.logger.warning('PLC connection already running...')
            return

        if not params:
            self.logger.error('no parameters, cannot connect')
            return

        self._params = params
        self.logger.info('connecting to -> %s | %s',
                         self.params.ip_address,
                         str(self.params.slot))
        self._commands.clear()  # clear out command buffer for any left-over commands
        self._connecting = True
        self._set_connected(True)  # initialize the connected status. # strobe will handle later.
        self.run()

    def disconnect(self) -> None:
        """disconnect process from plc
        """
        self.logger.info('Disconnecting...')
        self._set_connected(False)


class ConnectionTask(ApplicationTask):
    """Connection task for PLC.
    """

    def __init__(self,
                 application: Application):
        super().__init__(application=application)

    @property
    def model(self) -> ConnectionModel:
        return self._model

    def run(self):
        if not self.model:
            self._model = ConnectionModel(self.application)
            self.logger.info('Launching connection window...')
        self.model.launch()

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='Connection Parameters', command=self.run)
