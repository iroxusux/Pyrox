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
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Any
from pyrox.models.gui.logframe import LogFrame
from pyrox.models.gui.meta import PyroxFrame
from pyrox.models.gui.notebook import PyroxNotebook


class PyroxWorkspace(PyroxFrame):
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
        master=None,
        sidebar_width: int = 300,
        sidebar_position: str = 'left',
        sidebar_visible: bool = True,
        enable_status_bar: bool = True,
        enable_log_window: bool = True,
        splitter_sash_pad: int = 4,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxWorkspace.

        Args:
            master: Parent widget
            sidebar_width: Initial width of the sidebar in pixels
            sidebar_position: Position of sidebar ('left' or 'right')
            sidebar_visible: Whether sidebar is initially visible
            enable_status_bar: Whether to show status bar at bottom
            splitter_sash_pad: Padding for the splitter sash
            **kwargs: Additional arguments passed to PyroxFrame
        """
        super().__init__(master, **kwargs)

        # Configuration
        self.sidebar_width = sidebar_width
        self.sidebar_position = sidebar_position
        self.sidebar_visible = sidebar_visible
        self.enable_status_bar = enable_status_bar
        self.enable_log_window = enable_log_window
        self.splitter_sash_pad = splitter_sash_pad

        # Widget references
        self.main_paned_window: Optional[ttk.PanedWindow] = None
        self.sidebar_organizer: Optional[PyroxNotebook] = None
        self.workspace_area: Optional[PyroxFrame] = None
        self.status_bar: Optional[ttk.Frame] = None
        self.status_label: Optional[ttk.Label] = None

        # Widget tracking
        self._mounted_widgets: Dict[str, tk.Widget] = {}
        self._sidebar_tabs: Dict[str, str] = {}  # widget_id -> tab_id mapping
        self._workspace_widgets: Dict[str, tk.Widget] = {}

        # Event callbacks
        self.on_sidebar_toggle: Optional[Callable[[bool], None]] = None
        self.on_widget_mounted: Optional[Callable[[str, tk.Widget, str], None]] = None
        self.on_widget_unmounted: Optional[Callable[[str, str], None]] = None
        self.on_workspace_changed: Optional[Callable[[str], None]] = None

        # Status tracking
        self._status_text = tk.StringVar()
        self._status_text.set("Workspace Ready")

        # Create the layout
        self._create_layout()
        self._setup_bindings()

    def _create_layout(self) -> None:
        """Create the main workspace layout."""
        # Create status bar first if enabled
        if self.enable_status_bar:
            self._create_status_bar()

        # Create main paned window
        self.log_paned_window = ttk.PanedWindow(self, orient='vertical')
        self.main_paned_window = ttk.PanedWindow(self.log_paned_window, orient='horizontal')
        self.main_paned_window.pack(fill='both', expand=True, pady=(0, 0))

        # Create log window if enabled
        if self.enable_log_window:
            self._create_log_window()

        if self.enable_status_bar:
            self.log_paned_window.pack(fill='both', expand=True, pady=(0, 0))
        else:
            self.log_paned_window.pack(fill='both', expand=True)

        # Create sidebar organizer (PyroxNotebook with vertical tabs)
        self.sidebar_organizer = PyroxNotebook(
            self.main_paned_window,
            tab_pos='w',  # Vertical tabs on the left
            enable_context_menu=True,
            enable_tab_reordering=True,
            max_tabs=15
        )

        # Create main workspace area
        self.workspace_area = PyroxFrame(self.main_paned_window)

        # Add to paned window based on sidebar position
        if self.sidebar_position == 'left':
            self.main_paned_window.add(self.sidebar_organizer)
            self.main_paned_window.add(self.workspace_area)
        else:  # right
            self.main_paned_window.add(self.workspace_area)
            self.main_paned_window.add(self.sidebar_organizer)

        # Set initial sidebar width
        if self.sidebar_visible:
            self.after(10, self._set_initial_sidebar_width)
        else:
            self.hide_sidebar()

        self.log_paned_window.add(self.main_paned_window)
        if self.enable_log_window:
            self.log_paned_window.add(self.log_window)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill='x', side='bottom')

        # Status label
        self.status_label = ttk.Label(
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

    def _create_log_window(self) -> None:
        """Create a log window at the bottom.
        """
        if not self.enable_log_window:
            return

        self.log_window = LogFrame(self.log_paned_window)
        self.log_window.pack(fill='x', side='bottom', padx=2, pady=2)

    def _setup_bindings(self) -> None:
        """Set up event bindings."""
        # Bind sidebar organizer events
        if self.sidebar_organizer:
            self.sidebar_organizer.on_tab_selected = self._on_sidebar_tab_selected
            self.sidebar_organizer.on_tab_added = self._on_sidebar_tab_added
            self.sidebar_organizer.on_tab_removed = self._on_sidebar_tab_removed

    def _set_initial_sidebar_width(self) -> None:
        """Set the initial sidebar width."""
        if self.main_paned_window and self.sidebar_visible:
            try:
                # Wait for window to be properly initialized
                self.update_idletasks()
                if self.sidebar_position == 'left':
                    self.main_paned_window.sash_place(0, self.sidebar_width, 0)
                else:
                    total_width = self.winfo_width()
                    if total_width > self.sidebar_width:
                        pos = total_width - self.sidebar_width
                        self.main_paned_window.sash_place(0, pos, 0)
            except (tk.TclError, AttributeError):
                # Sash not ready yet, try again later
                self.after(100, self._set_initial_sidebar_width)

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

        container = PyroxFrame(self.sidebar_organizer)
        widget.pack(in_=container, fill='both', expand=True, padx=2, pady=2)

        # Add to sidebar organizer
        display_name = f"{icon} {tab_name}" if icon else tab_name
        tab_id, _ = self.sidebar_organizer.add_frame_tab(
            display_name,
            PyroxFrame,  # Use PyroxFrame class
            closeable=closeable
        )

        # Get the actual frame and replace its content with our container
        tab_frame = self.sidebar_organizer.get_tab_frame(tab_id)
        if tab_frame:
            # Clear the frame and add our container
            for child in tab_frame.winfo_children():
                child.destroy()
            container.pack(in_=tab_frame, fill='both', expand=True)

        # Store references
        self._mounted_widgets[widget_id] = widget
        self._sidebar_tabs[widget_id] = tab_id

        # Update status
        self.set_status(f"Added sidebar widget: {tab_name}")

        # Call callback
        if self.on_widget_mounted:
            try:
                self.on_widget_mounted(widget_id, widget, "sidebar")
            except Exception as e:
                print(f"Error in on_widget_mounted callback: {e}")

        return widget_id

    def add_workspace_widget(
        self,
        widget: tk.Widget,
        widget_id: Optional[str] = None,
        pack_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a widget to the main workspace area.

        Args:
            widget: The widget to add
            widget_id: Custom widget ID (auto-generated if None)
            pack_options: Options for packing the widget

        Returns:
            The widget ID

        Raises:
            ValueError: If widget_id already exists
        """
        if widget_id is None:
            widget_id = f"workspace_widget_{len(self._workspace_widgets) + 1}"

        if widget_id in self._workspace_widgets:
            raise ValueError(f"Widget ID '{widget_id}' already exists")

        # Default pack options
        if pack_options is None:
            pack_options = {'fill': 'both', 'expand': True, 'padx': 5, 'pady': 5}

        # Add widget to workspace area
        if not self.workspace_area:
            raise RuntimeError("Workspace area not initialized")
        widget.pack(in_=self.workspace_area, **pack_options)

        # Store reference
        self._workspace_widgets[widget_id] = widget

        # Update status
        self.set_status(f"Added workspace widget: {widget_id}")

        # Call callback
        if self.on_widget_mounted:
            try:
                self.on_widget_mounted(widget_id, widget, "workspace")
            except Exception as e:
                print(f"Error in on_widget_mounted callback: {e}")

        return widget_id

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
                self.sidebar_organizer.remove_tab(tab_id)

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
            if self.on_widget_unmounted:
                try:
                    self.on_widget_unmounted(widget_id, location)
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
            if self.sidebar_position == 'left':
                self.main_paned_window.insert(0, self.sidebar_organizer)
            else:
                self.main_paned_window.add(self.sidebar_organizer)

            self.sidebar_visible = True
            self.after(10, self._set_initial_sidebar_width)
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

    def set_sidebar_width(self, width: int) -> None:
        """Set the sidebar width."""
        self.sidebar_width = width
        if self.sidebar_visible:
            self._set_initial_sidebar_width()

    def set_status(self, message: str) -> None:
        """Set the status bar message."""
        self._status_text.set(message)

    def get_status(self) -> str:
        """Get the current status message."""
        return self._status_text.get()

    def clear_workspace(self) -> None:
        """Clear all widgets from the workspace area."""
        for widget_id in list(self._workspace_widgets.keys()):
            self.remove_widget(widget_id)
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
                'visible': self.sidebar_visible,
                'position': self.sidebar_position,
                'width': self.sidebar_width,
                'widget_count': len(self._mounted_widgets),
                'tab_count': self.sidebar_organizer.get_tab_count() if self.sidebar_organizer else 0
            },
            'workspace': {
                'widget_count': len(self._workspace_widgets),
                'area_size': (self.workspace_area.winfo_width(), self.workspace_area.winfo_height()) if self.workspace_area else (0, 0)
            },
            'status': {
                'current_message': self.get_status(),
                'status_bar_enabled': self.enable_status_bar
            },
            'widgets': self.get_all_widget_ids()
        }

    def _on_sidebar_tab_selected(self, tab_id: str, frame: PyroxFrame) -> None:
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

    def _on_sidebar_tab_added(self, tab_id: str, frame: PyroxFrame) -> None:
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
  • Visible: {info['sidebar']['visible']}
  • Position: {info['sidebar']['position']}
  • Width: {info['sidebar']['width']}px
  • Widgets: {info['sidebar']['widget_count']}
  • Tabs: {info['sidebar']['tab_count']}

