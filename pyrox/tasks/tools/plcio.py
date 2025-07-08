"""PLC Inspection Application
    """
from __future__ import annotations

from tkinter import Button, DISABLED, Entry, LabelFrame, NORMAL, StringVar, TOP, LEFT, X

from typing import Optional

from pylogix.lgx_response import Response
from pyrox.applications import App, AppTask, PlcControllerConnectionModel, PlcWatchTableModel
from pyrox.models.plc import ConnectionParameters
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
        self._connection_model: PlcControllerConnectionModel = PlcControllerConnectionModel(application)
        self._connection_model.on_connection.append(self._on_connected)
        self._connection_model.on_new_tags.append(self._clear_and_populate_tags)
        self._frame: Optional[PlcIoFrame] = None
        self._plc_watch_table_model: PlcWatchTableModel = PlcWatchTableModel(application, self._connection_model)
        self._watch_table_frame: Optional[WatchTableTaskFrame] = None

    def _clear_and_populate_tags(self,
                                 _) -> None:
        self._frame.tags_frame.tree.clear()
        self._frame.tags_frame.tree.populate_tree('', self._connection_model.tag_list_as_dict())

    def _launch_watch_table(self) -> None:
        """Launch the watch table for PLC tags.
        """
        if not self._watch_table_frame or not self._watch_table_frame.winfo_exists():
            self._watch_table_frame = WatchTableTaskFrame(self.application.workspace,
                                                          all_symbols=self._connection_model.tag_list_as_names())
            self._connection_model.on_new_tags.append(
                lambda: self._watch_table_frame.update_symbols(self._connection_model.tag_list_as_names()))
            self._connection_model.on_tick.append(lambda: self._plc_watch_table_model.on_tick(self._watch_table_frame.get_watch_table()))
            self._plc_watch_table_model.on_tag_value_update.append(self._update_watch_table_value)
            self.application.register_frame(self._watch_table_frame, raise_=True)
        else:
            self.application.set_frame(self._watch_table_frame)

    def _on_connected(self, connected: bool):
        if connected:
            self._frame.connect_pb.configure(state=DISABLED)
            self._frame.disconnect_pb.configure(state=NORMAL)
        else:
            self._frame.connect_pb.configure(state=NORMAL)
            self._frame.disconnect_pb.configure(state=DISABLED)

    def _update_watch_table_value(self, response):
        """Update the watch table with the value of a tag.
        This method is called when a read command response is received.
        """
        if not isinstance(response, Response):
            raise TypeError(f'Expected Response, got {type(response)}')

        # Notify the watch table model to update the value
        self._watch_table_frame.update_row_by_name(response.TagName, response.Value)

    def add_tag_to_watch_table(self, tag_name: str) -> None:
        """Add a tag to the watch table.

        Args:
            tag_name (str): The name of the tag to add.
        """
        if not self._watch_table_frame or not self._watch_table_frame.winfo_exists():
            return

        # Add the tag to the watch table
        self._watch_table_frame.add_tag(tag_name)

    def start(self):
        if not self._frame or not self._frame.winfo_exists():
            self._frame = PlcIoFrame(self.application.workspace)
            self._frame.connect_pb.config(command=lambda: self._connection_model.connect(ConnectionParameters(
                self._frame.ip_addr_entry.get(),
                self._frame.slot_entry.get(),
                500)))
            self._frame.disconnect_pb.config(command=self._connection_model.disconnect)
            self._frame.get_tags_pb.config(command=self._connection_model.get_controller_tags)
            self._frame.watch_table_pb.config(command=self._launch_watch_table)
            self._on_connected(self._connection_model.connected)
            self.application.register_frame(self._frame, raise_=True)
        else:
            self.application.set_frame(self._frame)
        super().start()

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='PLC I/O', command=self.start)
