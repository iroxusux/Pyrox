"""Main emulation model
    """
from __future__ import annotations


from enum import Enum
from typing import Callable, Optional, TYPE_CHECKING


from pylogix import PLC
from pylogix.lgx_tag import Tag
from pylogix.lgx_response import Response

from pyrox.models import Model, ConnectionParameters


if TYPE_CHECKING:
    from .app import App


APP_RUNTIME_INFO_IP = 'connection_params_ip_address'
APP_RUNTIME_INFO_SLOT = 'connection_params_slot'


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


class PlcControllerConnectionModel(Model):
    """.. description::
    Plc Controller Connection Model for managing ethernet connections and commands.
    .. ------------------------------------------------------------
    .. package::
    applications.connection
    .. ------------------------------------------------------------
    .. attributes::
    connected: :class:`bool`
        True if connected, False otherwise.
    on_connection: :class:`list[callable]`
        List of callbacks to run on connection status change.
    params: :class:`ConnectionParameters`
        The connection parameters for this model.
    """

    def __init__(self,
                 app: App):
        super().__init__(application=app)
        self._connected: bool = False
        self._connecting: bool = False
        self._commands: list[ConnectionCommand] = []
        self._on_connection: list[callable] = []
        self._on_new_tags: list[callable] = []
        self._on_tick: list[callable] = []
        self._params: Optional[ConnectionParameters] = None
        self._tags: list[Tag] = []

    @property
    def connected(self) -> bool:
        """get connected status of this model
        .. ------------------------------------------------------------
        .. returns::
        :class:`bool`
            True if connected, False otherwise.
        """
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        """Sets the connection status.
        """
        if not isinstance(value, bool):
            raise TypeError(f'Expected bool, got {type(value)}')
        self._on_connected(value)

    @property
    def on_connection(self) -> list[callable]:
        """a list of callbacks to run when the connection status changes.
        .. ------------------------------------------------------------
        .. returns::
        :class:`list[callable]`
            List of callbacks to run on connection status change.
        """
        return self._on_connection

    @property
    def on_new_tags(self) -> list[callable]:
        """a list of callbacks to run when new tags are fetched.
        .. ------------------------------------------------------------
        .. returns::
        :class:`list[callable]`
            List of callbacks to run when new tags are fetched.
        """
        return self._on_new_tags

    @property
    def on_tick(self) -> list[callable]:
        """a list of callbacks to run on each tick of the PLC connection loop.
        .. ------------------------------------------------------------
        .. returns::
        :class:`list[callable]`
            List of callbacks to run on each tick of the PLC connection loop.
        """
        return self._on_tick

    @property
    def params(self) -> ConnectionParameters:
        """connection parameters for this model.
        .. ------------------------------------------------------------
        .. returns::
        :class:`ConnectionParameters`
            The connection parameters for this model.
        """
        return self._params

    @params.setter
    def params(self, value: ConnectionParameters) -> None:
        """Sets the connection parameters for this model.
        """
        if not isinstance(value, ConnectionParameters):
            raise TypeError(f'Expected ConnectionParameters, got {type(value)}')
        self._params = value
        self.application.runtime_info.set(APP_RUNTIME_INFO_IP, str(self._params.ip_address))
        self.application.runtime_info.set(APP_RUNTIME_INFO_SLOT, str(self._params.slot))
        self.logger.info('Connection parameters set to %s', str(self._params))

    @property
    def tags(self) -> list[Tag]:
        """get the tags from the PLC controller.
        .. ------------------------------------------------------------
        .. returns::
        :class:`list[Tag]`
            List of tags fetched from the PLC controller.
        """
        return self._tags

    @tags.setter
    def tags(self, value: list[Tag]) -> None:
        """Sets the tags for this model.
        """
        if not isinstance(value, list):
            raise TypeError(f'Expected list, got {type(value)}')
        self._tags = value
        [x(self._tags) for x in self._on_new_tags]

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

        self.params = params
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

        [x() for x in self._on_tick]
        self._run_commands()
        self.application.tk_app.after(self.params.rpi, self._connection_loop)

    def _get_controller_tags(self) -> None:
        """Fetch tags from the PLC controller.
        """
        if not self._connected or self._connecting:
            self.logger.error('PLC is not connected, cannot fetch tags.')
            return

        with PLC(ip_address=self._params.ip_address,
                 slot=self._params.slot) as comm:
            tags = comm.GetTagList()
            if tags.Status == 'Success':
                self.tags = [tag for tag in tags.Value]
                self.logger.info('Fetched %d tags from PLC', len(self._tags))
            else:
                self.logger.error('Failed to fetch tags: %s', tags.Status)

    def _on_connected(self, connected: bool):
        self._connected = connected
        self._connecting = False
        [x(self.connected) for x in self.on_connection]

    def _run_commands(self):
        if not self.connected:
            return

        with PLC(ip_address=self.params.ip_address,
                 slot=self.params.slot) as comm:
            self._run_commands_read(comm)
            self._run_commands_write(comm)
        self._commands.clear()

    def _run_commands_read(self, comm: PLC):
        """Run read commands from the command buffer.
        """
        for command in self._commands:
            if command.type == ConnectionCommandType.READ:
                try:
                    response = comm.Read(command.tag_name, datatype=command.data_type)
                    command.response_cb(response)
                except KeyError as e:
                    self.logger.error('Error reading tag %s: %s', command.tag_name, str(e))
                    command.response_cb(Response(tag_name=command.tag_name, value=None, status='Error'))

    def _run_commands_write(self, comm: PLC):
        """Run write commands from the command buffer.
        """
        for command in self._commands:
            if command.type == ConnectionCommandType.WRITE:
                try:
                    try:
                        tag_value = int(command.tag_value)
                    except (ValueError, TypeError):
                        tag_value = command.tag_value  # keep as string if conversion fails
                    response = comm.Write(command.tag_name, tag_value, datatype=command.data_type)
                    command.response_cb(response)
                except KeyError as e:
                    self.logger.error('Error writing tag %s: %s', command.tag_name, str(e))
                    command.response_cb(Response(tag_name=command.tag_name, value=None, status='Error'))

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
        self._connect(params)

    def disconnect(self) -> None:
        """disconnect process from plc
        """
        self.logger.info('Disconnecting...')
        self.connected = False

    def get_controller_tags(self) -> None:
        """Fetch tags from the PLC controller.
        """
        self._get_controller_tags()

    def tag_list_as_dict(self) -> dict:
        pylogix_dict = {
            'Program Tags': {},
            'Module Tags': {},
            'Controller Tags': {},
        }
        for tag in self._tags:
            if 'Program:' in tag.TagName:
                pylogix_dict['Program Tags'][tag.TagName] = tag.__dict__
                pylogix_dict['Program Tags'][tag.TagName]['@Name'] = tag.TagName
            elif ':' in tag.TagName:
                pylogix_dict['Module Tags'][tag.TagName] = tag.__dict__
                pylogix_dict['Module Tags'][tag.TagName]['@Name'] = tag.TagName
            else:
                pylogix_dict['Controller Tags'][tag.TagName] = tag.__dict__
                pylogix_dict['Controller Tags'][tag.TagName]['@Name'] = tag.TagName

        return {
            'pylogix': pylogix_dict,
        }

    def tag_list_as_names(self) -> list[str]:
        """Returns a list of tag names from the PLC tags.
        """
        return [tag.TagName for tag in self._tags]


