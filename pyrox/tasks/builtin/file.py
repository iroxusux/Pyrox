""" file tasks
    """
from __future__ import annotations


import tkinter.messagebox
from typing import Optional
import sys


from pyrox.services.file import get_open_file, get_save_file
from pyrox.models import ApplicationTask


class FileTask(ApplicationTask):
    """PLC Tasker `Task`

    Injects `New` and `Save` tk menu buttons into parent :class:`Application`.

    Hosts delegates for `on_new` and `on_save` for ui callback to PLC model..

    .. ------------------------------------------------------------

    Attributes
    -----------
    on_new: :class:`SafeList`
        List of delegates to be called when user clicks 'New' in parent menu.

    on_save: :class:`SafeList`
        List of delegates to be called when user clicks 'Save' in parent menu.
    """

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)

    def _prompt_for_controller_closing(self) -> bool:
        # Prompt if a controller is already loaded
        if self.application.controller:
            proceed = tkinter.messagebox.askyesno(
                "Open New File",
                "A controller is currently loaded. Do you want to continue and open a new file?"
            )
            if not proceed:
                self.logger.info('User cancelled opening a new file.')
                return False
        return True

    def _on_file_close(self):
        """Close the current controller instance."""
        if not self.application.controller:
            self.logger.warning('No controller loaded, cannot close...')
            return

        self.logger.info('Closing current controller instance...')
        self.application.controller = None
        self.logger.info('Controller instance closed successfully.')

    def _on_file_new(self):
        """Create a new controller instance."""
        if not self._prompt_for_controller_closing():
            return
        self.application.new_controller()

    def _on_file_open(self,
                      file_location: Optional[str] = None):
        if not self._prompt_for_controller_closing():
            return

        if not file_location:
            file_location = get_open_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No file selected...')
            return

        self.logger.info('File location:\n%s', file_location)
        self.application.load_controller(file_location)

    def _on_file_save(self,
                      file_location: Optional[str] = None,
                      save_as: bool = False):
        if not self.application.controller:
            self.logger.warning('No controller loaded, cannot save...')
            return

        if not save_as and self.application.controller.file_location:
            file_location = file_location or self.application.controller.file_location
        elif save_as:
            file_location = None

        if not file_location:
            file_location = get_save_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No save location selected...')
            return

        self.logger.info('Save location:\n%s', file_location)
        self.application.save_controller(file_location)

    def inject(self) -> None:
        if not self.application.menu:
            return
        self.application.menu.file.insert_command(0, label='New Controller', command=self._on_file_new)
        self.application.menu.file.insert_separator(1)
        self.application.menu.file.insert_command(2, label='Open L5X', command=self._on_file_open)
        self.application.menu.file.insert_command(3, label='Save L5X', command=self._on_file_save)
        self.application.menu.file.insert_command(4, label='Save L5X As...', command=lambda: self._on_file_save(save_as=True))
        self.application.menu.file.insert_separator(5)
        self.application.menu.file.insert_command(6, label='Close L5X', command=self._on_file_close)
        self.application.menu.file.insert_separator(7)
        self.application.menu.file.insert_command(8, label='Exit', command=lambda: sys.exit(0))
