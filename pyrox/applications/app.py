from __future__ import annotations

import copy
import importlib
import os

from typing import Any, Optional
from tkinter import Event, PanedWindow


from ..models import Application, ApplicationTask, HashList
from ..models import plc
from .general_motors.gm import GmController
from ..models.gui import ladder as ladder_gui
from ..models.gui import (
    ContextMenu,
    FrameWithTreeViewAndScrollbar,
    LogWindow,
    MenuItem,
    ObjectEditTaskFrame,
    PyroxFrame,
    PyroxGuiObject,
    TaskFrame,
)
from ..models.gui.plc import PlcGuiObject

from ..services.dictionary_services import remove_none_values_inplace
from ..services.plc_services import dict_to_xml_file, l5x_dict_from_file


class AppOrganizerContextMenu(ContextMenu):
    """Context menu for the organizer window.

    This class extends `ContextMenu` to provide a context menu specific to the organizer window.
    It can be used to add, remove, or manage tasks and other elements in the organizer.
    """

    def __init__(self,
                 controller: Optional[plc.Controller] = None,
                 parent: AppOrganizer = None,
                 **kwargs):
        super().__init__(tearoff=0,
                         **kwargs)
        self._controller: Optional[plc.Controller] = controller
        self._parent: Optional[AppOrganizer] = parent
        self.logger.info('Organizer context menu initialized.')
        self.on_refresh: list[callable] = []

    @property
    def _default_menu_items(self) -> list[MenuItem]:
        """Default menu items for the organizer context menu."""
        return [
            MenuItem(label='Refresh',
                     command=self._on_refresh),
        ]

    def _on_modify_plc_object(self,
                              item: str = None,
                              plc_object: plc.PlcObject = None) -> None:
        """Handle the modification of a PlcObject in the context menu."""
        frame = ObjectEditTaskFrame(master=self._parent.application.workspace,
                                    object_=plc_object,
                                    properties=PlcGuiObject.from_data(plc_object).gui_interface_attributes())
        self._parent.application.register_frame(frame, raise_=True)

    def _on_edit_routine(self,
                         routine: plc.Routine):
        importlib.reload(ladder_gui)
        ladder_frame = ladder_gui.LadderEditorTaskFrame(
            master=self._parent.application.workspace,
            controller=self._parent.application.controller,
            routine=routine)
        self._parent.application.register_frame(ladder_frame, raise_=True)

    def _on_refresh(self):
        [x() for x in self.on_refresh if callable(x)]

    def compile_menu_from_item(self,
                               event: Event,
                               treeview_item: str,
                               hash_item: Any,
                               lookup_attribute: str) -> list[MenuItem]:
        menu_list = self._default_menu_items

        if None in [treeview_item, hash_item, lookup_attribute]:
            return menu_list

        clicked_obj = None
        plc_obj = None

        if isinstance(hash_item, (list, HashList)):
            clicked_obj = hash_item[lookup_attribute]
        elif isinstance(hash_item, dict):
            clicked_obj = hash_item.get(lookup_attribute, None)
        elif isinstance(hash_item, PlcGuiObject):
            clicked_obj = getattr(hash_item, lookup_attribute, None)
        else:
            clicked_obj_parent = self._parent.tree.parent(treeview_item)
            if not clicked_obj_parent:
                return menu_list
            return self._parent.tree.on_right_click(event=event,
                                                    treeview_item=clicked_obj_parent,)

        if isinstance(hash_item, PyroxGuiObject):
            plc_obj = clicked_obj if isinstance(clicked_obj, plc.PlcObject) else hash_item.pyrox_object
        elif isinstance(clicked_obj, plc.PlcObject):
            plc_obj = clicked_obj

        if isinstance(plc_obj, plc.PlcObject):
            menu_list.insert(0, MenuItem(label='Modify',
                                         command=lambda: self._on_modify_plc_object(item=hash_item, plc_object=plc_obj)))

        if isinstance(plc_obj, plc.Routine):
            menu_list.insert(0, MenuItem(label='Edit Routine',
                                         command=lambda: self._on_edit_routine(routine=plc_obj)))

        if isinstance(plc_obj, plc.TagEndpoint):
            task: 'AppTask' = self._parent.application.tasks.get('PlcIoTask')
            if task and task.running:
                menu_list.insert(0, MenuItem(label='Insert to Watch Table',
                                             command=lambda x=plc_obj: task.add_tag_to_watch_table(x.name)))

        return menu_list


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

    def __init__(self,
                 *args,
                 application: Optional[App] = None,
                 controller: Optional[plc.Controller] = None,
                 **kwargs):
        super().__init__(*args,
                         context_menu=AppOrganizerContextMenu(controller=controller,
                                                              parent=self),
                         **kwargs)
        self._application: Optional[App] = application
        self._controller: Optional[plc.Controller] = controller
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
    def context_menu(self) -> AppOrganizerContextMenu:
        """Context menu for this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            context_menu: :class:`OrganizerContextMenu`
        """
        return self.tree.context_menu

    @property
    def controller(self) -> Optional[plc.Controller]:
        """Controller associated with this organizer.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller`]
        """
        return self._controller


