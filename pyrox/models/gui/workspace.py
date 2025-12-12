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
from pyrox.models.abc.runtime import Buildable
from pyrox.models.gui.frame import TaskFrame
from pyrox.models.gui.logframe import LogFrame
from pyrox.models.gui.frame import PyroxFrameContainer
from pyrox.models.gui.notebook import PyroxNotebook
from pyrox.interfaces import EnvironmentKeys
from pyrox.services import EnvManager, GuiManager, log


class Workspace(Buildable):
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
        self
    ) -> None:
        """ Initialize the PyroxWorkspace.
        """
        super().__init__(
            name="PyroxWorkspace",
            description="A VSCode-like workspace widget with sidebar organizer and main content area."
        )

        self.iframework = GuiManager.unsafe_get_backend()
        self.iwindow = self.iframework.get_root_gui_window()
        self.imenu = self.iframework.get_root_application_gui_menu()

        self._main_paned_window = None
        self._log_paned_window = None
        self._sidebar_organizer = None
        self._workspace_area = None
        self._status_bar = None
        self._status_label = None

        # Widget tracking
        self._mounted_widgets: Dict[str, tk.Widget] = {}
        self._sidebar_tabs: Dict[str, str] = {}  # widget_id -> tab_id mapping
        self._workspace_widgets: Dict[str, TaskFrame] = {}

        # Event callbacks
        self.on_sidebar_toggle: Optional[Callable[[bool], None]] = None
        self.on_task_frame_mounted: Optional[Callable[[TaskFrame, str], None]] = None
        self.on_task_frame_unmounted: Optional[Callable[[TaskFrame], None]] = None
        self.on_sidebar_widget_mounted: Optional[Callable[[tk.Widget, str], None]] = None
        self.on_sidebar_widget_unmounted: Optional[Callable[[str], None]] = None
        self.on_workspace_changed: Optional[Callable[[str], None]] = None

        # Status tracking
        self._status_text = tk.StringVar()

    @property
    def framework(self) -> Any:
        """Get the GUI framework backend.

        Returns:
            The GUI framework backend instance.
        """
        return self.iframework.framework

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
        return self.imenu.menu

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
    def window(self) -> Any:
        """Get the main application window.

        Returns:
            The main application window instance.
        """
        return self.iwindow.window

    @property
    def workspace_area(self) -> PyroxFrameContainer:
        """Get the workspace area.

        Returns:
            PyroxFrameContainer: The workspace area instance.
        """
        if not self._workspace_area:
            raise RuntimeError("Workspace area not initialized")
        return self._workspace_area

    def _create_layout(self) -> None:
        """Create the main workspace layout."""
        self._create_status_bar()
        self._create_main_paned_window()
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
        log(self).debug("Creating log window")
        self.log_window = LogFrame(self.log_paned_window)
        self.log_paned_window.add(self.log_window.frame.root)
        self.iframework.schedule_event(20, self._set_initial_log_window_height)

    def _create_main_paned_window(self) -> None:
        """Create the main paned window for layout."""
        log(self).debug("Creating main paned window")
        self._main_paned_window = ttk.PanedWindow(self.window, orient='horizontal')
        self.main_paned_window.pack(fill='both', expand=True, pady=(0, 0))

    def _create_sidebar_organizer(self) -> None:
        """Create the sidebar organizer."""
        log(self).debug("Creating sidebar organizer")
        self._sidebar_organizer = PyroxNotebook(
            master=self.main_paned_window,
            enable_context_menu=True,
            enable_tab_reordering=True,
            max_tabs=10
        )
        self.main_paned_window.add(self.sidebar_organizer)
        self.iframework.schedule_event(10, self._set_initial_sidebar_width)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        log(self).debug("Creating status bar")
        self._status_bar = ttk.Frame(self.window)
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
        log(self).debug("Creating workspace area")
        self._workspace_area = PyroxFrameContainer(master=self.log_paned_window)
        self.log_paned_window.add(self.workspace_area.frame.root)

    def _get_shown_frame(self) -> Optional[TaskFrame]:
        """Get the currently shown frame in the workspace.

        Returns:
            TaskFrame or None: The currently shown frame, or None if none is shown.
        """
        for frame in self._workspace_widgets.values():
            if frame.shown:
                return frame
        return None

    def _hide_frames(self) -> None:
        """Hide frame from workspace area to prepare for another frame to be raised.
        """
        if not self.workspace_area:
            raise RuntimeError("Workspace area not initialized")

        for widget in self.workspace_area.frame.root.winfo_children():
            widget.pack_forget()

    def _pack_frame_into_workspace(
        self,
        frame: TaskFrame
    ) -> None:
        """Pack a frame into the workspace area.
        Args:
            frame (TaskFrame): The frame to pack.
        """
        if not self.workspace_area:
            raise RuntimeError("Workspace area not initialized")

        if not frame or not frame.winfo_exists():
            raise ValueError("Frame must be a valid existing widget")

        if frame.name not in self._workspace_widgets:
            raise ValueError("Frame is not registered in the workspace")

        frame.pack(in_=self.workspace_area.frame.root, fill='both', expand=True)
        self.set_status(f"Packed frame into workspace: {frame.name}")

    def _raise_frame(
        self,
        frame: TaskFrame
    ) -> None:
        """Raise a frame to the top of the application.

        Args:
            frame (TaskFrame): The frame to raise.
        """
        if not self.workspace_area:
            raise RuntimeError("Workspace area not initialized")

        if not frame or not frame.winfo_exists():
            raise ValueError("Frame must be a valid existing widget")

        if frame.name not in self._workspace_widgets:
            raise ValueError("Frame is not registered in the workspace")

        if frame.master != self.workspace_area.frame.root:
            raise ValueError("Frame is not packed in the workspace area")

        self._hide_frames()
        self._select_frame(frame)
        self._pack_frame_into_workspace(frame)
        self.set_status(f"Raised frame: {frame.name}")

    def _raise_next_available_frame(self) -> None:
        """Raise the next available frame in the workspace."""
        for widget_id, frame in self._workspace_widgets.items():
            if frame.winfo_exists():
                self._raise_frame(frame)
                return

    def _register_frame_to_view_menu(
        self,
        frame: TaskFrame
    ) -> None:
        """Register a frame to the view menubar."""
        view_menu = GuiManager.unsafe_get_backend().get_root_application_gui_menu().get_view_menu()
        view_menu.add_checkbutton(
            label=frame.name,
            variable=frame.shown_var,
            command=lambda f=frame: self._raise_frame(f),
            index='end',
        )

    def _register_workspace_frame(
        self,
        frame: TaskFrame,
        raise_frame: bool = False,
    ) -> None:
        """Register a widget in the workspace tracking."""

        if frame is None:
            raise ValueError("frame must be provided")

        frame.pack_forget()

        if frame.name in self._workspace_widgets:
            raise ValueError(f"Widget ID '{frame.name}' already exists")

        self._workspace_widgets[frame.name] = frame

        def destroy_func(frame):
            self._unregister_workspace_frame(frame)

        if destroy_func not in frame.on_destroy:
            frame.on_destroy.append(lambda frame: destroy_func(frame))

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
        frame: TaskFrame
    ) -> None:
        """Set the selected frame in the view menubar."""
        self._unset_frames_selected()
        frame.shown_var.set(True)

    def _setup_bindings(self) -> None:
        """Set up event bindings."""
        # Bind sidebar organizer events
        self.sidebar_organizer.on_tab_selected = self._on_sidebar_tab_selected
        self.sidebar_organizer.on_tab_added = self._on_sidebar_tab_added
        self.sidebar_organizer.on_tab_removed = self._on_sidebar_tab_removed

    def _set_initial_log_window_height(self) -> None:
        """Set the initial log window height."""
        log(self).debug("Setting initial log window height")
        height = EnvManager.get(
            EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            0.33,
            float
        )
        self.set_log_window_height(height)

    def _set_initial_sidebar_width(self) -> None:
        """Set the initial sidebar width."""
        log(self).debug("Setting initial sidebar width")
        width = EnvManager.get(
            EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            0.33,
            float
        )
        self.set_sidebar_width(width)

    def _unregister_frame_from_view_menu(
        self,
        frame: TaskFrame
    ) -> None:
        """Unregister a frame from the view menubar.
        """
        view_menu = GuiManager.unsafe_get_backend().get_root_application_gui_menu().get_view_menu()
        try:
            view_menu.remove_item(frame.name)
        except TclError:
            pass  # Menu item may not exist

    def _unregister_workspace_frame(
        self,
        frame: TaskFrame
    ) -> None:
        """Unregister a widget from the workspace tracking."""
        if frame.shown:
            self._hide_frames()

        self._workspace_widgets.pop(frame.name, None)
        self._unregister_frame_from_view_menu(frame)
        self.set_status(f"Removed workspace frame: {frame.name}")

        if not self._get_shown_frame():
            self._raise_next_available_frame()

    def _unset_frames_selected(self):
        """Unset all frames in the view menubar.
        """
        [frame.shown_var.set(False) for frame in self._workspace_widgets.values()]

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
        task_frame: TaskFrame,
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

        if task_frame.name in self._workspace_widgets:
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
        elif widget_id in self._workspace_widgets:
            widget = self._workspace_widgets[widget_id]
            widget.destroy()
            del self._workspace_widgets[widget_id]
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

    def get_widget(self, widget_id: str) -> Optional[tk.Widget]:
        """Get a widget by its ID."""
        if widget_id in self._mounted_widgets:
            return self._mounted_widgets[widget_id]
        elif widget_id in self._workspace_widgets:
            return self._workspace_widgets[widget_id]
        return None

    def get_all_widget_ids(self) -> Dict[str, List[str]]:
        """Get all widget IDs organized by location."""
        return {
            'sidebar': list(self._mounted_widgets.keys()),
            'workspace': list(self._workspace_widgets.keys())
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

    def set_status(self, message: str) -> None:
        """Set the status bar message."""
        self._status_text.set(message)

    def get_status(self) -> str:
        """Get the current status message."""
        return self._status_text.get()

    def clear_workspace(self) -> None:
        """Clear all widgets from the workspace area."""
        for task_id, task_frame in list(self._workspace_widgets.items()):
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

    def get_workspace_info(self) -> Dict[str, Any]:
        """Get comprehensive workspace information."""
        return {
            'sidebar': {
                'widget_count': len(self._mounted_widgets),
                'tab_count': self.sidebar_organizer.get_tab_count() if self.sidebar_organizer else 0
            },
            'workspace': {
                'widget_count': len(self._workspace_widgets),
                'area_size': (
                    self.workspace_area.frame.root.winfo_width(),
                    self.workspace_area.frame.root.winfo_height()
                ) if self.workspace_area else (0, 0)
            },
            'status': {
                'current_message': self.get_status(),
            },
            'widgets': self.get_all_widget_ids()
        }

    def set_log_window_height(self, perc_of_window: float) -> None:
        """Set the log window height as a percentage of the window height."""
        if not self.log_paned_window:
            raise RuntimeError("Log paned window not initialized")

        self.iframework.update_framekwork_tasks()
        total_height = self.window.winfo_height()
        log_height = int(total_height * perc_of_window)
        self.log_paned_window.sashpos(0, total_height - log_height)
        EnvManager.set(
            EnvironmentKeys.ui.UI_LOG_WINDOW_HEIGHT,
            str(perc_of_window)
        )

    def set_sidebar_width(self, perc_of_window: float) -> None:
        """Set the sidebar width as a percentage of the window width."""
        if not self.main_paned_window:
            raise RuntimeError("Main paned window not initialized")

        self.iframework.update_framekwork_tasks()
        total_width = self.window.winfo_width()
        sidebar_width = int(total_width * perc_of_window)
        self.main_paned_window.sashpos(0, sidebar_width)
        EnvManager.set(
            EnvironmentKeys.ui.UI_SIDEBAR_WIDTH,
            str(perc_of_window)
        )

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
        info_window = tk.Toplevel(self.window)
        info_window.title("Workspace Information")
        info_window.geometry("400x300")
        info_window.resizable(False, False)

        # Center the window
        info_window.transient(self.window.winfo_toplevel())
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


def create_demo_window():
    """Create a demo window showing the PyroxWorkspace in action."""
    workspace = Workspace()

    class ExplorerWidget(PyroxFrameContainer):
        """File explorer-like widget."""

        def __init__(self, master):
            super().__init__(master=master)

            ttk.Label(self.frame.root, text="📁 Explorer", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Create a simple tree
            tree = ttk.Treeview(self.frame.root, show='tree')
            tree.pack(fill='both', expand=True, padx=5, pady=5)

            # Add sample folders
            root_folder = tree.insert('', 'end', text='📁 Project')
            src_folder = tree.insert(root_folder, 'end', text='📁 src')
            tree.insert(src_folder, 'end', text='📄 main.py')
            tree.insert(src_folder, 'end', text='📄 utils.py')

            docs_folder = tree.insert(root_folder, 'end', text='📁 docs')
            tree.insert(docs_folder, 'end', text='📄 README.md')

            tree.item(root_folder, open=True)
            tree.item(src_folder, open=True)

    class SearchWidget(PyroxFrameContainer):
        """Search widget."""

        def __init__(self, master):
            super().__init__(master=master)

            ttk.Label(self.frame.root, text="🔍 Search", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Search entry
            search_frame = ttk.Frame(self.frame.root)
            search_frame.pack(fill='x', padx=5, pady=5)

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(fill='x')
            search_entry.insert(0, "Search files...")

            # Results area
            results_frame = ttk.LabelFrame(self.frame.root, text="Results")
            results_frame.pack(fill='both', expand=True, padx=5, pady=5)

            results_list = tk.Listbox(results_frame)
            results_list.pack(fill='both', expand=True, padx=5, pady=5)

            # Add sample results
            for i in range(10):
                results_list.insert('end', f"match_{i+1}.py:42 - sample result")

    class GitWidget(PyroxFrameContainer):
        """Git/VCS widget."""

        def __init__(self, master):
            super().__init__(master=master)

            ttk.Label(self.frame.root, text="🌿 Source Control", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Status
            status_frame = ttk.LabelFrame(self.frame.root, text="Status")
            status_frame.pack(fill='x', padx=5, pady=5)

            ttk.Label(status_frame, text="Branch: main").pack(anchor='w', padx=5, pady=2)
            ttk.Label(status_frame, text="Changes: 3 modified").pack(anchor='w', padx=5, pady=2)

            # Changed files
            changes_frame = ttk.LabelFrame(self.frame.root, text="Changes")
            changes_frame.pack(fill='both', expand=True, padx=5, pady=5)

            changes_tree = ttk.Treeview(changes_frame, columns=('status',), show='tree headings')
            changes_tree.heading('#0', text='File')
            changes_tree.heading('status', text='Status')
            changes_tree.pack(fill='both', expand=True, padx=5, pady=5)

            # Add sample changes
            changes_tree.insert('', 'end', text='main.py', values=('Modified',))
            changes_tree.insert('', 'end', text='utils.py', values=('Added',))
            changes_tree.insert('', 'end', text='config.json', values=('Deleted',))

    # Main workspace content
    class MainEditor(TaskFrame):
        """Main editor area."""

        def __init__(self, master):
            super().__init__(master=master)

            # Editor tabs
            editor_notebook = PyroxNotebook(self)
            editor_notebook.pack(fill='both', expand=True, padx=5, pady=5)

            # Add editor tabs
            for i in range(3):
                tab_id, tab_frame = editor_notebook.add_frame_tab(f"file_{i+1}.py")

                # Add text widget to simulate editor
                text_editor = tk.Text(
                    tab_frame.frame.root,
                    font=('Consolas', 10),
                    bg='#101010',
                    fg='#aaaaaa',
                    insertbackground='#ffffff',
                    wrap='none'
                )
                text_editor.pack(fill='both', expand=True, padx=5, pady=5)

                # Add sample code
                sample_code = f"""# File {i+1} - Sample Python Code
def main():
    print("Hello from file {i+1}")

    # Sample function
    result = calculate_something()
    return result

def calculate_something():
    '''Sample calculation function'''
    return 42 * (i + 1)

if __name__ == "__main__":
    main()
"""
                text_editor.insert('1.0', sample_code)

        @property
        def name(self) -> str:
            return "MainEditor"

    class TerminalWidget(TaskFrame):
        """Terminal/console widget."""

        def __init__(self, master):
            super().__init__(master=master)

            # Terminal output
            terminal_text = tk.Text(
                self,
                font=('Consolas', 9),
                bg='#000000',
                fg='#00ff00',
                insertbackground='#00ff00',
                height=8
            )
            terminal_text.pack(fill='both', expand=True, padx=5, pady=5)

            # Sample terminal output
            terminal_output = """$ python main.py
Starting application...
Loading configuration...
✓ Configuration loaded successfully
✓ Database connection established
✓ Server started on port 8000
Ready to accept connections...
$ """
            terminal_text.insert('1.0', terminal_output)
            terminal_text.see('end')

        @property
        def name(self) -> str:
            return "TerminalWidget"

    # Add sidebar widgets
    explorer = ExplorerWidget(master=workspace.window)
    search = SearchWidget(master=workspace.window)
    git = GitWidget(master=workspace.window)

    workspace.add_sidebar_widget(explorer.frame.root, "Explorer", "explorer", "📁", closeable=False)
    workspace.add_sidebar_widget(search.frame.root, "Search", "search", "🔍")
    workspace.add_sidebar_widget(git.frame.root, "Source Control", "git", "🌿")

    # Add main workspace content
    main_editor = MainEditor(master=workspace.workspace_area.frame.root)
    terminal = TerminalWidget(master=workspace.workspace_area.frame.root)

    workspace.add_workspace_task_frame(main_editor)
    workspace.add_workspace_task_frame(terminal)

    # View menu
    view_menu = workspace.imenu.get_view_menu()
    view_menu.add_item(label="Toggle Sidebar", command=workspace.toggle_sidebar)
    view_menu.add_separator()
    view_menu.add_item(label="Workspace Info", command=workspace._show_workspace_info)
    view_menu.add_item(label="Clear Workspace", command=workspace.clear_workspace)
    view_menu.add_item(label="Clear Sidebar", command=workspace.clear_sidebar)

    # Set up callbacks
    def on_sidebar_toggle_callback(visible: bool):
        workspace.set_status(f"Sidebar {'shown' if visible else 'hidden'}")

    def on_task_frame_mounted_callback(frame: TaskFrame, location: str):
        workspace.set_status(f"Mounted {frame.name} to {location}")

    workspace.on_sidebar_toggle = on_sidebar_toggle_callback
    workspace.on_task_frame_mounted = on_task_frame_mounted_callback

    # Keyboard shortcuts
    workspace.iframework.bind_hotkey('Control-b', lambda: workspace.toggle_sidebar())
    workspace.iframework.bind_hotkey('F1', lambda: workspace._show_workspace_info())

    return workspace.window


def only_create_workspace():
    """Create a workspace instance without running the demo."""
    workspace = Workspace()
    return workspace


if __name__ == "__main__":
    # Run the demo
    demo_window = create_demo_window()
    # demo_window = only_create_workspace().window
    demo_window.mainloop()
