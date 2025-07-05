from __future__ import annotations

import copy
import os
from pathlib import Path
import platformdirs
from typing import Any, Optional
from tkinter import PanedWindow


from ..models import Application, ApplicationTask, HashList
from ..models.plc import Controller, PlcObject
from ..models.gui import (
    ContextMenu,
    FrameWithTreeViewAndScrollbar,
    LogWindow,
    MenuItem,
    PyroxFrame,
    TaskFrame,
    ValueEditPopup
)
from ..models.gui.plc import PlcGuiObject
from ..services import file
from ..services.dictionary_services import remove_none_values_inplace
from ..services.plc_services import dict_to_xml_file, l5x_dict_from_file, edit_plcobject_in_taskframe
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
        self.build_directory()

        super().__init__(**kwargs)

    @property
    def all_directories(self) -> dict:
        """All directories for this service class.

        .. ------------------------------------------------

        Returns
        ----------
        :class:`dict`
            Dictionary of all directories for this service class.
        """
        return {
            'user_cache': self.user_cache,
            'user_config': self.user_config,
            'user_data': self.user_data,
            'user_documents': self.user_documents,
            'user_downloads': self.user_downloads,
            'user_log': self.user_log
        }

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

    @property
    def user_log_file(self) -> str:
        """User log file.

        This is the file where the application will log messages.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return os.path.join(self.user_log, f'{self._app_name}.log')

    def build_directory(self,
                        as_refresh: bool = False):
        """Build the directory for the parent application.

        Uses the supplied name for directory naming.
        """
        for dir in self.all_directories.values():
            if not os.path.isdir(dir):
                os.makedirs(dir, exist_ok=True)
            else:
                if as_refresh:
                    file.remove_all_files(dir)


class AppFrameWithTreeViewAndScrollbar(FrameWithTreeViewAndScrollbar):
    """A frame with a tree view and scrollbar for the Pyrox Application.

    This class extends `FrameWithTreeViewAndScrollbar` to provide a specific
    implementation for the Pyrox application, allowing for easy management of
    tasks and other elements in the application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         base_gui_class=PlcGuiObject,
                         **kwargs)
        self.logger.info('AppFrameWithTreeViewAndScrollbar initialized.')


