from __future__ import annotations

import copy
import importlib
import os

from typing import Any, Callable, Optional, Union
import tkinter as tk
from tkinter import ttk

from pyrox.services.env import get_env, set_env
from pyrox.services.logging import LoggingManager, log

from .. import models
from ..services.dict import remove_none_values_inplace
from ..services.plc import dict_to_xml_file, l5x_dict_from_file


ENV_LAST_OPEN_L5X = 'PLC_LAST_OPEN_L5X'


__all__ = [
    'App',
    'AppTask',
]


class AppOrganizerContextMenu(models.ContextMenu):
    """Context menu for the organizer window.

    This class extends `ContextMenu` to provide a context menu specific to the organizer window.
    It can be used to add, remove, or manage tasks and other elements in the organizer.
    """

    def __init__(
        self,
        master: Optional[Any] = None,
        app: Optional[App] = None,
    ) -> None:
        super().__init__(master=master)
        self._app = app
        self.on_refresh: list[Callable] = []

    @property
    def app(self) -> Optional[App]:
        """The application associated with this context menu.

        .. ------------------------------------------------------------

        Returns
        -----------
            app: Optional[:class:`App`]
        """
        return self._app

    @property
    def _default_menu_items(self) -> list[models.MenuItem]:
        """Default menu items for the organizer context menu."""
        return [
            models.MenuItem(label='Refresh',
                            command=self._on_refresh),
        ]

    def _get_clicked_object(
        self,
        hash_item: Optional[Union[list, models.HashList, dict, models.PlcGuiObject]] = None,
        lookup_attribute: Optional[Union[str, int]] = None
    ) -> Optional[Any]:
        """Get the object that was clicked on in the context menu."""
        if isinstance(hash_item, (list, models.HashList)):
            if not isinstance(lookup_attribute, int):
                log(self).error('Lookup attribute must be an integer for list or HashList types.')
                return None
            return hash_item[lookup_attribute]

        if isinstance(hash_item, dict):
            return hash_item.get(lookup_attribute, None)

        if isinstance(hash_item, models.PlcGuiObject):
            if not isinstance(lookup_attribute, str):
                log(self).error('Lookup attribute must be a string for PlcGuiObject types.')
                return None
            return getattr(hash_item, lookup_attribute, None)

        log(self).error('Unable to determine clicked object from provided hash_item and lookup_attribute.')
        return None

    def _on_modify_plc_object(
        self,
        item: Optional[str] = None,
        plc_object: Optional[models.plc.PlcObject] = None
    ) -> None:
        """Handle the modification of a PlcObject in the context menu."""
        if self.app is None:
            log(self).error('No application associated with this context menu.')
            return

        if plc_object is None:
            log(self).error('No PlcObject provided to modify.')
            return

        frame = models.ObjectEditTaskFrame(
            master=self.app.workspace,
            object_=plc_object,
            properties=models.PlcGuiObject.from_data(plc_object).gui_interface_attributes()
        )
        self.app.register_frame(frame, raise_=True)

    def _on_edit_routine(
        self,
        routine: models.plc.Routine
    ) -> None:
        if self.app is None:
            log(self).error('No application associated with this context menu.')
            return

        ladder_frame = models.LadderEditorTaskFrame(
            master=self.app.workspace,
            controller=self.app.controller,
            routine=routine
        )
        self.app.register_frame(ladder_frame, raise_=True)

    def _on_refresh(self):
        [x() for x in self.on_refresh if callable(x)]

    def compile_menu_from_item(
        self,
        event: tk.Event,
        treeview_item: str,
        hash_item: Any,
        lookup_attribute: str
    ) -> list[models.MenuItem]:
        menu_list = self._default_menu_items

        if None in [treeview_item, hash_item, lookup_attribute]:
            return menu_list

        clicked_obj = self._get_clicked_object(hash_item, lookup_attribute)
        if not clicked_obj:
            if hasattr(self.master, 'tree'):
                tree: models.gui.meta.PyroxTreeview = self.master.tree
            else:
                return menu_list

            if not isinstance(self.master.tree, models.gui.meta.PyroxTreeview):
                return menu_list

            clicked_obj_parent = self.master.tree.parent(treeview_item)
            if not clicked_obj_parent:
                return menu_list
            return self.master.tree.on_right_click(event=event,
                                                   treeview_item=clicked_obj_parent,)
        plc_obj = None

        if isinstance(hash_item, (list, models.HashList)):
            if not isinstance(lookup_attribute, int):
                return menu_list
            clicked_obj = hash_item[lookup_attribute]

        elif isinstance(hash_item, dict):
            clicked_obj = hash_item.get(lookup_attribute, None)
        elif isinstance(hash_item, models.PlcGuiObject):
            clicked_obj = getattr(hash_item, lookup_attribute, None)
        else:
            pass

        if isinstance(hash_item, models.PyroxGuiObject):
            plc_obj = clicked_obj if isinstance(clicked_obj, models.plc.PlcObject) else hash_item.pyrox_object
        elif isinstance(clicked_obj, models.plc.PlcObject):
            plc_obj = clicked_obj

        if isinstance(plc_obj, models.plc.PlcObject):
            menu_list.insert(0, models.MenuItem(label='Modify',
                                                command=lambda: self._on_modify_plc_object(item=hash_item, plc_object=plc_obj)))

        if isinstance(plc_obj, models.plc.Program) and plc_obj.controller:
            menu_list.insert(0, models.MenuItem(label='Add New Routine',
                                                command=lambda: plc_obj.add_routine(models.plc.Routine(controller=plc_obj.controller,
                                                                                                       program=plc_obj))))

        if isinstance(plc_obj, models.plc.Routine):
            menu_list.insert(0, models.MenuItem(label='Edit Routine',
                                                command=lambda: self._on_edit_routine(routine=plc_obj)))

        if isinstance(plc_obj, models.plc.TagEndpoint):
            task: 'AppTask' = self._app.tasks.get('PlcIoTask')
            if task and task.running:
                menu_list.insert(0, models.MenuItem(label='Insert to Watch Table',
                                                    command=lambda x=plc_obj: task.add_tag_to_watch_table(x.name)))

        return menu_list


