"""
Workspace Widget for Pyrox applications with VSCode-like layout.

This module provides a workspace widget that mimics the VSCode interface with:
- Left sidebar organizer (PyroxNotebook) for navigation and tools
- Main workspace area for content
- Resizable panes with splitter
- Dynamic widget mounting and management
- Configurable sidebar visibility and positioning
"""
import tkinter as tk
from tkinter import ttk, TclError
from typing import Dict, List, Optional, Callable, Any
from pyrox.models.gui.logframe import LogFrame
from pyrox.models.gui.frame import PyroxFrameContainer
from pyrox.models.gui.notebook import PyroxNotebook
from pyrox.models.gui.tk.frame import TkinterGuiFrame

from pyrox.interfaces import (
    EnvironmentKeys,
    IGuiFrame,
    IGuiWindow,
    IWorkspace,
    ITaskFrame
)


class TkWorkspace(
    IWorkspace,
    TkinterGuiFrame
):
    """
    A VSCode-like workspace widget with sidebar organizer and main content area.

    Features:
    - Left sidebar with PyroxNotebook organizer
    - Resizable main workspace area
    - Dynamic widget mounting/unmounting
    - Sidebar visibility toggle
    - Multiple workspace layouts
    - Event callbacks for workspace operations
    - Built-in status bar support
    - Configurable splitter positions
    """

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
    ) -> None:
        TkinterGuiFrame.__init__(
            self,
            name="PyroxWorkspace",
            description="A VSCode-like workspace widget with sidebar organizer and main content area.",
        )
        self.initialize(
            name="pyroxWorkspace",
            master=master
        )
        self.root.pack(fill='both', expand=True)

        self._main_paned_window = None
        self._log_paned_window = None
        self._sidebar_organizer = None
        self._workspace_area = None
        self._status_bar = None
        self._status_label = None

        self._panes: List[tk.Widget] = []

        # Widget tracking
        self._mounted_widgets: Dict[str, tk.Widget] = {}
        self._sidebar_tabs: Dict[str, str] = {}  # widget_id -> tab_id mapping
        self._workspace_frames: Dict[str, ITaskFrame] = {}

        # Event callbacks
        self.on_sidebar_toggle: Optional[Callable[[bool], None]] = None
        self.on_task_frame_mounted: Optional[Callable[[ITaskFrame, str], None]] = None
        self.on_task_frame_unmounted: Optional[Callable[[ITaskFrame], None]] = None
        self.on_sidebar_widget_mounted: Optional[Callable[[tk.Widget, str], None]] = None
        self.on_sidebar_widget_unmounted: Optional[Callable[[str], None]] = None
        self.on_workspace_changed: Optional[Callable[[str], None]] = None

        # Status tracking
        self._status_text = tk.StringVar()

        # Callback tracking
        self._sash_callbacks: List[Callable] = []

    @property
    def log_paned_window(self) -> ttk.PanedWindow:
        """Get the log paned window.

        Returns:
            ttk.PanedWindow: The log paned window instance.
        """
        if not self._log_paned_window:
            raise RuntimeError("Log paned window not initialized")
        return self._log_paned_window

    @property
    def main_paned_window(self) -> ttk.PanedWindow:
        """Get the main paned window.

        Returns:
            ttk.PanedWindow: The main paned window instance.
        """
        if not self._main_paned_window:
            raise RuntimeError("Main paned window not initialized")
        return self._main_paned_window

    @property
    def menu(self) -> Any:
        """Get the main application menu.

        Returns:
            The main application menu instance.
        """
        return self.gui.unsafe_get_backend().get_root_application_menu()

    @property
    def sidebar_organizer(self) -> PyroxNotebook:
        """Get the sidebar organizer.

        Returns:
            PyroxNotebook: The sidebar organizer instance.
        """
        if not self._sidebar_organizer:
            raise RuntimeError("Sidebar organizer not initialized")
        return self._sidebar_organizer

    @property
    def status_bar(self) -> ttk.Frame:
        """Get the status bar.

        Returns:
            ttk.Frame: The status bar instance.
        """
        if not self._status_bar:
            raise RuntimeError("Status bar not initialized")
        return self._status_bar

    @property
    def status_label(self) -> ttk.Label:
        """Get the status label.

        Returns:
            ttk.Label: The status label instance.
        """
        if not self._status_label:
            raise RuntimeError("Status label not initialized")
        return self._status_label

    @property
    def window(self) -> IGuiWindow:
        """Get the main application window.

        Returns:
            The main application window instance.
        """
        return self.gui.unsafe_get_backend().get_root_gui_window()

    @property
    def workspace_area(self) -> IGuiFrame[tk.Frame, tk.Widget]:
        """Get the workspace area.

        Returns:
            PyroxFrameContainer: The workspace area instance.
        """
        if not self._workspace_area:
            raise RuntimeError("Workspace area not initialized")
        return self._workspace_area

    def _create_layout(self) -> None:
        """Create the main workspace layout."""
        self._create_status_bar()  # Pack status bar first (side='bottom')
        self._create_main_paned_window()  # Then pack main content (fill='both')
        self._create_sidebar_organizer()
        self._create_log_paned_window()
        self._create_workspace_area()
        self._create_log_window()

    def _create_log_paned_window(self) -> None:
        """Create the log paned window for layout."""
        self._log_paned_window = ttk.PanedWindow(self.main_paned_window, orient='vertical')
        self.main_paned_window.add(self.log_paned_window)

    def _create_log_window(self) -> None:
        """Create a log window at the bottom.
        """
        self.log().debug("Creating log window")
        self.log_window = LogFrame(self.log_paned_window)
        self.log_paned_window.add(self.log_window.frame.root)
        self.gui.unsafe_get_backend().schedule_event(10, self._set_initial_log_window_height)

    def _create_main_paned_window(self) -> None:
        """Create the main paned window for layout."""
        self.log().debug("Creating main paned window")
        self._main_paned_window = ttk.PanedWindow(self.root, orient='horizontal')
        self.main_paned_window.pack(fill='both', expand=True)

    def _create_sidebar_organizer(self) -> None:
        """Create the sidebar organizer."""
        self.log().debug("Creating sidebar organizer")
        self._sidebar_organizer = PyroxNotebook(
            master=self.main_paned_window,
            enable_context_menu=True,
            enable_tab_reordering=True,
            max_tabs=10
        )
        self.main_paned_window.add(self.sidebar_organizer)
        self.gui.unsafe_get_backend().schedule_event(100, self._set_initial_sidebar_width)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        self.log().debug("Creating status bar")
        self._status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')

        # Status label
        self._status_label = ttk.Label(
            self.status_bar,
            textvariable=self._status_text,
            relief='sunken',
            padding=(5, 2)
        )
        self.status_label.pack(fill='x', side='left', expand=True)

        # Add workspace info button
        info_button = ttk.Button(
            self.status_bar,
            text="ⓘ",
            width=3,
            command=self._show_workspace_info
        )
        info_button.pack(side='right', padx=(2, 5))

    def _create_workspace_area(self) -> None:
        """Create the main workspace area."""
        self.log().debug("Creating workspace area")
        self._workspace_area = self.gui.unsafe_get_backend().create_gui_frame(
            master=self.log_paned_window,
        )
        self.log_paned_window.add(self.workspace_area.root)

    def _get_shown_frame(self) -> Optional[ITaskFrame]:
        """Get the currently shown frame in the workspace.

        Returns:
            TaskFrame or None: The currently shown frame, or None if none is shown.
        """
        for frame in self._workspace_frames.values():
            if frame.shown:
                return frame
        return None

    def _hide_frames(self) -> None:
        """Hide frame from workspace area to prepare for another frame to be raised.
        """
        if not self.workspace_area:
            raise RuntimeError("Workspace area not initialized")

        for widget in self.workspace_area.root.winfo_children():
            widget.pack_forget()

    def _pack_frame_into_workspace(
        self,
        frame: ITaskFrame
    ) -> None:
        """Pack a frame into the workspace area.
        Args:
            frame (TaskFrame): The frame to pack.
        """
        if not frame or not frame.root.winfo_exists():
            raise ValueError("Frame must be a valid existing widget")

        if frame.name not in self._workspace_frames:
            raise ValueError("Frame is not registered in the workspace")

        frame.pack(in_=self.workspace_area.root, fill='both', expand=True)
        self.set_status(f"Packed frame into workspace: {frame.name}")

    def _raise_frame(
        self,
        frame: ITaskFrame[tk.Frame, tk.Widget]
    ) -> None:
        """Raise a frame to the top of the application.

        Args:
            frame (TaskFrame): The frame to raise.
        """

        if not frame or not frame.root.winfo_exists():
            raise ValueError("Frame must be a valid existing widget")

        if frame.name not in self._workspace_frames:
            raise ValueError("Frame is not registered in the workspace")

        if frame.root.master != self.workspace_area.root:
            frame.root.master = self.workspace_area.root
            # raise ValueError("Frame is not packed in the workspace area")

        self._hide_frames()
        self._select_frame(frame)
        self._pack_frame_into_workspace(frame)
        self.set_status(f"Raised frame: {frame.name}")

    def _raise_next_available_frame(self) -> None:
        """Raise the next available frame in the workspace."""
        for widget_id, frame in self._workspace_frames.items():
            if frame.root.winfo_exists():
                self._raise_frame(frame)
                return

    def _register_frame_to_view_menu(
        self,
        frame: ITaskFrame
    ) -> None:
        """Register a frame to the view menubar."""
        view_menu = self.gui.unsafe_get_backend().get_root_application_gui_menu().get_view_menu()
        view_menu.add_checkbutton(
            label=frame.name,
            variable=frame.shown,
            command=lambda f=frame: self._raise_frame(f),
            index='end',
        )

    def _register_workspace_frame(
        self,
        frame: ITaskFrame,
        raise_frame: bool = False,
    ) -> None:
        """Register a widget in the workspace tracking."""

        if frame is None:
            raise ValueError("frame must be provided")

        frame.pack_forget()

        if frame.name in self._workspace_frames:
            raise ValueError(f"Widget ID '{frame.name}' already exists")

        self._workspace_frames[frame.name] = frame

        def destroy_func(frame):
            self._unregister_workspace_frame(frame)

        if destroy_func not in frame.on_destroy():
            frame.on_destroy().append(lambda frame: destroy_func(frame))

        self._register_frame_to_view_menu(frame)

        if self.on_task_frame_mounted:
            try:
                self.on_task_frame_mounted(frame, "workspace")
            except Exception as e:
                print(f"Error in on_widget_mounted callback: {e}")

        self.set_status(f"Added workspace widget: {frame.name}")

        if raise_frame:
            self._raise_frame(frame)

    def _select_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Set the selected frame in the view menubar."""
        self._unset_frames_selected()
        frame.set_shown(True)

    def _setup_bindings(self) -> None:
        """Set up event bindings."""
        # Bind sidebar organizer events
        self.sidebar_organizer.on_tab_selected = self._on_sidebar_tab_selected
        self.sidebar_organizer.on_tab_added = self._on_sidebar_tab_added
        self.sidebar_organizer.on_tab_removed = self._on_sidebar_tab_removed

        self.log_paned_window.bind('<B1-Motion>', self.on_log_sash_moved)
        self.main_paned_window.bind('<B1-Motion>', self.on_main_sash_moved)

    def _set_initial_log_window_height(self) -> None:
        """Set the initial log window height."""
        self.log().debug("Setting initial log window height")
        height = self.env.get(
            EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            0.33,
            float
        )
        self.set_log_window_height(height)

    def _set_initial_sidebar_width(self) -> None:
        """Set the initial sidebar width."""
        self.log().debug("Setting initial sidebar width")
        width = self.env.get(
            EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            0.33,
            float
        )
        self.set_sidebar_width(width)

    def _unregister_frame_from_view_menu(
        self,
        frame: ITaskFrame
    ) -> None:
        """Unregister a frame from the view menubar.
        """
        view_menu = self.gui.unsafe_get_backend().get_root_application_gui_menu().get_view_menu()
        try:
            view_menu.remove_item(frame.name)
        except TclError:
            pass  # Menu item may not exist

    def _unregister_workspace_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Unregister a widget from the workspace tracking."""
        if frame.shown:
            self._hide_frames()

        self._workspace_frames.pop(frame.name, None)
        self._unregister_frame_from_view_menu(frame)
        self.set_status(f"Removed workspace frame: {frame.name}")

        if not self._get_shown_frame():
            self._raise_next_available_frame()

    def _unset_frames_selected(self):
        """Unset all frames in the view menubar.
        """
        [frame.set_shown(False) for frame in self._workspace_frames.values()]

    def register_frame(
        self,
        frame: ITaskFrame,
        raise_frame: bool = True
    ) -> None:
        """Register a frame with the workspace.

        Args:
            frame (ITaskFrame): The frame to register.
            raise_frame (bool): Whether to bring the frame to the front upon registration.
        """
        if not isinstance(frame, ITaskFrame):
            raise ValueError("Only ITaskFrame instances can be registered in the workspace")

        self._register_workspace_frame(frame, raise_frame)

    def unregister_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Unregister a frame from the workspace.

        Args:
            frame (ITaskFrame): The frame to unregister.
        """
        if not isinstance(frame, ITaskFrame):
            raise ValueError("Only ITaskFrame instances can be unregistered from the workspace")

        self._unregister_workspace_frame(frame)

    def get_frame(
        self,
        frame_name: str
    ) -> Optional[ITaskFrame]:
        """Get a registered frame by its ID.

        Args:
            frame_name (str): The frame_name of the frame.

        Returns:
            ITaskFrame or None: The registered frame, or None if not found.
        """
        return self._workspace_frames.get(frame_name, None)

    def get_frames(self) -> list[ITaskFrame]:
        """Get all registered frames in the workspace.

        Returns:
            list[ITaskFrame]: List of registered frames.
        """
        return List[self._workspace_frames.values()]

    def set_frames(
        self,
        frames: List[ITaskFrame]
    ) -> None:
        """Set the registered frames in the workspace.

        Args:
            frames (List[ITaskFrame]): List of frames to register.
        """
        self.clear_workspace()
        for frame in frames:
            self._register_workspace_frame(frame, raise_frame=False)

    def raise_frame(
        self,
        frame: ITaskFrame
    ) -> None:
        """Raise a registered frame to the front of the workspace.

        Args:
            frame (ITaskFrame): The frame to raise.
        """
        if not isinstance(frame, ITaskFrame):
            raise ValueError("Only ITaskFrame instances can be raised in the workspace")

        self._raise_frame(frame)

    def add_panel(
        self,
        panel: tk.Widget,
        position: str = 'left'
    ) -> None:
        """
        Add a panel to the workspace.

        Args:
            panel: The panel widget to add
            position: Position to add the panel ('left' or 'right')
        """
        if position == 'left':
            self.main_paned_window.insert(0, panel)
        elif position == 'right':
            self.main_paned_window.add(panel)
        else:
            raise ValueError("Position must be 'left' or 'right'")

    def remove_panel(
        self,
        panel: tk.Widget
    ) -> None:
        """
        Remove a panel from the workspace.

        Args:
            panel: The panel widget to remove
        """
        self.main_paned_window.forget(panel)

    def get_panels(self) -> List[tk.Widget]:
        """
        Get all panels in the workspace.

        Returns:
            List of panel widgets
        """
        return self.main_paned_window.panes()

    def clear_panels(self) -> None:
        """
        Clear all panels from the workspace.
        """
        for pane in self.main_paned_window.panes():
            self.main_paned_window.forget(pane)
        self.panels.clear()

    def set_panel_height(
        self,
        panel_id: str,
        height: int
    ) -> None:
        """
        Set the height of a specific panel.

        Args:
            panel_id: The ID of the panel
            height: The height to set for the panel
        """
        for pane in self.log_paned_window.panes():
            if str(pane) == panel_id:
                index = self.log_paned_window.panes().index(pane)
                total_height = self.log_paned_window.winfo_height()
                if total_height > 0:
                    sash_pos = total_height - height
                    self.log_paned_window.sashpos(index - 1, sash_pos)
                return
        raise ValueError(f"Panel with ID '{panel_id}' not found")

    def get_panel_height(self) -> float:
        """
        Get the height of the log window as a fraction of total height.

        Returns:
            Fractional height (0.0 to 1.0)
        """
        total_height = self.log_paned_window.winfo_height()
        sash_pos = self.log_paned_window.sashpos(0)
        log_height = total_height - sash_pos
        return log_height / total_height if total_height > 0 else 0.0

    def add_sidebar_widget(
        self,
        widget: tk.Widget,
        tab_name: str,
        widget_id: Optional[str] = None,
        icon: Optional[str] = None,
        closeable: bool = True
    ) -> str:
        """
        Add a widget to the sidebar organizer.

        Args:
            widget: The widget to add
            tab_name: Name for the tab
            widget_id: Custom widget ID (auto-generated if None)
            icon: Optional icon for the tab (Unicode character or emoji)
            closeable: Whether the tab can be closed

        Returns:
            The widget ID

        Raises:
            ValueError: If widget_id already exists
        """
        if widget_id is None:
            widget_id = f"sidebar_widget_{len(self._mounted_widgets) + 1}"

        if widget_id in self._mounted_widgets:
            raise ValueError(f"Widget ID '{widget_id}' already exists")

        # Create a container frame for the widget
        if not self.sidebar_organizer:
            raise RuntimeError("Sidebar organizer not initialized")

        container = PyroxFrameContainer(master=self.sidebar_organizer)
        widget.pack(in_=container.frame.root, fill='both', expand=True, padx=2, pady=2)

        # Add to sidebar organizer
        display_name = f"{icon} {tab_name}" if icon else tab_name
        tab_id, _ = self.sidebar_organizer.add_frame_tab(
            display_name,
            PyroxFrameContainer,  # Use PyroxFrame class
            closeable=closeable
        )

        # Get the actual frame and replace its content with our container
        tab_frame_container = self.sidebar_organizer.get_tab_frame(tab_id)
        if tab_frame_container:
            frame = tab_frame_container.frame
            if not frame:
                raise RuntimeError("Failed to get sidebar tab frame")
            # Clear the frame and add our container
            for child in frame.root.winfo_children():
                child.destroy()
            container.frame.pack(in_=frame.root, fill='both', expand=True)

        # Store references
        self._mounted_widgets[widget_id] = widget
        self._sidebar_tabs[widget_id] = tab_id

        # Update status
        self.set_status(f"Added sidebar widget: {tab_name}")

        # Call callback
        if self.on_sidebar_widget_mounted:
            try:
                self.on_sidebar_widget_mounted(widget, "sidebar")
            except Exception as e:
                print(f"Error in on_widget_mounted callback: {e}")

        return widget_id

    def add_workspace_task_frame(
        self,
        task_frame: ITaskFrame,
        raise_frame: bool = True
    ) -> str:
        """
        Add a widget to the main workspace area.

        Args:
            task_frame: The TaskFrame to add
            raise_frame: Whether to raise the frame to the top

        Returns:
            The widget ID

        Raises:
            ValueError: If widget_id already exists or task_frame is None
        """
        if task_frame is None:
            raise ValueError("task_frame must be provided")

        if task_frame.name in self._workspace_frames:
            raise ValueError(f"Widget ID '{task_frame.name}' already exists")

        self._register_workspace_frame(task_frame, raise_frame)

        return task_frame.name

    def build(self) -> None:
        self._create_layout()
        self._setup_bindings()
        self._status_text.set("Workspace Ready")
        super().build()

    def remove_widget(self, widget_id: str) -> bool:
        """
        Remove a widget from the workspace.

        Args:
            widget_id: ID of the widget to remove

        Returns:
            True if widget was removed, False if not found
        """
        removed = False
        location = None

        # Check sidebar widgets
        if widget_id in self._mounted_widgets:
            tab_id = self._sidebar_tabs.get(widget_id)
            if tab_id and self.sidebar_organizer:
                if self.sidebar_organizer.remove_tab(tab_id):
                    if widget_id in self._mounted_widgets:
                        del self._mounted_widgets[widget_id]
                    if widget_id in self._sidebar_tabs:
                        del self._sidebar_tabs[widget_id]
                    location = "sidebar"
                    removed = True

        # Check workspace widgets
        elif widget_id in self._workspace_frames:
            widget = self._workspace_frames[widget_id]
            widget.destroy()
            del self._workspace_frames[widget_id]
            location = "workspace"
            removed = True

        if removed and location:
            self.set_status(f"Removed widget: {widget_id}")

            # Call callback
            if self.on_sidebar_widget_unmounted:
                try:
                    self.on_sidebar_widget_unmounted(widget_id)
                except Exception as e:
                    print(f"Error in on_widget_unmounted callback: {e}")

        return removed

    def get_widget(self, widget_id: str) -> Optional[tk.Widget | ITaskFrame]:
        """Get a widget by its ID."""
        if widget_id in self._mounted_widgets:
            return self._mounted_widgets[widget_id]
        elif widget_id in self._workspace_frames:
            return self._workspace_frames[widget_id]
        return None

    def get_all_widget_ids(self) -> Dict[str, List[str]]:
        """Get all widget IDs organized by location."""
        return {
            'sidebar': list(self._mounted_widgets.keys()),
            'workspace': list(self._workspace_frames.keys())
        }

    def show_sidebar(self) -> None:
        """Show the sidebar organizer."""
        if not self.sidebar_visible and self.main_paned_window and self.sidebar_organizer:
            self.main_paned_window.insert(0, self.sidebar_organizer)

            self.sidebar_visible = True
            self.set_status("Sidebar shown")

            if self.on_sidebar_toggle:
                try:
                    self.on_sidebar_toggle(True)
                except Exception as e:
                    print(f"Error in on_sidebar_toggle callback: {e}")

    def hide_sidebar(self) -> None:
        """Hide the sidebar organizer."""
        if self.sidebar_visible and self.main_paned_window:
            self.main_paned_window.forget(self.sidebar_organizer)
            self.sidebar_visible = False
            self.set_status("Sidebar hidden")

            if self.on_sidebar_toggle:
                try:
                    self.on_sidebar_toggle(False)
                except Exception as e:
                    print(f"Error in on_sidebar_toggle callback: {e}")

    def toggle_sidebar(self) -> bool:
        """
        Toggle sidebar visibility.

        Returns:
            New visibility state
        """
        if self.sidebar_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()
        return self.sidebar_visible

    def set_status(self, status: str) -> None:
        """Set the status bar message."""
        self._status_text.set(status)

    def get_status(self) -> str:
        """Get the current status message."""
        return self._status_text.get()

    def clear_workspace(self) -> None:
        """Clear all widgets from the workspace area."""
        for task_id, task_frame in list(self._workspace_frames.items()):
            self._unregister_workspace_frame(task_frame)
        self.set_status("Workspace cleared")

    def clear_sidebar(self) -> None:
        """Clear all widgets from the sidebar."""
        for widget_id in list(self._mounted_widgets.keys()):
            self.remove_widget(widget_id)
        self.set_status("Sidebar cleared")

    def clear_all(self) -> None:
        """Clear all widgets from both areas."""
        self.clear_workspace()
        self.clear_sidebar()
        self.set_status("All widgets cleared")

    def on_log_sash_moved(self, event):
        pos = self.get_log_window_height()
        for cb in self._sash_callbacks:
            cb('log', pos)

    def on_main_sash_moved(self, event):
        pos = self.get_sidebar_width()
        for cb in self._sash_callbacks:
            cb('main', pos)

    def get_workspace_info(self) -> Dict[str, Any]:
        """Get comprehensive workspace information."""
        return {
            'sidebar': {
                'widget_count': len(self._mounted_widgets),
                'tab_count': self.sidebar_organizer.get_tab_count() if self.sidebar_organizer else 0
            },
            'workspace': {
                'widget_count': len(self._workspace_frames),
                'area_size': (
                    self.workspace_area.root.winfo_width(),
                    self.workspace_area.root.winfo_height()
                ) if self.workspace_area else (0, 0)
            },
            'status': {
                'current_message': self.get_status(),
            },
            'widgets': self.get_all_widget_ids()
        }

    def get_log_window_height(self) -> Optional[int]:
        """Get the current log window sash position as a percentage of the window height."""
        if not self.log_paned_window:
            return None

        self.gui.unsafe_get_backend().update_framekwork_tasks()
        screen_height = self.main_window.winfo_height()
        sash_pos = self.log_paned_window.sashpos(0)
        perc_of_window = (screen_height - sash_pos) / screen_height
        return perc_of_window

    def get_sidebar_width(self) -> Optional[int]:
        """Get the current main window sash position as a percentage of the window width."""
        if not self.main_paned_window:
            return None

        self.gui.unsafe_get_backend().update_framekwork_tasks()
        screen_width = self.main_window.winfo_width()
        sash_pos = self.main_paned_window.sashpos(0)
        perc_of_window = sash_pos / screen_width
        return perc_of_window

    def set_log_window_height(self, perc_of_window: float) -> None:
        """Set the log window height as a percentage of the window height."""
        self.gui.unsafe_get_backend().update_framekwork_tasks()
        total_height = self.window.height
        log_height = int(total_height * perc_of_window)
        self.log_paned_window.sashpos(0, total_height - log_height)
        self.env.set(
            EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            str(perc_of_window)
        )

    def set_sidebar_width(self, perc_of_window: float) -> None:
        """Set the sidebar width as a percentage of the window width."""
        if not self.main_paned_window:
            raise RuntimeError("Main paned window not initialized")

        self.gui.unsafe_get_backend().update_framekwork_tasks()
        total_width = self.window.width
        sidebar_width = int(total_width * perc_of_window)
        self.main_paned_window.sashpos(0, sidebar_width)
        self.env.set(
            EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            str(perc_of_window)
        )

    def subscribe_to_sash_movement_events(
        self,
        callback: Callable
    ) -> None:
        """Subscribe to sash movement events.
        This is temporary and may be replaced with a more robust GUI backend event system later.

        Args:
            callback: Function to call on sash movement with parameters (sash_id, position)
        """
        self._sash_callbacks.append(callback)

    def _on_sidebar_tab_selected(self, tab_id: str, frame: PyroxFrameContainer) -> None:
        """Handle sidebar tab selection."""
        # Find widget_id from tab_id
        widget_id = None
        for wid, tid in self._sidebar_tabs.items():
            if tid == tab_id:
                widget_id = wid
                break

        if widget_id:
            self.set_status(f"Selected sidebar widget: {widget_id}")

            if self.on_workspace_changed:
                try:
                    self.on_workspace_changed(widget_id)
                except Exception as e:
                    print(f"Error in on_workspace_changed callback: {e}")

    def _on_sidebar_tab_added(self, tab_id: str, frame: PyroxFrameContainer) -> None:
        """Handle sidebar tab addition."""
        self.set_status("New sidebar tab added")

    def _on_sidebar_tab_removed(self, tab_id: str) -> None:
        """Handle sidebar tab removal."""
        # Clean up widget references
        widget_id_to_remove = None
        for widget_id, stored_tab_id in self._sidebar_tabs.items():
            if stored_tab_id == tab_id:
                widget_id_to_remove = widget_id
                break

        if widget_id_to_remove:
            if widget_id_to_remove in self._mounted_widgets:
                del self._mounted_widgets[widget_id_to_remove]
            if widget_id_to_remove in self._sidebar_tabs:
                del self._sidebar_tabs[widget_id_to_remove]

            self.set_status(f"Removed sidebar widget: {widget_id_to_remove}")

    def _show_workspace_info(self) -> None:
        """Show workspace information dialog."""
        info = self.get_workspace_info()

        info_text = f"""Workspace Information:

Sidebar:
  • Widgets: {info['sidebar']['widget_count']}
  • Tabs: {info['sidebar']['tab_count']}

Main Area:
  • Widgets: {info['workspace']['widget_count']}
  • Size: {info['workspace']['area_size'][0]}×{info['workspace']['area_size'][1]}px

Status: {info['status']['current_message']}
"""

        # Create info dialog
        info_window = tk.Toplevel(self.window.root)
        info_window.title("Workspace Information")
        info_window.geometry("400x300")
        info_window.resizable(False, False)

        # Center the window
        info_window.transient(self.window.root.winfo_toplevel())
        info_window.grab_set()

        text_widget = tk.Text(
            info_window,
            wrap='word',
            font=('Consolas', 10),
            bg='#101010',
            fg='#aaaaaa',
            padx=10,
            pady=10
        )
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', info_text)
        text_widget.config(state='disabled')

        # Close button
        close_btn = ttk.Button(
            info_window,
            text="Close",
            command=info_window.destroy
        )
        close_btn.pack(pady=(0, 10))
