""" file tasks
    """
from __future__ import annotations


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

    def _on_file_new(self):
        """Create a new controller instance."""
        self.logger.info('Creating new controller instance...')
        self.application.controller = self.application.create_controller()
        if not self.application.controller:
            self.logger.error('Failed to create new controller instance.')
            return

        # do some extra code here?
        self.logger.info('New controller instance created successfully.')

    def _on_file_open(self,
                      file_location: Optional[str] = None):
        if not file_location:
            file_location = get_open_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No file selected...')
            return

        self.logger.info('File location -> %s', file_location)
        self.application.load_controller(file_location)

    def _on_file_save(self,
                      file_location: Optional[str] = None):
        if not self.application.controller:
            self.logger.warning('No controller loaded, cannot save...')
            return

        if not file_location:
            file_location = get_save_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No save location selected...')
            return

        self.logger.info('Save location -> %s', file_location)
        self.application.save_controller(file_location)

    def inject(self) -> None:
        if not self.application.menu:
            return
        self.application.menu.file.insert_command(0, label='New', command=self._on_file_new)
        self.application.menu.file.insert_separator(1)
        self.application.menu.file.insert_command(2, label='Open', command=self._on_file_open)
        self.application.menu.file.insert_command(3, label='Save', command=self._on_file_save)
        self.application.menu.file.insert_separator(4)
        self.application.menu.file.insert_command(5, label='Exit', command=lambda: sys.exit(0))
