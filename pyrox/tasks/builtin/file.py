""" manage PLC tasks as built-ins
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING


from ...models import EmulationModel
from ...services.file import get_open_file, get_save_file
from ...types.application import ApplicationTask
from ...types import SafeList


if TYPE_CHECKING:
    from ...types import Model, Application


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
                 application: Application,
                 model: Model):
        super().__init__(application=application,
                         model=model)

        self.on_new: SafeList[callable] = SafeList()
        self.on_save: SafeList[callable] = SafeList()

    def _on_file_new(self,
                     file_location: Optional[str] = None):
        if not file_location:
            file_location = get_open_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No file selected...')
            return

        self.logger.info('File location -> %s', file_location)

        _ = [x(file_location) for x in self.on_new]

    def _on_file_save(self,
                      file_location: Optional[str] = None):
        if not file_location:
            file_location = get_save_file([("L5X XML Files", ".L5X")])

        if not file_location:
            self.logger.warning('No save location selected...')
            return

        self.logger.info('Save location -> %s', file_location)

        _ = [x(file_location) for x in self.on_save]

    def inject(self) -> None:
        self.application.menu.file.insert_command(0, label='Save', command=self._on_file_save)
        self.application.menu.file.insert_command(0, label='New', command=self._on_file_new)

        if self.model:  # only bind to the correct model when creating
            if isinstance(self.model, EmulationModel):
                self.on_new.append(self.model.load_controller)
                self.on_save.append(self.model.save_controller)