class AppOrganizer(models.PyroxObject):
    """Application orgranizer class.
    """

    def __init__(
        self,
        application: Optional[App] = None,
    ) -> None:
        super().__init__()
        self._application: Optional[App] = application
        self._window: models.OrganizerWindow = None

        self._raw_l5x_frame: Optional[models.FrameWithTreeViewAndScrollbar] = None
        self._program_frame: Optional[models.FrameWithTreeViewAndScrollbar] = None

    @property
    def application(self) -> Optional[App]:
        """Application associated with this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Optional[:class:`App`]
        """
        return self._application

    def _build_organizer_programs_tab(self) -> None:
        cm = AppOrganizerContextMenu(
            master=self._window._notebook,
            app=self.application
        )
        cm.on_refresh.append(self.application.refresh)

        self._program_frame = models.FrameWithTreeViewAndScrollbar(
            master=self._window._notebook,
            base_gui_class=models.PlcGuiObject,
            context_menu=cm,
        )
        self._program_frame.pack(fill=tk.BOTH, expand=True)

        self._window.register_tab(
            frame=self._program_frame,
            text='PLC\nProg',
        )

    def _build_organizer_raw_tab(self) -> None:
        cm = AppOrganizerContextMenu(
            master=self._window._notebook,
            app=self.application
        )
        cm.on_refresh.append(self.application.refresh)

        self._raw_l5x_frame = models.FrameWithTreeViewAndScrollbar(
            master=self._window._notebook,
            base_gui_class=models.PlcGuiObject,
            context_menu=cm,
        )
        self._raw_l5x_frame.pack(fill=tk.BOTH, expand=True)

        self._window.register_tab(
            frame=self._raw_l5x_frame,
            text='Raw\nL5X',
        )

    def _build_standard_program_dict(self, program: models.plc.Program) -> dict:
        """Build a dictionary of standard programs for the organizer."""
        d = {
            'name': program.name,
        }
        for routine in program.routines:
            d[routine.name] = routine
        return d

    def _populate_prog_tab(self, controller: models.plc.Controller) -> None:
        if not controller:
            log(self).debug('No controller provided to populate programs tab.')
            return
        log(self).debug('Populating programs tab with controller data.')
        self._program_frame.tree.populate_tree('', {
            'Standard': [self._build_standard_program_dict(program) for program in controller.standard_programs],
            'Safety': [self._build_standard_program_dict(program) for program in controller.safety_programs]}
        )

    def _populate_raw_tab(self, controller: models.plc.Controller) -> None:
        log(self).debug('Populating raw tab with controller data.')
        self._raw_l5x_frame.tree.populate_tree('', controller)

    def build(
        self,
        master: tk.Widget
    ) -> models.OrganizerWindow:
        self._window = models.OrganizerWindow(master=master)
        self._window.pack(side=tk.LEFT, fill=tk.Y)
        self._build_organizer_raw_tab()
        self._build_organizer_programs_tab()
        return self._window

    def clear_organizer(self) -> None:
        """Clear organizer of all children.

        This method will remove all children from the organizer window, if it exists.
        """
        log(self).debug('Clearing organizer of all children.')
        self._raw_l5x_frame.tree.delete(*self._raw_l5x_frame.tree.get_children())
        self._program_frame.tree.delete(*self._program_frame.tree.get_children())

    def populate_organizer(self,
                           controller: models.plc.Controller) -> None:
        """Populate the organizer with the provided controller.

        This method will populate the organizer with the provided controller's data.
        It will clear the existing data and add the new data from the controller.

        .. ------------------------------------------------------------

        Arguments
        -----------
        controller: :class:`Controller`
            The controller to populate the organizer with.
        """
        self._populate_raw_tab(controller)
        self._populate_prog_tab(controller)


