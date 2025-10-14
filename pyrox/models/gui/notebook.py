"""
Enhanced Notebook widget for Pyrox applications with advanced tab management.

This module provides a notebook widget with built-in PyroxFrame management,
dynamic tab creation/removal, tab reordering, and comprehensive event handling
for efficient UI management.
"""
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable, Any
from pyrox.models.gui.meta import PyroxFrame, PyroxThemeManager


class PyroxNotebook(ttk.Notebook):
    """
    An enhanced notebook widget with Pyrox theming and advanced tab management.

    Features:
    - Automatic PyroxFrame creation and management
    - Dynamic tab addition and removal
    - Tab reordering support
    - Event callbacks for tab operations
    - Built-in context menu support
    - Tab close buttons (optional)
    - Tab naming and validation
    - Lazy loading support for tab content
    """

    def __init__(
        self,
        master=None,
        tab_pos: str = 'n',
        enable_context_menu: bool = True,
        enable_tab_reordering: bool = True,
        max_tabs: int = 20,
        **kwargs
    ) -> None:
        """
        Initialize the PyroxNotebook.

        Args:
            master: Parent widget
            tab_pos: Tab position ('n', 's', 'e', 'w')
            enable_context_menu: Enable right-click context menu
            enable_tab_reordering: Enable drag-and-drop tab reordering
            max_tabs: Maximum number of tabs allowed
            **kwargs: Additional arguments passed to ttk.Notebook
        """
        self._configure_style(tab_pos)
        super().__init__(master, **kwargs)

        # Configuration
        self.max_tabs = max_tabs
        self.enable_context_menu = enable_context_menu
        self.enable_tab_reordering = enable_tab_reordering

        # Internal tracking
        self._tab_frames: Dict[str, PyroxFrame] = {}
        self._tab_data: Dict[str, Dict[str, Any]] = {}
        self._tab_callbacks: Dict[str, Callable] = {}
        self._tab_counter = 0
        self._dragging_tab = None
        self._context_menu: Optional[tk.Menu] = None

        # Event callbacks
        self.on_tab_added: Optional[Callable[[str, PyroxFrame], None]] = None
        self.on_tab_removed: Optional[Callable[[str], None]] = None
        self.on_tab_selected: Optional[Callable[[str, PyroxFrame], None]] = None
        self.on_tab_renamed: Optional[Callable[[str, str, str], None]] = None

        # Set up event bindings
        self._setup_bindings()

        # Create context menu if enabled
        if self.enable_context_menu:
            self._create_context_menu()

    def _configure_style(self, tab_pos) -> None:
        """Configure the notebook style."""
        PyroxThemeManager.ensure_theme_created()
        style = ttk.Style()
        style.configure('TNotebook', tabposition=tab_pos)

    def _setup_bindings(self) -> None:
        """Set up event bindings for the notebook."""
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        if self.enable_context_menu:
            self.bind('<Button-3>', self._show_context_menu)

        if self.enable_tab_reordering:
            self.bind('<Button-1>', self._on_tab_click)
            self.bind('<B1-Motion>', self._on_tab_drag)
            self.bind('<ButtonRelease-1>', self._on_tab_release)

    def _create_context_menu(self) -> None:
        """Create the right-click context menu."""
        self._context_menu = tk.Menu(self, tearoff=0)
        self._context_menu.add_command(label="Rename Tab", command=self._rename_current_tab)
        self._context_menu.add_command(label="Close Tab", command=self._close_current_tab)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="Close All Other Tabs", command=self._close_other_tabs)
        self._context_menu.add_command(label="Close All Tabs", command=self._close_all_tabs)

    def add_frame_tab(
        self,
        text: str,
        frame_class: type = PyroxFrame,
        tab_id: Optional[str] = None,
        closeable: bool = True,
        **frame_kwargs
    ) -> tuple[str, PyroxFrame]:
        """
        Add a new tab with a PyroxFrame.

        Args:
            text: Tab text/title
            frame_class: Class to use for the frame (defaults to PyroxFrame)
            tab_id: Custom tab ID (auto-generated if None)
            closeable: Whether the tab can be closed
            **frame_kwargs: Additional arguments for frame creation

        Returns:
            Tuple of (tab_id, frame_instance)

        Raises:
            ValueError: If max_tabs exceeded or invalid parameters
        """
        if len(self._tab_frames) >= self.max_tabs:
            raise ValueError(f"Maximum number of tabs ({self.max_tabs}) exceeded")

        if not text.strip():
            raise ValueError("Tab text cannot be empty")

        # Generate tab ID if not provided
        if tab_id is None:
            self._tab_counter += 1
            tab_id = f"tab_{self._tab_counter}"
        elif tab_id in self._tab_frames:
            raise ValueError(f"Tab ID '{tab_id}' already exists")

        # Create the frame
        try:
            frame = frame_class(self, **frame_kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create frame: {e}")

        # Add to notebook
        self.add(frame, text=text)

        # Store references
        self._tab_frames[tab_id] = frame
        self._tab_data[tab_id] = {
            'text': text,
            'closeable': closeable,
            'frame_class': frame_class,
            'frame_kwargs': frame_kwargs
        }

        # Call callback if set
        if self.on_tab_added:
            try:
                self.on_tab_added(tab_id, frame)
            except Exception as e:
                print(f"Error in on_tab_added callback: {e}")

        return tab_id, frame

    def remove_tab(self, tab_id: str) -> bool:
        """
        Remove a tab by ID.

        Args:
            tab_id: The ID of the tab to remove

        Returns:
            True if tab was removed, False if not found or not closeable

        Raises:
            ValueError: If tab_id is invalid
        """
        if not tab_id or tab_id not in self._tab_frames:
            return False

        # Check if tab is closeable
        if not self._tab_data[tab_id].get('closeable', True):
            return False

        frame = self._tab_frames[tab_id]

        # Remove from notebook
        self.forget(frame)

        # Clean up references
        del self._tab_frames[tab_id]
        del self._tab_data[tab_id]
        if tab_id in self._tab_callbacks:
            del self._tab_callbacks[tab_id]

        # Call callback if set
        if self.on_tab_removed:
            try:
                self.on_tab_removed(tab_id)
            except Exception as e:
                print(f"Error in on_tab_removed callback: {e}")

        return True

    def get_tab_frame(self, tab_id: str) -> Optional[PyroxFrame]:
        """Get the frame associated with a tab ID."""
        return self._tab_frames.get(tab_id)

    def get_current_tab_id(self) -> Optional[str]:
        """Get the ID of the currently selected tab."""
        current_frame = self.nametowidget(self.select()) if self.select() else None
        if current_frame:
            for tab_id, frame in self._tab_frames.items():
                if frame == current_frame:
                    return tab_id
        return None

    def get_current_tab_frame(self) -> Optional[PyroxFrame]:
        """Get the frame of the currently selected tab."""
        tab_id = self.get_current_tab_id()
        return self.get_tab_frame(tab_id) if tab_id else None

    def get_all_tab_ids(self) -> List[str]:
        """Get a list of all tab IDs."""
        return list(self._tab_frames.keys())

    def select_tab(self, tab_id: str) -> bool:
        """Select a tab by ID."""
        frame = self.get_tab_frame(tab_id)
        if frame:
            self.select(frame)
            return True
        return False

    def rename_tab(self, tab_id: str, new_text: str) -> bool:
        """
        Rename a tab.

        Args:
            tab_id: The ID of the tab to rename
            new_text: The new tab text

        Returns:
            True if renamed successfully, False otherwise
        """
        if not new_text.strip():
            return False

        frame = self.get_tab_frame(tab_id)
        if not frame:
            return False

        old_text = self._tab_data[tab_id]['text']
        self.tab(frame, text=new_text)
        self._tab_data[tab_id]['text'] = new_text

        # Call callback if set
        if self.on_tab_renamed:
            try:
                self.on_tab_renamed(tab_id, old_text, new_text)
            except Exception as e:
                print(f"Error in on_tab_renamed callback: {e}")

        return True

    def close_all_tabs(self) -> int:
        """
        Close all closeable tabs.

        Returns:
            Number of tabs closed
        """
        closed_count = 0
        tab_ids = list(self._tab_frames.keys())  # Copy to avoid modification during iteration

        for tab_id in tab_ids:
            if self.remove_tab(tab_id):
                closed_count += 1

        return closed_count

    def close_other_tabs(self, keep_tab_id: Optional[str] = None) -> int:
        """
        Close all tabs except the specified one (or current if None).

        Args:
            keep_tab_id: Tab ID to keep (current tab if None)

        Returns:
            Number of tabs closed
        """
        if keep_tab_id is None:
            keep_tab_id = self.get_current_tab_id()

        if not keep_tab_id:
            return 0

        closed_count = 0
        tab_ids = list(self._tab_frames.keys())

        for tab_id in tab_ids:
            if tab_id != keep_tab_id and self.remove_tab(tab_id):
                closed_count += 1

        return closed_count

    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return len(self._tab_frames)

    def is_empty(self) -> bool:
        """Check if the notebook has no tabs."""
        return len(self._tab_frames) == 0

    def clear(self) -> None:
        """Remove all tabs and clear internal state."""
        self.close_all_tabs()
        self._tab_counter = 0

    def set_tab_callback(self, tab_id: str, callback: Callable) -> bool:
        """Set a callback function for a specific tab."""
        if tab_id in self._tab_frames:
            self._tab_callbacks[tab_id] = callback
            return True
        return False

    def get_tab_info(self, tab_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a tab."""
        if tab_id in self._tab_data:
            info = self._tab_data[tab_id].copy()
            info['id'] = tab_id
            info['frame'] = self._tab_frames[tab_id]
            return info
        return None

    def _on_tab_changed(self, event) -> None:
        """Handle tab selection change."""
        current_tab_id = self.get_current_tab_id()
        if current_tab_id and self.on_tab_selected:
            frame = self.get_tab_frame(current_tab_id)
            if frame:  # Ensure frame is not None
                try:
                    self.on_tab_selected(current_tab_id, frame)
                except Exception as e:
                    print(f"Error in on_tab_selected callback: {e}")

    def _show_context_menu(self, event) -> None:
        """Show the context menu."""
        if self._context_menu and self.get_tab_count() > 0:
            try:
                self._context_menu.tk_popup(event.x_root, event.y_root)
            except Exception:
                pass

    def _rename_current_tab(self) -> None:
        """Rename the current tab via dialog."""
        current_tab_id = self.get_current_tab_id()
        if not current_tab_id:
            return

        current_text = self._tab_data[current_tab_id]['text']

        # Simple input dialog
        from tkinter.simpledialog import askstring
        new_text = askstring("Rename Tab", "Enter new tab name:", initialvalue=current_text)

        if new_text and new_text != current_text:
            self.rename_tab(current_tab_id, new_text)

    def _close_current_tab(self) -> None:
        """Close the current tab."""
        current_tab_id = self.get_current_tab_id()
        if current_tab_id:
            self.remove_tab(current_tab_id)

    def _close_other_tabs(self) -> None:
        """Close all other tabs."""
        self.close_other_tabs()

    def _close_all_tabs(self) -> None:
        """Close all tabs with confirmation."""
        if self.get_tab_count() > 1:
            from tkinter import messagebox
            if messagebox.askyesno("Close All Tabs", "Are you sure you want to close all tabs?"):
                self.close_all_tabs()
        else:
            self.close_all_tabs()

    def _on_tab_click(self, event) -> None:
        """Handle tab click for drag detection."""
        if not self.enable_tab_reordering:
            return

        try:
            element = self.identify(event.x, event.y)
            if element == "label":
                self._dragging_tab = self.index("@%d,%d" % (event.x, event.y))
        except Exception:
            self._dragging_tab = None

    def _on_tab_drag(self, event) -> None:
        """Handle tab dragging."""
        if not self.enable_tab_reordering or self._dragging_tab is None:
            return

        try:
            element = self.identify(event.x, event.y)
            if element == "label":
                target_index = self.index("@%d,%d" % (event.x, event.y))
                if target_index != self._dragging_tab:
                    # Reorder tabs
                    self.insert(target_index, self._dragging_tab)
                    self._dragging_tab = target_index
        except Exception:
            pass

    def _on_tab_release(self, event) -> None:
        """Handle end of tab dragging."""
        self._dragging_tab = None


def create_demo_window():
    """Create a demo window showing the PyroxNotebook in action."""

    root = tk.Tk()
    root.title("PyroxNotebook Demo")
    root.geometry("900x700")

    # Create main container
    main_frame = ttk.Frame(root)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Create the notebook
    notebook = PyroxNotebook(
        main_frame,
        enable_context_menu=True,
        enable_tab_reordering=True,
        max_tabs=10
    )

    # Add some demo content classes
    class TextDemoFrame(PyroxFrame):
        """Demo frame with text content."""

        def __init__(self, master, content="Sample content"):
            super().__init__(master)

            # Add a text widget with sample content
            text_widget = tk.Text(
                self,
                wrap='word',
                font=('Consolas', 10),
                bg='#101010',
                fg='#aaaaaa',
                insertbackground='#ffffff'
            )
            text_widget.pack(fill='both', expand=True, padx=5, pady=5)
            text_widget.insert('1.0', content)

    class TreeDemoFrame(PyroxFrame):
        """Demo frame with treeview content."""

        def __init__(self, master):
            super().__init__(master)

            # Add a simple treeview
            tree = ttk.Treeview(self, columns=('value',), show='tree headings')
            tree.heading('#0', text='Item')
            tree.heading('value', text='Value')

            # Add some sample data
            root_item = tree.insert('', 'end', text='Root', values=('Root Value',))
            for i in range(5):
                child = tree.insert(root_item, 'end', text=f'Child {i+1}', values=(f'Value {i+1}',))
                for j in range(3):
                    tree.insert(child, 'end', text=f'Subchild {j+1}', values=(f'Subvalue {j+1}',))

            tree.pack(fill='both', expand=True, padx=5, pady=5)

    class ButtonDemoFrame(PyroxFrame):
        """Demo frame with buttons and controls."""

        def __init__(self, master):
            super().__init__(master)

            # Add various controls
            ttk.Label(self, text="Control Demo").pack(pady=10)

            button_frame = ttk.Frame(self)
            button_frame.pack(fill='x', padx=10, pady=5)

            ttk.Button(button_frame, text="Button 1").pack(side='left', padx=5)
            ttk.Button(button_frame, text="Button 2").pack(side='left', padx=5)
            ttk.Button(button_frame, text="Button 3").pack(side='left', padx=5)

            # Add entry and combobox
            entry_frame = ttk.Frame(self)
            entry_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(entry_frame, text="Entry:").pack(side='left')
            ttk.Entry(entry_frame).pack(side='left', fill='x', expand=True, padx=5)

            combo_frame = ttk.Frame(self)
            combo_frame.pack(fill='x', padx=10, pady=5)

            ttk.Label(combo_frame, text="Combo:").pack(side='left')
            combo = ttk.Combobox(combo_frame, values=['Option 1', 'Option 2', 'Option 3'])
            combo.pack(side='left', fill='x', expand=True, padx=5)
            combo.set('Option 1')

    # Pack the notebook
    notebook.pack(fill='both', expand=True, pady=(0, 10))

    # Add some demo tabs
    tab1_id, tab1_frame = notebook.add_frame_tab(
        "Welcome",
        TextDemoFrame,
        content="""Welcome to PyroxNotebook Demo!

This enhanced notebook widget provides:

• Dynamic tab creation and removal
• Tab reordering via drag-and-drop
• Context menu support (right-click)
• Event callbacks for tab operations
• Theming with Pyrox default theme
• Maximum tab limits
• Tab close protection

Try the buttons below to test various features!
"""
    )

    tab2_id, tab2_frame = notebook.add_frame_tab(
        "Tree View",
        TreeDemoFrame
    )

    tab3_id, tab3_frame = notebook.add_frame_tab(
        "Controls",
        ButtonDemoFrame,
        closeable=False  # This tab cannot be closed
    )

    # Create control buttons
    control_frame = ttk.Frame(main_frame)
    control_frame.pack(fill='x', pady=(5, 0))

    def add_text_tab():
        """Add a new text tab."""
        try:
            count = notebook.get_tab_count() + 1
            tab_id, frame = notebook.add_frame_tab(
                f"Text Tab {count}",
                TextDemoFrame,
                content=f"This is dynamically created text tab #{count}.\n\nYou can add up to {notebook.max_tabs} tabs total."
            )
            notebook.select_tab(tab_id)
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

    def add_tree_tab():
        """Add a new tree tab."""
        try:
            count = notebook.get_tab_count() + 1
            tab_id, frame = notebook.add_frame_tab(
                f"Tree Tab {count}",
                TreeDemoFrame
            )
            notebook.select_tab(tab_id)
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))

    def close_current():
        """Close the current tab."""
        current_id = notebook.get_current_tab_id()
        if current_id:
            if notebook.remove_tab(current_id):
                status_var.set(f"Closed tab: {current_id}")
            else:
                status_var.set("Tab cannot be closed")
        else:
            status_var.set("No tab selected")

    def show_tab_info():
        """Show info about the current tab."""
        current_id = notebook.get_current_tab_id()
        if current_id:
            info = notebook.get_tab_info(current_id)
            if info:
                info_text = f"""Tab Information:
                
ID: {info['id']}
Text: {info['text']}
Closeable: {info['closeable']}
Frame Class: {info['frame_class'].__name__}
Total Tabs: {notebook.get_tab_count()}
"""
                from tkinter import messagebox
                messagebox.showinfo("Tab Info", info_text)

    def close_others():
        """Close all other tabs."""
        count = notebook.close_other_tabs()
        status_var.set(f"Closed {count} other tabs")

    # Add control buttons
    ttk.Button(control_frame, text="Add Text Tab", command=add_text_tab).pack(side='left', padx=2)
    ttk.Button(control_frame, text="Add Tree Tab", command=add_tree_tab).pack(side='left', padx=2)
    ttk.Button(control_frame, text="Close Current", command=close_current).pack(side='left', padx=2)
    ttk.Button(control_frame, text="Close Others", command=close_others).pack(side='left', padx=2)
    ttk.Button(control_frame, text="Tab Info", command=show_tab_info).pack(side='left', padx=2)

    # Add status bar
    status_var = tk.StringVar()
    status_bar = ttk.Label(root, textvariable=status_var, relief='sunken')
    status_bar.pack(fill='x', side='bottom')

    # Set up event callbacks
    def on_tab_added_callback(tab_id: str, frame: PyroxFrame):
        status_var.set(f"Tab added: {tab_id}")

    def on_tab_removed_callback(tab_id: str):
        status_var.set(f"Tab removed: {tab_id}")

    def on_tab_selected_callback(tab_id: str, frame: PyroxFrame):
        info = notebook.get_tab_info(tab_id)
        if info:
            status_var.set(f"Selected: {info['text']} (ID: {tab_id})")

    def on_tab_renamed_callback(tab_id: str, old_text: str, new_text: str):
        status_var.set(f"Renamed '{old_text}' to '{new_text}'")

    # Assign callbacks
    notebook.on_tab_added = on_tab_added_callback
    notebook.on_tab_removed = on_tab_removed_callback
    notebook.on_tab_selected = on_tab_selected_callback
    notebook.on_tab_renamed = on_tab_renamed_callback

    # Select the first tab and show initial status
    notebook.select_tab(tab1_id)
    status_var.set("PyroxNotebook Demo Ready - Right-click tabs for context menu")

    # Add some helpful instructions
    help_frame = ttk.Frame(root)
    help_frame.pack(fill='x', side='bottom', before=status_bar)

    help_text = "💡 Tips: Right-click tabs for context menu • Drag tabs to reorder • 'Controls' tab cannot be closed"
    ttk.Label(help_frame, text=help_text, font=('Consolas', 8)).pack(pady=2)

    return root


if __name__ == "__main__":
    # Run the demo
    demo_window = create_demo_window()
    demo_window.mainloop()
