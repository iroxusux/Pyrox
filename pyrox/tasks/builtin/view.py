""" view tasks
    """
from __future__ import annotations

from tkinter import Menu
from pyrox.models import ApplicationTask


class ViewTask(ApplicationTask):

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)

    def _open_dir(self, dir_location: str):
        """Open a directory in the file explorer."""

        if not dir_location:
            self.logger.warning('No directory selected...')
            return

        self.logger.info('Opening directory -> %s', dir_location)
        try:
            import os
            os.startfile(dir_location)
        except Exception as e:
            self.logger.error(f'Failed to open directory: {e}')

    def inject(self) -> None:
        if not self.application.menu:
            self.logger.error('Application menu not found, cannot inject view tasks.')
            return
        getattr(self.application, 'all_directories', None)
        if not self.application.directory_service.all_directories:
            self.logger.error('Application does not support directories services, cannot create view tasks.')
            return
        drop_down = Menu(self.application.menu.view, name='application_directories', tearoff=0)
        self.application.menu.view.add_cascade(menu=drop_down, label='Application Directories',)
        for dir_name in self.application.directory_service.all_directories:
            drop_down.add_command(label=dir_name, command=lambda d=dir_name: self._open_dir(
                self.application.directory_service.all_directories[d]))
