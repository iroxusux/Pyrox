from typing import Optional


from ..models import Application
from ..models.plc import Controller
from ..models.utkinter import populate_tree
from ..tasks.builtin import ALL_TASKS
from ..services.plc_services import dict_to_xml_file, l5x_dict_from_file


class App(Application):
    """Application class for Pyrox.

    This class is used to create and manage the application instance.
    It inherits from the `Application` model and provides additional
    functionality specific to the Pyrox framework.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller: Optional[Controller] = None
        self.add_tasks(tasks=ALL_TASKS)
        self.logger.info('Pyrox Application initialized.')

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

    def refresh(self, **_):
        if not self.organizer:
            return

        self.clear_workspace()
        populate_tree(self._organizer.tree, '', self.controller.l5x_meta_data)

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