class App(Application):
    """Application class for Pyrox.

    This class is used to create and manage the application instance.
    It inherits from the `Application` model and provides additional
    functionality specific to the Pyrox framework.
    """

    def __init__(self,
                 *args,
                 **kwargs):
        super().__init__(*args,
                         add_to_globals=True,
                         **kwargs)

        self._controller: Optional[plc.Controller] = None
        self._organizer: Optional[AppOrganizer] = None
        self._log_window: Optional[LogWindow] = None
        self._paned_window: Optional[PanedWindow] = None
        self._registered_frames: HashList[TaskFrame] = HashList('name')
        self._workspace: Optional[PyroxFrame] = None
        self.logger.info('Pyrox Application initialized.')

    @property
    def controller(self) -> Optional[plc.Controller]:
        """Allen Bradley L5X Controller Object associated with this :class:`Model`.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller`]
        """
        return self._controller

    @controller.setter
    def controller(self,
                   value: plc.Controller):
        if not isinstance(value, plc.Controller) and value is not None:
            raise TypeError(f'Expected Controller, got {type(value)}')
        self._controller = value
        if self._controller:
            if self.refresh not in self._controller.on_compiled:
                self._controller.on_compiled.append(self.refresh)
            if self.set_app_state_busy not in self._controller.on_compiling:
                self._controller.on_compiling.append(self.set_app_state_busy)
        self._runtime_info.data['last_plc_file_location'] = value.file_location if value else None
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

    def _load_controller(self,
                         file_location: str) -> plc.Controller:
        """Load a controller from a file location.
        This private method also manages the ux of loading a controller.
        .. ------------------------------------------------------------
        .. arguments::
        :class:`str` file_location:
            The file location to load the controller from.
        .. -------------------------------------------------------------
        .. returns::
        :class:`Controller`:
            The loaded controller instance.
        """
        self.set_app_state_busy()
        self.logger.info('Loading controller from file: %s', file_location)
        try:
            return plc.Controller(l5x_dict_from_file(file_location))
        except KeyError as e:
            self.logger.error('error parsing controller from file %s: %s', file_location, e)
        finally:
            self.set_app_state_normal()

    def _raise_frame(self,
                     frame: TaskFrame) -> None:
        """Raise a frame to the top of the application."""
        self.clear_workspace()
        if not frame or not frame.winfo_exists():
            self.unregister_frame(frame)
            self.logger.error('Frame does not exist or is not provided.')
            return
        if frame.name not in self._registered_frames:
            self.logger.error(f'Frame {frame.name} is not registered in this application.')
            self.register_frame(frame, raise_=False)
        frame.master = self.workspace
        frame.pack(fill='both', expand=True, side='top')
        self._set_frame_selected(frame)

    def _set_frame_selected(self, frame):
        """Set the selected frame in the view menubar."""
        self._unset_frames_selected()
        frame.shown_var.set(True)

    def _transform_controller(self,
                              controller: plc.Controller,
                              sub_class: Optional[type[plc.Controller]] = None) -> plc.Controller:
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
            if not issubclass(sub_class, plc.Controller):
                raise TypeError(f'Subclass must be a Controller subclass, got {sub_class}')
            if isinstance(controller, sub_class):
                return controller
            if not isinstance(controller, plc.Controller):
                raise TypeError(f'Controller must be a Controller instance, got {type(controller)}')
            if not controller.root_meta_data:
                raise ValueError('Controller must have root_meta_data to transform.')
            transformed_ctrl = sub_class.from_meta_data(controller.root_meta_data)
            transformed_ctrl.file_location = controller.file_location
            return transformed_ctrl
        finally:
            self.set_app_state_normal()

    def _unset_frames_selected(self):
        """Unset all frames in the view menubar."""
        [frame.shown_var.set(False) for frame in self._registered_frames]

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

        sub_frame.add(self._log_window)
        sub_frame.pack(fill='both', expand=True)
        sub_frame.configure(sashrelief='groove', sashwidth=5, sashpad=5)

        self._paned_window.add(sub_frame)
        self._paned_window.pack(fill='both', expand=True)
        self._paned_window.configure(sashrelief='groove', sashwidth=5, sashpad=5)

        last_plc_file_location = self._runtime_info.data.get('last_plc_file_location', None)
        if last_plc_file_location and os.path.isfile(last_plc_file_location):
            self.load_controller(last_plc_file_location)
            return
        self.refresh()

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
        self._unset_frames_selected()

    def load_controller(self,
                        file_location: str) -> None:
        """Attempt to load a :class:`Controller` from a provided .L5X Allen Bradley PLC File.

        .. ------------------------------------------------------------

        Arguments
        -----------
        file_location: :type:`str`
            Location to open :class:`Controller` from.

        """
        ctrl = self._load_controller(file_location)
        if not ctrl:
            self.logger.error('Failed to load controller from file: %s', file_location)
            return
        self.logger.info('new ctrl loaded -> %s', ctrl.name)

        # General Motors PLC detection
        if 'zz_Version' in ctrl.datatypes:
            ctrl = self._transform_controller(ctrl, GmController)
            if not ctrl:
                self.logger.error('Failed to transform controller to GmController.')
                return
            self.logger.info('Loaded GmController from metadata: %s', ctrl.name)

        ctrl.file_location = file_location
        self.controller = ctrl

    def log(self,
            message: str) -> None:
        super().log(message)
        if not self._log_window:
            return
        self._log_window.log(message)

    def new_controller(self) -> None:
        """Create a new controller instance."""
        self.logger.info('Creating new controller instance...')
        ctrl = plc.Controller(l5x_dict_from_file(plc.BASE_FILES[0]))
        self.logger.info('New controller instance created: %s', ctrl.name)
        self.controller = ctrl
        self.logger.info('Controller instance set successfully.')

    def refresh(self) -> None:
        if not self.organizer:
            return

        self.logger.info('Refreshing application gui...')
        self.clear_organizer()
        self.clear_workspace()
        if self.controller:
            self._tk_app.title(f'{self.config.title} - [{self.controller.name}] - [{self.controller.file_location}]')
            self._organizer.tree.populate_tree('', self.controller)
        else:
            self._tk_app.title(self.config.title)
        self._menu.file.entryconfig('Save L5X', state='disabled' if not self.controller else 'normal')
        self._menu.file.entryconfig('Save L5X As...', state='disabled' if not self.controller else 'normal')
        self._menu.file.entryconfig('Close L5X', state='disabled' if not self.controller else 'normal')
        self.set_app_state_normal()
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

        try:
            self.set_app_state_busy()
            self.controller.file_location = file_location
            self.logger.info('Saving controller to file: %s', file_location)
            # create a copy of the controller's metadata
            # because we don't want to modify the original controller's metadata
            write_dict = copy.deepcopy(self.controller.root_meta_data)
            remove_none_values_inplace(write_dict)
            dict_to_xml_file(write_dict,
                             file_location)
            self.controller = self.controller  # reassign to update gui and other references
            self.logger.info('Controller saved successfully to: %s', file_location)
        finally:
            self.set_app_state_normal()

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

        if frame.name not in self._registered_frames:
            self.logger.warning(f'Frame {frame.name} is not registered in this application.')
            return

        self._registered_frames.remove(frame)
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

    @property
    def controller(self) -> Optional[plc.Controller]:
        """Controller instance associated with this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            controller: Optional[:class:`Controller]
        """
        return self.application.controller if self.application else None
