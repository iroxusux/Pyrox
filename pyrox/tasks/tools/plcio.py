"""PLC Inspection Application
    """
from __future__ import annotations

from tkinter import Button, DISABLED, Entry, LabelFrame, NORMAL, StringVar, TOP, LEFT, X

from typing import Optional

from pylogix import PLC
from pylogix.lgx_tag import Tag
from pylogix.lgx_response import Response

from pyrox.applications.app import App, AppTask
from pyrox.models.plc import ConnectionCommand, ConnectionParameters
from pyrox.models.gui import FrameWithTreeViewAndScrollbar, TaskFrame, WatchTableTaskFrame


class PlcIoFrame(TaskFrame):
    """Connection view for PLC i/o.
    """

    def __init__(self,
                 parent=None,
                 connection_params: ConnectionParameters = None,):
        super().__init__(parent,
                         name='PLC I/O',)

        self._conn_params: ConnectionParameters = connection_params
        if not self._conn_params:
            self._conn_params = ConnectionParameters('120.15.35.2', '1')

        self._plccfgframe = LabelFrame(self.content_frame, text='PLC Connection Configuration')
        self._plccfgframe.pack(side=TOP, fill=X)

        _ip_addr = StringVar(self._plccfgframe, self._conn_params.ip_address, 'PLC IP Address')
        self._ip_addr_entry = Entry(self._plccfgframe, textvariable=_ip_addr)
        self._ip_addr_entry.pack(side=LEFT)

        _slot = StringVar(self._plccfgframe, self._conn_params.slot, 'PLC Slot Number')
        self._slot_entry = Entry(self._plccfgframe, textvariable=_slot)
        self._slot_entry.pack(side=LEFT)

        self._connect_pb = Button(self._plccfgframe, text='Connect')
        self._connect_pb.pack(side=LEFT, fill=X)

        self._disconnect_pb = Button(self._plccfgframe, text='Disconnect')
        self._disconnect_pb.pack(side=LEFT, fill=X)

        self._plccmdframe = LabelFrame(self.content_frame, text='PLC Commands')
        self._plccmdframe.pack(side=TOP, fill=X)

        self._get_tags_pb = Button(self._plccmdframe, text='Read Tags')
        self._get_tags_pb.pack(side=LEFT, fill=X)

        self._watch_table_pb = Button(self._plccmdframe, text='Watch Table')
        self._watch_table_pb.pack(side=LEFT, fill=X)

        self._tags_frame = FrameWithTreeViewAndScrollbar(self.content_frame, text='PLC Tags')
        self._tags_frame.pack(side=TOP, fill='both', expand=True)

    @property
    def connect_pb(self) -> Button:
        """Returns the connect button.
        """
        return self._connect_pb

    @property
    def disconnect_pb(self) -> Button:
        """Returns the disconnect button.
        """
        return self._disconnect_pb

    @property
    def get_tags_pb(self) -> Button:
        """Returns the get tags button.
        """
        return self._get_tags_pb

    @property
    def ip_addr_entry(self) -> Entry:
        """Returns the IP address entry.
        """
        return self._ip_addr_entry

    @property
    def slot_entry(self) -> Entry:
        """Returns the slot entry.
        """
        return self._slot_entry

    @property
    def tags_frame(self) -> FrameWithTreeViewAndScrollbar:
        """Returns the tags tree view.
        """
        return self._tags_frame

    @property
    def watch_table_pb(self) -> Button:
        """Returns the watch table button.
        """
        return self._watch_table_pb


class PlcIoTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)
        self._connected: bool = False
        self._connecting: bool = False
        self._tags: list[Tag] = []
        self._commands: list[ConnectionCommand] = []
        self._frame: Optional[PlcIoFrame] = None
        self._params: Optional[ConnectionParameters] = None
        self._watch_table_frame: Optional[WatchTableTaskFrame] = None

    def _connect(self,
                 params: ConnectionParameters) -> None:
        """Connect to the PLC.
        """
        self.logger.info('Connecting to PLC...')
        if self._connected:
            self.logger.warning('PLC connection already running...')
            return

        if not params:
            self.logger.error('no parameters, cannot connect')
            return

        self._params = params
        self.logger.info('connecting to -> %s | %s',
                         self._params.ip_address,
                         str(self._params.slot))
        self._commands.clear()  # clear out command buffer for any left-over commands
        self._connecting = True
        self._connection_loop()

    def _connection_loop(self) -> None:
        """Main connection loop for the PLC.
        """
        if not self._connected and not self._connecting:
            self.logger.info('PLC connection not established or lost...')
            self.connected = False
            return

        try:
            self._strobe_plc()
        except Exception as e:
            self.logger.error('Error during PLC connection: %s', str(e))
            self.connected = False

        self.application.tk_app.after(self._params.rpi, self._connection_loop)

    def _get_controller_tags(self) -> None:
        """Fetch tags from the PLC controller.
        """
        if not self._params:
            self.logger.error('No connection parameters set.')
            return

        if self._connecting:
            self.logger.warning('PLC is still connecting, cannot fetch tags.')
            return

        if not self._connected:
            self.logger.error('PLC is not connected, cannot fetch tags.')
            return

        with PLC(ip_address=self._params.ip_address,
                 slot=self._params.slot) as comm:
            tags = comm.GetTagList()
            if tags.Status == 'Success':
                self._tags = [tag for tag in tags.Value]
                self.logger.info('Fetched %d tags from PLC', len(self._tags))
            else:
                self.logger.error('Failed to fetch tags: %s', tags.Status)

        self._frame.tags_frame.tree.clear()
        self._frame.tags_frame.tree.populate_tree('', self._tag_list_as_dict())

    def _launch_watch_table(self) -> None:
        """Launch the watch table for PLC tags.
        """
        if self._watch_table_frame and self._watch_table_frame.winfo_exists():
            self.application.set_frame(self._watch_table_frame)
            return

        if not self._frame:
            self.logger.error('PLC I/O frame not initialized.')
            return

        if self._tags:
            self.logger.info('Launching watch table with %d tags from "read tags"', len(self._tags))
            tags = self._tag_list_as_dict()
        else:
            self.logger.info('Launching watch table with %d tags from "get controller tags"', len(self.application.controller.tags))
            tags = self.application.controller.tags.as_list_names() if self.application.controller else {}

        self._watch_table_frame = WatchTableTaskFrame(self.application.workspace,
                                                      all_symbols=tags)
        self.application.register_frame(self._watch_table_frame, raise_=True)

    def _on_connected(self, connected: bool):
        self._connected = connected
        self._connecting = False
        if connected:
            self._frame.connect_pb.configure(state=DISABLED)
            self._frame.disconnect_pb.configure(state=NORMAL)
        else:
            self._frame.connect_pb.configure(state=NORMAL)
            self._frame.disconnect_pb.configure(state=DISABLED)

    def _on_connect(self) -> None:
        ip_addr = self._frame.ip_addr_entry.get()
        slot = self._frame.slot_entry.get()
        self._connect(ConnectionParameters(ip_addr, slot, 500))

    def _on_disconnect(self) -> None:
        """disconnect process from plc
        """
        self.logger.info('Disconnecting...')
        self.connected = False

    def _strobe_plc(self) -> Response:
        with PLC(ip_address=self._params.ip_address,
                 slot=self._params.slot) as comm:
            sts = comm.GetPLCTime()

            if not sts.Value:
                self.connected = False
                self.logger.error('Disonnected. PLC Status Error -> %s', sts.Status)
            elif self._connecting:
                self.connected = True
                self.logger.info('Status -> %s | PlcTime -> %s', str(sts.Status), str(sts.Value))

            self._connecting = False

    def _tag_list_as_dict(self) -> dict:
        tag_dict = {}
        for tag in self._tags:
            tag_dict[tag.TagName] = tag.__dict__
            tag_dict[tag.TagName]['@Name'] = tag.TagName  # add @Name for compatibility with tree view

        return tag_dict

    @property
    def connected(self) -> bool:
        """Returns the connection status.
        """
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        """Sets the connection status.
        """
        if not isinstance(value, bool):
            raise TypeError(f'Expected bool, got {type(value)}')
        self._on_connected(value)

    def run(self):
        if not self._frame or not self._frame.winfo_exists():
            self._frame = PlcIoFrame(self.application.workspace)
            self._frame.connect_pb.config(command=self._on_connect)
            self._frame.disconnect_pb.config(command=self._on_disconnect)
            self._frame.get_tags_pb.config(command=self._get_controller_tags)
            self._frame.watch_table_pb.config(command=self._launch_watch_table)
            self._on_connected(self._connected)
            self.application.register_frame(self._frame, raise_=True)

        self.application.logger.info('Starting plc io task...')
        # some custom logic
        self.application.set_frame(self._frame)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='PLC I/O', command=self.run)