class App(models.Application):
    """App class for Pyrox.
    This extends a basic 'engine' application into a useful class to run our plc functions
    """

    def __init__(self, config: models.ApplicationConfiguration) -> None:
        super().__init__(config=config)

        self._controller = None
        self._organizer: Optional[AppOrganizer] = None
        self._log_window: Optional[models.LogFrame] = None
        self._main_paned_window: Optional[tk.PanedWindow] = None
        self._sub_paned_window: Optional[tk.PanedWindow] = None
        self._registered_frames: models.HashList[models.TaskFrame] = models.HashList('name')
        self._workspace: Optional[models.PyroxFrame] = None

        self._organizer_visible = True
        self._organizer_width = 300

    @property
    def controller(self) -> Optional[models.plc.Controller]:
        """Allen Bradley L5X Controller Object associated with this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller`]
        """
        return self._controller

    @controller.setter
    def controller(
        self,
        value: Optional[models.plc.Controller]
    ) -> None:
        if not isinstance(value, models.plc.Controller) and value is not None:
            raise TypeError(f'Expected Controller, got {type(value)}')
        self._controller = value
        if value:
            if self.refresh not in value.on_compiled:
                value.on_compiled.append(self.refresh)
            if self.set_app_state_busy not in value.on_compiling:
                value.on_compiling.append(self.set_app_state_busy)
            if value.file_location is not None:
                set_env(ENV_LAST_OPEN_L5X, value.file_location)
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
    def workspace(self) -> Optional[models.PyroxFrame]:
        """The workspace window for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            workspace: :class:`LabelFrame`
        """
        return self._workspace

    def _build_and_pack_main_paned_window(self) -> None:
        self._main_paned_window.add(self._sub_paned_window)
        self._main_paned_window.pack(fill='both', expand=True)

    def _build_and_pack_sub_paned_window(self) -> None:
        self._sub_paned_window.pack(fill='both', expand=True)

    def _build_log_window(self) -> None:
        if not self._sub_paned_window:
            raise RuntimeError('Sub paned window must be built before log window.')

        self._log_window = models.LogFrame(self.frame)
        self._log_window.pack(fill='both', expand=True)
        self._sub_paned_window.add(self._log_window)

        for stream in [LoggingManager._captured_stdout, LoggingManager._captured_stderr]:
            if stream:
                for line in stream.get_lines():
                    if 'WARNING' in line or 'ERROR' in line or 'CRITICAL' in line:
                        self._log_window.log(line)

    def _build_organizer(self) -> None:
        self._organizer: AppOrganizer = AppOrganizer(application=self)
        frame = self._organizer.build(master=self._main_paned_window)
        self._main_paned_window.add(frame)

    def _build_tasks(self) -> None:
        models.ApplicationTaskFactory.build_tasks(self)

    def _build_workspace(self) -> None:
        self._workspace = models.PyroxFrame(
            self._sub_paned_window,
            height=500,
        )
        self._workspace.pack(side='top', fill='x')
        self._sub_paned_window.add(self._workspace)

    def _config_menu_file_entries(self) -> None:
        """Configure the file menu entries based on the controller state."""
        log(self).debug('Configuring file menu entries based on controller state.')
        self._menu.file.entryconfig('Save L5X', state='disabled' if not self.controller else 'normal')
        self._menu.file.entryconfig('Save L5X As...', state='disabled' if not self.controller else 'normal')
        self._menu.file.entryconfig('Close L5X', state='disabled' if not self.controller else 'normal')

    def _load_controller(
        self,
        file_location: str
    ) -> models.plc.Controller:
        """ Attempt to load a :class:`Controller` from a provided .L5X Allen Bradley PLC File.

        Args:
            file_location (str): Location to open :class:`Controller

        Returns:
            :class:`Controller`: Loaded controller instance.

        Raises:
            ValueError: If the controller fails to load from the file.
        """
        importlib.reload(models.plc)
        ctrl = models.plc.Controller.from_file(file_location)
        if not ctrl:
            raise ValueError(f'Failed to load controller from file: {file_location}')
        return ctrl

    def _load_last_opened_controller(self) -> None:
        file = get_env(ENV_LAST_OPEN_L5X, default=None, cast_type=str)
        if file and os.path.isfile(file):
            self.load_controller(file)
        else:
            set_env(ENV_LAST_OPEN_L5X, '')

    def _raise_frame(self,
                     frame: models.TaskFrame) -> None:
        """Raise a frame to the top of the application."""
        self.clear_workspace()
        if not frame or not frame.winfo_exists():
            self.unregister_frame(frame)
            log(self).error('Frame does not exist or is not provided.')
            return
        if frame.name not in self._registered_frames:
            log(self).error(f'Frame {frame.name} is not registered in this application.')
            self.register_frame(frame, raise_=False)
        frame.master = self.workspace
        frame.pack(fill='both', expand=True, side='top')
        self._set_frame_selected(frame)

    def _set_app_title(self) -> None:
        """Set the application title based on the controller name and file location."""
        if self.controller:
            self._tk_app.title(f'{self.config.title} - [{self.controller.name}] - [{self.controller.file_location}]')
        else:
            self._tk_app.title(self.config.title)

    def _set_frame_selected(self, frame):
        """Set the selected frame in the view menubar."""
        self._unset_frames_selected()
        frame.shown_var.set(True)

    def _setup_keybinds(
        self
    ) -> None:
        """Setup keybinds for the application."""
        self._tk_app.bind('<Control-b>', self.toggle_organizer)

    def _transform_controller(self,
                              controller: models.plc.Controller,
                              sub_class: Optional[type[models.plc.Controller]] = None) -> models.plc.Controller:
        """Transform a controller to a specific subclass.
        This method will transform a controller to a specific subclass if provided.
        .. ------------------------------------------------------------
        .. arguments::
        :class:`Controller` controller:
            The controller to transform.
        :class:`type[Controller]` sub_class:
            The subclass to transform the controller to.
        .. -------------------------------------------------------------
        .. returns::
        :class:`Controller`:
            The transformed controller instance.
        """
        try:
            self.set_app_state_busy()
            if not sub_class:
                return controller
            if not issubclass(sub_class, models.plc.Controller):
                raise TypeError(f'Subclass must be a Controller subclass, got {sub_class}')
            if isinstance(controller, sub_class):
                return controller
            if not isinstance(controller, models.plc.Controller):
                raise TypeError(f'Controller must be a Controller instance, got {type(controller)}')
            if not controller.meta_data:
                raise ValueError('Controller must have root_meta_data to transform.')
            transformed_ctrl = sub_class.from_meta_data(controller.meta_data)
            transformed_ctrl.file_location = controller.file_location
            return transformed_ctrl
        finally:
            self.set_app_state_normal()

    def _unset_frames_selected(self):
        """Unset all frames in the view menubar."""
        [frame.shown_var.set(False) for frame in self._registered_frames]

    def build(self):
        super().build()
        self._main_paned_window = ttk.PanedWindow(self.frame, orient='horizontal')
        self._sub_paned_window = ttk.PanedWindow(self._main_paned_window, orient='vertical')
        self._build_organizer()
        self._build_workspace()
        self._build_log_window()
        self._build_and_pack_sub_paned_window()
        self._build_and_pack_main_paned_window()
        self._build_tasks()
        self._setup_keybinds()
        self._load_last_opened_controller()

    def clear_organizer(self) -> None:
        """Clear organizer of all children.

        This method will remove all children from the organizer window, if it exists.

        """
        if not self.organizer:
            return

        self.organizer.clear_organizer()

    def clear_workspace(self) -> None:
        """Clear workspace of all children.
        """
        if not self.workspace:
            return
        log(self).debug('Clearing workspace of all children.')

        for child in self.workspace.winfo_children():
            child.pack_forget()
        self._unset_frames_selected()

    def load_controller(
        self,
        file_location: str
    ) -> None:
        """Attempt to load a :class:`Controller` from a provided .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to open :class:`Controller` from.

        """
        self.set_app_state_busy()
        try:
            log(self).info('Loading ctrl from file: %s', file_location)
            ctrl = self._load_controller(file_location)
            if ctrl is None:
                log(self).error('Failed to load controller from file: %s', file_location)
                return

            log(self).info('new ctrl loaded -> %s', ctrl.name)
            self.controller = ctrl
        finally:
            self.set_app_state_normal()

    def application_log(
        self,
            message: str
    ) -> None:
        """Log a message to the log window.

        .. ------------------------------------------------------------

        Arguments
        -----------
        message: :type:`str`
            The message to log.

        """
        if self._log_window:
            self._log_window.log(message)

    def new_controller(self) -> None:
        """Create a new controller instance."""
        log(self).info('Creating new controller instance...')
        ctrl = models.plc.Controller(l5x_dict_from_file(models.plc.BASE_FILES[0]))
        log(self).info('New controller instance created: %s', ctrl.name)
        self.controller = ctrl
        log(self).info('Controller instance set successfully.')

    def refresh(self) -> None:
        if not self.organizer:
            return

        log(self).info('Refreshing application gui...')
        self.set_app_state_busy()
        self.clear_organizer()
        self.clear_workspace()
        self._set_app_title()
        self._organizer.populate_organizer(self.controller)
        self._config_menu_file_entries()
        self.set_app_state_normal()
        log(self).info('Done!')

    def register_frame(self,
                       frame: models.TaskFrame,
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

        if not isinstance(frame, models.TaskFrame):
            raise TypeError(f'Expected TaskFrame, got {type(frame)}')

        if frame.name in self._registered_frames:
            if raise_:
                self._raise_frame(frame)
            return

        self._registered_frames.append(frame)
        self.menu.view.add_checkbutton(label=frame.name,
                                       variable=frame.shown_var,
                                       command=lambda: self._raise_frame(frame))
        if raise_:
            self._raise_frame(frame)
        frame.on_destroy.append(lambda: self.unregister_frame(frame))

    def save_controller(self,
                        file_location: Optional[str] = None) -> None:
        """Save a :class:`Controller` back to a .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to save :class:`Controller` to.

        """
        file_location = file_location or self.controller.file_location

        if not file_location or not self.controller:
            return

        if not file_location.endswith('.L5X'):
            file_location += '.L5X'

        try:
            self.set_app_state_busy()
            self.controller.file_location = file_location
            log(self).info('Saving controller to file: %s', file_location)
            # create a copy of the controller's metadata
            # because we don't want to modify the original controller's metadata
            write_dict = copy.deepcopy(self.controller.meta_data)
            remove_none_values_inplace(write_dict)
            dict_to_xml_file(write_dict,
                             file_location)
            self.controller = self.controller  # reassign to update gui and other references
            log(self).info('Controller saved successfully to: %s', file_location)
        finally:
            self.set_app_state_normal()

    def set_frame(self,
                  frame: models.TaskFrame) -> None:
        """Set a frame to the top of the application.

        This method will raise the provided frame to the top of the application.

        .. ------------------------------------------------------------

        Arguments
        -----------
        frame: :class:`TaskFrame`
            The frame to set to the top of the application.

        """
        self._raise_frame(frame)

    def toggle_organizer(
        self,
        *_,
    ) -> None:
        """Toggle the visibility of the organizer panel."""
        if not self._main_paned_window or not self._organizer:
            return

        if self._organizer_visible:
            # Hide organizer
            self._organizer_width = self._organizer.winfo_width()  # Store current width
            self._main_paned_window.forget(self._organizer)  # Remove from paned window
            self._organizer_visible = False
            log(self).info('Organizer hidden')
        else:
            # Show organizer
            self._main_paned_window.add(self._organizer, before=self._main_paned_window.panes()[0] if self._main_paned_window.panes() else None)
            # Restore the saved width
            self._main_paned_window.paneconfigure(self._organizer, width=self._organizer_width)
            self._organizer_visible = True
            log(self).info('Organizer shown')

    def unregister_frame(self,
                         frame: models.TaskFrame) -> None:
        """Unregister a frame from this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------
        frame: :class:`Frame`
            The frame to unregister from this :class:`Application`.

        """
        if not frame:
            raise ValueError('Frame must be provided to unregister a frame.')

        if not isinstance(frame, models.TaskFrame):
            raise TypeError(f'Expected TaskFrame, got {type(frame)}')

        # Safely remove from menu (menu might be destroyed during app shutdown)
        try:
            if hasattr(self, 'menu') and self.menu and hasattr(self.menu, 'view'):
                self.menu.view.delete(frame.name)
        except (tk.TclError, AttributeError) as e:
            log(self).debug(f'Could not remove menu item for {frame.name}: {e}')

        if frame.name not in self._registered_frames:
            log(self).warning(f'Frame {frame.name} is not registered in this application.')
            return

        self._registered_frames.remove(frame)
        if len(self._registered_frames) != 0:
            try:
                self._raise_frame(self._registered_frames[0])
            except (tk.TclError, AttributeError) as e:
                log(self).debug(f'Could not raise frame during unregistration: {e}')


class AppTask(models.ApplicationTask):

    def __init__(
        self,
        application
    ) -> None:
        super().__init__(application)

    @property
    def controller(self) -> Optional[models.plc.Controller]:
        """Controller instance associated with this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller]
        """
        return getattr(self.application, 'controller', None)

    def inject(self) -> None:
        """Inject this task into the application.
        """
        ...