Main Area:
  • Widgets: {info['workspace']['widget_count']}
  • Size: {info['workspace']['area_size'][0]}×{info['workspace']['area_size'][1]}px

Status: {info['status']['current_message']}
"""

        # Create info dialog
        info_window = tk.Toplevel(self)
        info_window.title("Workspace Information")
        info_window.geometry("400x300")
        info_window.resizable(False, False)

        # Center the window
        info_window.transient(self.winfo_toplevel())
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

    root = tk.Tk()
    root.title("PyroxWorkspace Demo")
    root.geometry("1200x800")

    # Create the workspace
    workspace = PyroxWorkspace(
        root,
        sidebar_width=350,
        sidebar_position='left',
        sidebar_visible=True,
        enable_status_bar=True
    )
    workspace.pack(fill='both', expand=True)

    # Demo widgets for sidebar
    class ExplorerWidget(PyroxFrame):
        """File explorer-like widget."""

        def __init__(self, master):
            super().__init__(master)

            ttk.Label(self, text="📁 Explorer", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Create a simple tree
            tree = ttk.Treeview(self, show='tree')
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

    class SearchWidget(PyroxFrame):
        """Search widget."""

        def __init__(self, master):
            super().__init__(master)

            ttk.Label(self, text="🔍 Search", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Search entry
            search_frame = ttk.Frame(self)
            search_frame.pack(fill='x', padx=5, pady=5)

            search_entry = ttk.Entry(search_frame)
            search_entry.pack(fill='x')
            search_entry.insert(0, "Search files...")

            # Results area
            results_frame = ttk.LabelFrame(self, text="Results")
            results_frame.pack(fill='both', expand=True, padx=5, pady=5)

            results_list = tk.Listbox(results_frame)
            results_list.pack(fill='both', expand=True, padx=5, pady=5)

            # Add sample results
            for i in range(10):
                results_list.insert('end', f"match_{i+1}.py:42 - sample result")

    class GitWidget(PyroxFrame):
        """Git/VCS widget."""

        def __init__(self, master):
            super().__init__(master)

            ttk.Label(self, text="🌿 Source Control", font=('Consolas', 12, 'bold')).pack(pady=5)

            # Status
            status_frame = ttk.LabelFrame(self, text="Status")
            status_frame.pack(fill='x', padx=5, pady=5)

            ttk.Label(status_frame, text="Branch: main").pack(anchor='w', padx=5, pady=2)
            ttk.Label(status_frame, text="Changes: 3 modified").pack(anchor='w', padx=5, pady=2)

            # Changed files
            changes_frame = ttk.LabelFrame(self, text="Changes")
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
    class MainEditor(PyroxFrame):
        """Main editor area."""

        def __init__(self, master):
            super().__init__(master)

            # Editor tabs
            editor_notebook = PyroxNotebook(self, tab_pos='n')
            editor_notebook.pack(fill='both', expand=True, padx=5, pady=5)

            # Add editor tabs
            for i in range(3):
                tab_id, tab_frame = editor_notebook.add_frame_tab(f"file_{i+1}.py")

                # Add text widget to simulate editor
                text_editor = tk.Text(
                    tab_frame,
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

    class TerminalWidget(PyroxFrame):
        """Terminal/console widget."""

        def __init__(self, master):
            super().__init__(master)

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

    # Add sidebar widgets
    explorer = ExplorerWidget(workspace)
    search = SearchWidget(workspace)
    git = GitWidget(workspace)

    workspace.add_sidebar_widget(explorer, "Explorer", "explorer", "📁", closeable=False)
    workspace.add_sidebar_widget(search, "Search", "search", "🔍")
    workspace.add_sidebar_widget(git, "Source Control", "git", "🌿")

    # Add main workspace content
    main_editor = MainEditor(workspace)
    terminal = TerminalWidget(workspace)

    workspace.add_workspace_widget(main_editor, "editor", {'fill': 'both', 'expand': True})
    workspace.add_workspace_widget(terminal, "terminal", {'fill': 'x', 'side': 'bottom'})

    # Menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # View menu
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Toggle Sidebar", command=workspace.toggle_sidebar)
    view_menu.add_separator()
    view_menu.add_command(label="Workspace Info", command=workspace._show_workspace_info)

    # Window menu
    window_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Window", menu=window_menu)
    window_menu.add_command(label="Clear Workspace", command=workspace.clear_workspace)
    window_menu.add_command(label="Clear Sidebar", command=workspace.clear_sidebar)

    # Set up callbacks
    def on_sidebar_toggle_callback(visible: bool):
        workspace.set_status(f"Sidebar {'shown' if visible else 'hidden'}")

    def on_widget_mounted_callback(widget_id: str, widget: tk.Widget, location: str):
        workspace.set_status(f"Mounted {widget_id} to {location}")

    workspace.on_sidebar_toggle = on_sidebar_toggle_callback
    workspace.on_widget_mounted = on_widget_mounted_callback

    # Initial status
    workspace.set_status("PyroxWorkspace Demo Ready - Use View menu to toggle sidebar")

    # Keyboard shortcuts
    root.bind('<Control-b>', lambda e: workspace.toggle_sidebar())
    root.bind('<F1>', lambda e: workspace._show_workspace_info())

    return root


if __name__ == "__main__":
    # Run the demo
    demo_window = create_demo_window()
    demo_window.mainloop()
