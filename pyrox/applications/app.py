from __future__ import annotations

from pathlib import Path
from typing import Optional
from tkinter import PanedWindow, TclError

from ..models import Application, ApplicationTask
from ..models.plc import Controller
from ..models.utkinter import FrameWithTreeViewAndScrollbar, LogWindow, PyroxFrame
from ..services.plc_services import dict_to_xml_file, l5x_dict_from_file
from ..services.task_services import find_and_instantiate_class
from ..services.utkinter import populate_tree


class App(Application):
    """Application class for Pyrox.

    This class is used to create and manage the application instance.
    It inherits from the `Application` model and provides additional
    functionality specific to the Pyrox framework.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller: Optional[Controller] = None
        self._organizer: Optional[FrameWithTreeViewAndScrollbar] = None
        self._log_window: Optional[LogWindow] = None
        self._paned_window: Optional[PanedWindow] = None
        self._workspace: Optional[PyroxFrame] = None

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

    @property
    def organizer(self) -> Optional[FrameWithTreeViewAndScrollbar]:
        """The organizer window for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            organizer: :class:`OrganizerWindow`
        """
        return self._organizer

    @property
    def workspace(self) -> Optional[PyroxFrame]:
        """The workspace window for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            workspace: :class:`LabelFrame`
        """
        return self._workspace

    def build(self):
        """Build this :class:`Application`.

        This method will build the main menu, organizer window, log window and workspace if they are enabled in the configuration.

        """
        super().build()

        self._paned_window = PanedWindow(self.frame, orient='horizontal')

        self._organizer = FrameWithTreeViewAndScrollbar(master=self._paned_window, text='Organizer')
        self._organizer.pack(side='left', fill='y')

        self._paned_window.add(self._organizer)

        # use an additional sub frame to pack widgets on left side of screen neatly
        sub_frame = PanedWindow(self._paned_window, orient='vertical')

        self._workspace = PyroxFrame(sub_frame, text='Workspace', height=350)
        self._workspace.pack(side='top', fill='x')
        sub_frame.add(self._workspace)

        self._log_window = LogWindow(sub_frame)
        self._log_window.pack(side='bottom', fill='x')
        self._log_handler.set_callback(self.log)

        sub_frame.add(self._log_window)
        sub_frame.pack(fill='both', expand=True)
        sub_frame.configure(sashrelief='groove', sashwidth=5, sashpad=5)

        self._paned_window.add(sub_frame)
        self._paned_window.pack(fill='both', expand=True)
        self._paned_window.configure(sashrelief='groove', sashwidth=5, sashpad=5)

        tasks = find_and_instantiate_class(str(Path(__file__).parent.parent) + '/tasks',
                                           "ApplicationTask",
                                           True,
                                           ApplicationTask,
                                           application=self)
        self.add_tasks(tasks=tasks)

    def clear_organizer(self) -> None:
        """Clear organizer of all children.

        This method will remove all children from the organizer window, if it exists.

        """
        if not self.organizer:
            return

        self.organizer.tree.delete(*self.organizer.tree.get_children())

    def clear_workspace(self) -> None:
        """Clear workspace of all children.
        """
        if not self.workspace:
            return

        for child in self.workspace.winfo_children():
            child.pack_forget()

    def create_controller(self) -> Optional[Controller]:
        """Create a new :class:`Controller` instance for this :class:`Application`."""
        self.logger.info('Creating new controller instance...')
        return Controller()

    def load_controller(self,
                        file_location: str) -> None:
        """Attempt to load a :class:`Controller` from a provided .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to open :class:`Controller` from.

        """
        self.logger.info('Loading controller from file: %s', file_location)
        try:
            ctrl = Controller(l5x_dict_from_file(file_location))
        except KeyError as e:
            self.logger.error('error parsing controller from file %s: %s', file_location, e)
            return

        if not ctrl:
            self.logger.error('no controller was passed...')
            return
        ctrl.file_location = file_location

        self.logger.info('new ctrl loaded -> %s', ctrl.name)
        self.controller = ctrl

    def log(self,
            message: str):
        """Post a message to this :class:`Application`'s logger frame.

        Arguments
        ----------
        message: :type:`str`
            Message to be sent to this :class:`Application`'s log frame.
        """
        if not self._log_window:
            return

        try:
            self._log_window.log_text.config(state='normal')
            self._log_window.log_text.insert('end', f'{message}\n')
            self._log_window.log_text.see('end')
            line_count = self._log_window.log_text.count('1.0', 'end', 'lines')[0]
            if line_count > 100:
                dlt_count = abs(line_count - 100) + 1
                self._log_window.log_text.delete('1.0', float(dlt_count))
            self._log_window.log_text.config(state='disabled')
        except TclError as e:
            print('Tcl error, original msg -> %s' % e)
        self._log_window.update()

    def refresh(self, **_):
        if not self.organizer:
            return

        self.logger.info('Refreshing application gui...')
        self.clear_organizer()
        self.clear_workspace()
        populate_tree(self._organizer.tree, '', self.controller.l5x_meta_data)
        self.logger.info('Done!')

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


class AppTask(ApplicationTask):
    def __init__(self, application):
        super().__init__(application)

    @property
    def application(self) -> App:
        """Application instance associated with this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: :class:`App`
        """
        return super().application
