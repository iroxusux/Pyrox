from __future__ import annotations

from logging import INFO, WARNING, ERROR
import os
from pathlib import Path
import platformdirs
from typing import Optional
from tkinter import PanedWindow, TclError


from ..models import Application, ApplicationTask
from ..models.plc import Controller
from ..models.utkinter import FrameWithTreeViewAndScrollbar, LogWindow, PyroxFrame, TaskFrame
from ..services import file
from ..services.plc_services import dict_to_xml_file, l5x_dict_from_file
from ..services.task_services import find_and_instantiate_class


class ApplicationDirectoryService:
    """Application Directory Service

    Manage Application Directories with this service class

    .. ------------------------------------------------------------

    .. package:: applications.app

    .. ------------------------------------------------------------

    Attributes
    -----------
    root: :class:`str`
        Root directory for this service.
    """

    def __init__(self,
                 author_name: str,
                 app_name: str,
                 **kwargs):
        if not author_name or author_name == '':
            raise ValueError('A valid, non-null author name must be supplied for this class!')

        if not app_name or app_name == '':
            raise ValueError('A valid, non-null application name must be supplied for this class!')

        self._app_name = app_name
        self._author_name = author_name

        super().__init__(**kwargs)

    @property
    def app_name(self) -> str:
        """Application Name supplied to this service class

        .. ------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return self._app_name

    @property
    def author_name(self) -> str:
        """Author Name supplied to this service class

        .. ------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return self._author_name

    @property
    def user_cache(self):
        """User cache directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_cache_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_config(self):
        """User config directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_config_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_data(self):
        """User data directory.

        Example >>> 'C:/Users/JohnSmith/AppData/Local/JSmithEnterprises/MyApplication'

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_data_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_documents(self):
        """User documents directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_documents_dir()

    @property
    def user_downloads(self):
        """User downloads directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_downloads_dir()

    @property
    def user_log(self):
        """User log directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_log_dir(self._app_name, self._author_name)

    def build_directory(self,
                        as_refresh: bool = False):
        """Build the directory for the parent application.

        Uses the supplied name for directory naming.
        """
        # --- cache --- #
        if os.path.isdir(self.user_cache):
            if as_refresh:
                file.remove_all_files(self.user_cache)

        else:
            os.mkdir(self.user_cache)

        # --- config --- #
        if os.path.isdir(self.user_config):
            if as_refresh:
                file.remove_all_files(self.user_config)

        else:
            os.mkdir(self.user_config)

        # --- data --- #
        if os.path.isdir(self.user_data):
            if as_refresh:
                file.remove_all_files(self.user_data)

        else:
            os.mkdir(self.user_data)


class App(Application, ApplicationDirectoryService):
    """Application class for Pyrox.

    This class is used to create and manage the application instance.
    It inherits from the `Application` model and provides additional
    functionality specific to the Pyrox framework.
    """

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         author_name='irox',
                         app_name='pyrox',
                         **kwargs)

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

    def _raise_frame(self,
                     frame: TaskFrame) -> None:
        """Raise a frame to the top of the application."""
        self.clear_workspace()
        if not frame or not frame.winfo_exists():
            self.unregister_frame(frame)
            self.logger.error('Frame does not exist or is not provided.')
            return
        frame.master = self.workspace
        frame.pack(fill='both', expand=True, side='top')

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

        self._workspace = PyroxFrame(sub_frame, text='Workspace', height=500)
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

        tasks = find_and_instantiate_class(directory_path=str(Path(__file__).parent.parent) + '/tasks',
                                           class_name="ApplicationTask",
                                           as_subclass=True,
                                           ignoring_classes=['ApplicationTask', 'AppTask'],
                                           parent_class=ApplicationTask,
                                           application=self)
        self.add_tasks(tasks=tasks)

        self.build_directory()

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
            message: str) -> None:
        """Post a message to this :class:`Application`'s logger frame.

        Arguments
        ----------
        message: :type:`str`
            Message to be sent to this :class:`Application`'s log frame.
        """
        if not self._log_window:
            return

        severity = WARNING if '| WARNING | ' in message else \
            ERROR if '| ERROR | ' in message else INFO

        try:
            self._log_window.log_text.config(state='normal')
            msg_begin = self._log_window.log_text.index('end-1c')
            self._log_window.log_text.insert('end', f'{message}\n')
            msg_end = self._log_window.log_text.index('end-1c')
            self._log_window.log_text.tag_add(message, msg_begin, msg_end)
            self._log_window.log_text.tag_config(message,
                                                 foreground='white' if severity == ERROR else 'black',
                                                 background='yellow' if severity == WARNING else 'red' if severity == ERROR else 'white',
                                                 font=('Courier New', 10, 'bold'))
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
        self._organizer.tree.populate_tree('', self.controller.l5x_meta_data)
        self.logger.info('Done!')

    def register_frame(self,
                       frame: TaskFrame,
                       raise_=False) -> None:
        """Register a frame to this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------
        frame: :class:`Frame`
            The frame to register to this :class:`Application`.

        """
        if not frame:
            raise ValueError('Frame must be provided to register a frame.')

        if not isinstance(frame, TaskFrame):
            raise TypeError(f'Expected TaskFrame, got {type(frame)}')

        self.menu.view.add_command(label=frame.name, command=lambda: self._raise_frame(frame))
        if raise_:
            self._raise_frame(frame)

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

    def set_frame(self,
                  frame: TaskFrame) -> None:
        """Set a frame to the top of the application.

        This method will raise the provided frame to the top of the application.

        .. ------------------------------------------------------------

        Arguments
        -----------
        frame: :class:`TaskFrame`
            The frame to set to the top of the application.

        """
        self._raise_frame(frame)

    def unregister_frame(self,
                         frame: TaskFrame) -> None:
        """Unregister a frame from this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------
        frame: :class:`Frame`
            The frame to unregister from this :class:`Application`.

        """
        if not frame:
            raise ValueError('Frame must be provided to unregister a frame.')

        if not isinstance(frame, TaskFrame):
            raise TypeError(f'Expected TaskFrame, got {type(frame)}')

        self.menu.view.delete(frame.name)


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