class AppOrganizer(AppFrameWithTreeViewAndScrollbar):
    """Organizer window for the Pyrox Application.

    This class extends `FrameWithTreeViewAndScrollbar` to provide an organizer
    window that can be used to manage tasks and other elements in the application.
    It is intended to be used as a part of the main application frame.
    """

    class OrganizerContextMenu(ContextMenu):
        """Context menu for the organizer window.

        This class extends `ContextMenu` to provide a context menu specific to the organizer window.
        It can be used to add, remove, or manage tasks and other elements in the organizer.
        """

        def __init__(self,
                     *args,
                     controller: Optional[Controller] = None,
                     parent: AppOrganizer = None,
                     **kwargs):
            self._controller: Optional[Controller] = controller
            self._parent: Optional[AppOrganizer] = parent
            super().__init__(*args,
                             tearoff=0,
                             **kwargs)
            self.logger.info('Organizer context menu initialized.')
            self.on_refresh: list[callable] = []

        @property
        def _default_menu_items(self) -> list[MenuItem]:
            """Default menu items for the organizer context menu."""
            return [
                MenuItem(label='Refresh',
                         command=self._on_refresh),
            ]

        def _on_modify(self,
                       item: str = None,
                       data: tuple[str, Any] = None) -> None:
            """Handle the modify action in the context menu."""
            if not item:
                self.logger.error('No data provided for modification.')
                return

            self.logger.info(f'Modifying item: {item}')
            ValueEditPopup(parent=self.master,
                           value=data[0][data[1]],
                           callback=lambda x: self._on_modify_accept(item=item, new_value=x, data=data),
                           title='Modify Item')

        def _on_modify_accept(self,
                              item: str = None,
                              new_value: Any = None,
                              data: tuple[str, Any] = None) -> None:
            data[0][data[1]] = new_value
            self.logger.info(f'Value modified: {new_value} | item: {item}')
            self._parent.tree.update_node_value(item, new_value)

        def _on_modify_plc_object(self,
                                  item: str = None,
                                  plc_object: PlcObject = None) -> None:
            """Handle the modification of a PlcObject in the context menu."""
            app = self._parent.application
            frame = edit_plcobject_in_taskframe(app.workspace,
                                                plc_object,
                                                PlcGuiObject.from_data)
            if not frame:
                self.logger.error('Failed to create frame for editing PLC object.')
                return
            app.register_frame(frame, raise_=True)

        def _on_refresh(self):
            [x() for x in self.on_refresh if callable(x)]

        def compile_menu_from_item(self,
                                   item: str = None,
                                   data: Any = None) -> list[MenuItem]:
            """Compile the context menu from the given item."""
            menu_list = self._default_menu_items

            if not item or not data:
                return menu_list

            if isinstance(data[0], (list, HashList)):
                obj = data[0][data[1]]
            elif isinstance(data[0], dict):
                obj = data[0].get(data[1], None)
            elif isinstance(data[0], PlcObject):
                obj = getattr(data[0], data[1], None)
            else:
                return menu_list

            if isinstance(obj, PlcObject):
                # If the data is a PlcObject, we can add specific actions
                menu_list.insert(0, MenuItem(label='Modify',
                                             command=lambda: self._on_modify_plc_object(item=item, plc_object=obj)))

            return menu_list

    def __init__(self,
                 *args,
                 application: Optional[App] = None,
                 controller: Optional[Controller] = None,
                 **kwargs):
        super().__init__(*args,
                         context_menu=self.OrganizerContextMenu(controller=controller,
                                                                parent=self),
                         **kwargs)
        self._application: Optional[App] = application
        self._controller: Optional[Controller] = controller
        self.logger.info('Organizer initialized.')

    @property
    def application(self) -> Optional[App]:
        """Application associated with this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Optional[:class:`App`]
        """
        return self._application

    @property
    def context_menu(self) -> OrganizerContextMenu:
        """Context menu for this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            context_menu: :class:`OrganizerContextMenu`
        """
        return self.tree.context_menu

    @property
    def controller(self) -> Optional[Controller]:
        """Controller associated with this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller`]
        """
        return self._controller


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
                         author_name='physirox',
                         app_name='pyrox',
                         **kwargs)

        self._controller: Optional[Controller] = None
        self._organizer: Optional[AppOrganizer] = None
        self._log_window: Optional[LogWindow] = None
        self._paned_window: Optional[PanedWindow] = None
        self._workspace: Optional[PyroxFrame] = None
        self._registered_frames: HashList[TaskFrame] = HashList('name')

        self.logger.info('Pyrox Application initialized.')

        # clear log file
        try:
            with open(self.user_log_file, 'w', encoding='utf-8') as log_file:
                log_file.write('')  # Create an empty log file
        except IOError as e:
            self.logger.error(f'Error creating log file {self.user_log_file}: {e}')

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
    def organizer(self) -> Optional[AppOrganizer]:
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
        if frame not in self._registered_frames:
            self.logger.error(f'Frame {frame.name} is not registered in this application.')
            self.register_frame(frame, raise_=False)
        frame.master = self.workspace
        frame.pack(fill='both', expand=True, side='top')
        self._set_frame_selected(frame)

    def _set_frame_selected(self, frame):
        """Set the selected frame in the view menubar."""
        cmds = self.menu.get_menu_commands(self.menu.view)
        [self.menu.view.entryconfig(self.menu.view.index(entry), state='normal') for entry in cmds if entry != frame.name]
        self.menu.view.entryconfig(self.menu.view.index(frame.name), state='active')

    def build(self):
        """Build this :class:`Application`.

        This method will build the main menu, organizer window, log window and workspace if they are enabled in the configuration.

        """
        super().build()

        self._paned_window = PanedWindow(self.frame, orient='horizontal')

        self._organizer: AppOrganizer = AppOrganizer(master=self._paned_window,
                                                     application=self,
                                                     controller=self._controller,
                                                     text='Organizer')
        self._organizer.pack(side='left', fill='y')
        self._organizer.context_menu.on_refresh.append(self.refresh)

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
        Additionally, append the message to this application's log text file.

        Arguments
        ----------
        message: :type:`str`
            Message to be sent to this :class:`Application`'s log frame and to be appended to the log text file.
        """
        try:
            with open(self.user_log_file, 'a', encoding='utf-8') as log_file:
                log_file.write(f'{message}\n')
        except IOError as e:
            print(f'Error writing to log file {self.user_log_file}: {e}')
            return

        if not self._log_window:
            return

        self._log_window.log(message)

    def refresh(self, **_):
        if not self.organizer:
            return

        self.logger.info('Refreshing application gui...')
        self.clear_organizer()
        self.clear_workspace()
        if self.controller:
            self._organizer.tree.populate_tree('', self.controller)
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

        self._registered_frames.append(frame)
        self.menu.view.add_command(label=frame.name, command=lambda: self._raise_frame(frame))
        if raise_:
            self._raise_frame(frame)
        frame.on_destroy.append(lambda: self.unregister_frame(frame))

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

        # create a copy of the controller's metadata
        # because we don't want to modify the original controller's metadata
        write_dict = copy.deepcopy(self.controller.root_meta_data)
        remove_none_values_inplace(write_dict)
        dict_to_xml_file(write_dict,
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

        if frame not in self._registered_frames:
            self.logger.warning(f'Frame {frame.name} is not registered in this application.')
            return

        self._registered_frames.remove(frame)
        self.menu.view.delete(frame.name)
        if len(self._registered_frames) != 0:
            self._raise_frame(self._registered_frames[0])


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
