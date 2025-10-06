"""PLC IO Application Manager.
"""
import importlib
from typing import Optional
from pyrox.applications.app import App
from pyrox.models.plc import connection
from pyrox.models.gui import plcio
from pyrox.services.logging import log


class PlcIoApplicationManager:
    """Application manager for PLC IO communications.
    """

    def __init__(
        self,
        application: App
    ) -> None:
        importlib.reload(connection)
        importlib.reload(plcio)

        self.application = application

        if self.application.controller:
            ip_address = self.application.controller.ip_address
        else:
            ip_address = None

        if not ip_address:
            ip_address = '192.168.1.1'

        self.connection_model = connection.ControllerConnection(
            parameters=connection.ConnectionParameters(
                connection.Ipv4Address(ip_address),
                slot=0,
                rpi=500
            ))

        self.frame = plcio.PlcIoFrame(
            self.application.workspace,
        )

        self.application.register_frame(self.frame, True)
        self.frame.on_connect_pb_clicked(self.connect)
        self.frame.on_disconnect_pb_clicked(self.disconnect)

    def connect(
        self,
        connection_parameters: Optional[connection.ConnectionParameters] = None
    ) -> None:
        """Connect to the PLC.
        """
        if not connection_parameters:
            ip_address = self.frame.ip_addr_entry.get()
            if not ip_address:
                log(self).error('IP address is required to connect to PLC')
                return
            slot = self.frame.slot_entry.get()
            if not slot:
                log(self).error('Slot is required to connect to PLC')
                return
            connection_parameters = connection.ConnectionParameters(
                connection.Ipv4Address(ip_address),
                slot=slot,
                rpi=500
            )
        self.connection_model.connect(connection_parameters)

    def disconnect(self) -> None:
        """Disconnect from the PLC.
        """
        self.connection_model.disconnect()
