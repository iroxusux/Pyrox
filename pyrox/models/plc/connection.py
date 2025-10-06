"""Connection parameters and commands for a PLC
"""
from enum import Enum
from typing import Callable, Optional
from pylogix import PLC
from pylogix.lgx_response import Response
from pyrox.models.abc.network import Ipv4Address
from pyrox.services.timer import TimerService


class ConnectionParameters:

    def __init__(
        self,
        ip_address: Ipv4Address,
        slot: int,
        rpi: int = 250
    ) -> None:
        self.ip_address = ip_address
        self.slot = slot
        self.rpi = rpi

    @property
    def rpi(self) -> float:
        return self._rpi

    @rpi.setter
    def rpi(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError('rpi must be a number')
        if value < 1:
            raise ValueError('rpi must be a positive number')
        self._rpi = float(value)

    @property
    def slot(self) -> int:
        return self._slot

    @slot.setter
    def slot(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError('slot must be an integer')
        if value < 0:
            raise ValueError('slot must be a non-negative integer')
        if value > 16:
            raise ValueError('slot must be between 0 and 16')
        self._slot = value


class ConnectionCommandType(Enum):
    NA = 0
    READ = 1
    WRITE = 2


class ConnectionCommand:
    """Connection Command for a PLC
    """

    def __init__(
        self,
        type: ConnectionCommandType,
        tag_name: str,
        tag_value: int,
        data_type: int,
        response_cb: Callable
    ) -> None:
        self.type: ConnectionCommandType = type
        self.tag_name: str = tag_name
        self.tag_value: int = tag_value
        self.data_type: int = data_type
        self.response_cb: Callable = response_cb


class ControllerConnection:
    """Controller Connection for a PLC
    """

    def __init__(
        self,
        parameters: ConnectionParameters,
        commands: list[ConnectionCommand] = []
    ) -> None:
        self.commands = commands
        self.parameters = parameters
        self.is_connected = False
        self._commands = []
        self._subscribers = []
        self._timer_service = TimerService()

    def _connect(
        self,
        params: Optional[ConnectionParameters] = None
    ) -> None:
        """Connect to the PLC.
        """
        if self.is_connected:
            return

        if params:
            self.parameters = params

        self._connection_loop()

    def _connection_loop(self) -> None:
        """Main connection loop for the PLC.
        """
        if not self.is_connected:
            return

        try:
            if not self._strobe_plc():
                self.is_connected = False
                return
        except Exception:
            self.is_connected = False
            return

        self._tick()
        self._run_commands()
        self._schedule()

    def _run_commands(self):
        if not self.is_connected:
            return

        with PLC(
            ip_address=str(self.parameters.ip_address),
            slot=self.parameters.slot
        ) as comm:
            self._run_commands_read(comm)
            self._run_commands_write(comm)
        self._commands.clear()

    def _run_commands_read(self, comm: PLC):
        """Run read commands from the command buffer.
        """
        read_commands = [cmd for cmd in self._commands if cmd.type == ConnectionCommandType.READ]
        for command in read_commands:
            try:
                response = comm.Read(command.tag_name, datatype=command.data_type)
                command.response_cb(response)
            except KeyError:
                command.response_cb(Response(tag_name=command.tag_name, value=None, status='Error'))

    def _run_commands_write(self, comm: PLC):
        """Run write commands from the command buffer.
        """
        write_commands = [cmd for cmd in self._commands if cmd.type == ConnectionCommandType.WRITE]
        for command in write_commands:
            try:
                try:
                    tag_value = int(command.tag_value)
                except (ValueError, TypeError):
                    tag_value = command.tag_value  # keep as string if conversion fails
                response = comm.Write(command.tag_name, tag_value, datatype=command.data_type)
                command.response_cb(response)
            except KeyError:
                command.response_cb(Response(tag_name=command.tag_name, value=None, status='Error'))

    def _schedule(self) -> None:
        """Schedule the next connection loop iteration.
        """
        if not self.is_connected:
            return

        self._timer_service.schedule_task(self._connection_loop, self.parameters.rpi)

    def _strobe_plc(self) -> Response:
        with PLC(
            ip_address=str(self.parameters.ip_address),
            slot=self.parameters.slot
        ) as comm:
            return comm.GetPLCTime()

    def _tick(self) -> None:
        [callback() for callback in self._subscribers]

    def connect(
        self,
        params: Optional[ConnectionParameters] = None
    ) -> None:
        """Start connection process to PLC.
        """
        self._connect(params)

    def subscribe_to_ticks(self, callback: Callable) -> None:
        """Subscribe to tick events.

        Args:
            callback: Function to call on each tick
        """
        if not callable(callback):
            raise ValueError('Callback must be callable')
        self._subscribers.append(callback)

    def unsubscribe_from_ticks(self, callback: Callable) -> None:
        """Unsubscribe from tick events.

        Args:
            callback: Function to remove from subscribers
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