class PlcWatchTableModel(Model):
    """.. description::
    Model for managing a watch table of PLC tags.
    .. ------------------------------------------------------------
    .. package::
    applications.plcio
    .. ------------------------------------------------------------
    .. attributes::
    tags: :class:`list[Tag]`
        List of tags in the watch table.
    """

    def __init__(self,
                 application: App,
                 connection_model: PlcControllerConnectionModel):
        super().__init__(application=application)
        self._connection_model = connection_model
        self._on_tag_value_update: list[Callable] = []

    @property
    def on_tag_value_update(self) -> list[Callable]:
        """List of callbacks to run when a tag value is updated.
        .. ------------------------------------------------------------
        .. returns::
        :class:`list[Callable]`
            List of callbacks to run on tag value update.
        """
        return self._on_tag_value_update

    @property
    def tags(self) -> list[Tag]:
        """Returns the tags in the watch table.
        """
        return self._tags

    @tags.setter
    def tags(self, value: list[Tag]) -> None:
        """Sets the tags for the watch table.
        """
        if not isinstance(value, list):
            raise TypeError(f'Expected list, got {type(value)}')
        self._tags = value

    def _update_tag_value(self, response: Response) -> None:
        """Update the value of a tag in the watch table.
        This method is called when a read command response is received.
        """
        if not isinstance(response, Response):
            raise TypeError(f'Expected Response, got {type(response)}')

        if response.Status != 'Success':
            self.logger.error('Error updating tag value: %s', response.Status)

        [x(response) for x in self._on_tag_value_update]

    def on_tick(self,
                active_watch_items: list[tuple[str, str]]) -> None:
        """Run on each tick of the PLC connection loop.
        This method is called to update the watch table with the current values of the active tags.
        .. ------------------------------------------------------------
        .. arguments::
        active_watch_items :class:`list[str]`
            List of tag names that are currently being watched.
        """
        if not self._connection_model.connected or not active_watch_items:
            return

        for item, _ in active_watch_items:
            self._connection_model.add_command(ConnectionCommand(ConnectionCommandType.READ,
                                                                 item,
                                                                 0,  # value is not used for read commands
                                                                 None,
                                                                 self._update_tag_value))

    def write_value(self, tag, value):
        """Write a value to a tag in the watch table.
        This method is called to update the value of a tag in the watch table.
        .. ------------------------------------------------------------
        .. arguments::
        tag :class:`str`
            The name of the tag to write to.
        value :class:`int`
            The value to write to the tag.
        """
        if not isinstance(tag, str) or not isinstance(value, str):
            raise TypeError(f'Expected str and str, got {type(tag)} and {type(value)}')

        self._connection_model.add_command(ConnectionCommand(ConnectionCommandType.WRITE,
                                                             tag,
                                                             value,
                                                             None,  # data_type is not used for write commands
                                                             self._update_tag_value))
