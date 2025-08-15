"""tkinter user made frames
    """
from __future__ import annotations
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Widget
import sys
from typing import Any, Optional, Union

from . import meta
from .treeview import LazyLoadingTreeView


class FrameWithTreeViewAndScrollbar(meta.PyroxFrame):
    """A frame containing a LazyLoadingTreeView with vertical scrollbar.

    This frame provides a ready-to-use treeview widget with scrollbar
    for displaying hierarchical data. The treeview has columns for
    'Name' and 'Value'.

    Args:
        *args: Variable length argument list passed to PyroxFrame.
        base_gui_class (type, optional): The base GUI class for the treeview.
        **kwargs: Arbitrary keyword arguments. 'context_menu' is extracted
            and passed to the treeview.

    Attributes:
        _tree (LazyLoadingTreeView): The treeview widget.
    """

    def __init__(
        self,
        master,
        base_gui_class: type = None,
        context_menu: Optional[tk.Menu] = None
    ) -> None:
        super().__init__(master=master)

        self._tree: LazyLoadingTreeView = LazyLoadingTreeView(
            master=self,
            base_gui_class=base_gui_class,
            columns=('Value',),
            show='tree headings',
            context_menu=context_menu
        )
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')

        vscrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self._tree.yview,
            style="TScrollbar"
        )
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self._tree.pack(fill=tk.BOTH, expand=True)

    @property
    def tree(self) -> LazyLoadingTreeView:
        """Get the treeview widget.

        Returns:
            LazyLoadingTreeView: The treeview widget contained in this frame.
        """
        return self._tree

    @tree.setter
    def tree(self, value: LazyLoadingTreeView):
        """Set the treeview widget.

        Args:
            value (LazyLoadingTreeView): The new treeview widget to set.

        Raises:
            TypeError: If value is not a LazyLoadingTreeView instance.
        """
        if isinstance(value, LazyLoadingTreeView):
            self._tree = value
            self._tree.pack(fill=tk.BOTH, expand=True)
        else:
            raise TypeError(f'Expected LazyLoadingTreeView, got {type(value)}')


class LogFrame(meta.PyroxFrame):
    """Enhanced log window that captures both logging and stderr/stdout."""

    def __init__(self, parent,):
        super().__init__(parent)

        # Create toolbar frame
        self._toolbar = meta.PyroxFrame(
            self,
            height=30,
            style='TFrameHeader',
        )
        self._toolbar.pack(
            fill=tk.X,
            side=tk.TOP
        )
        self._toolbar.pack_propagate(False)

        self._setup_toolbar()
        self._setup_text_widget()
        self._setup_text_tags()
        self._setup_stream_redirection()

    def _setup_text_widget(self):
        """Setup the main text widget and scrollbar."""
        text_frame = ttk.Frame(self)
        text_frame.pack(
            side=tk.BOTTOM,
            fill=tk.BOTH,
            expand=True
        )

        self._logtext = tk.Text(
            text_frame,
            state='disabled',
            background=meta.PyroxDefaultTheme.widget_background,
            foreground=meta.PyroxDefaultTheme.foreground,
            wrap='word',
            borderwidth=meta.PyroxDefaultTheme.borderwidth,
            relief=meta.PyroxDefaultTheme.relief,
        )

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            text_frame,
            orient=tk.VERTICAL,
            command=self._logtext.yview
        )

        self._logtext.configure(
            yscrollcommand=v_scrollbar.set,
        )

        # Grid layout
        self._logtext.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

    def _setup_text_tags(self):
        """Setup text tags for different types of messages."""
        # Standard logging levels
        self._logtext.tag_configure(
            'INFO',
            foreground=meta.PyroxDefaultTheme.foreground,
            background=meta.PyroxDefaultTheme.widget_background
        )
        self._logtext.tag_configure(
            'WARNING',
            foreground=meta.PyroxDefaultTheme.widget_background,
            background='yellow'
        )
        self._logtext.tag_configure(
            'ERROR',
            foreground=meta.PyroxDefaultTheme.foreground,
            background='red'
        )
        self._logtext.tag_configure(
            'DEBUG',
            foreground='cyan',
            background=meta.PyroxDefaultTheme.widget_background
        )

        # Stream types
        self._logtext.tag_configure(
            'STDERR',
            foreground='orange',
            background=meta.PyroxDefaultTheme.widget_background
        )
        self._logtext.tag_configure(
            'STDOUT',
            foreground='lightgreen',
            background=meta.PyroxDefaultTheme.widget_background
        )

    def _setup_stream_redirection(self):
        """Setup redirection of stderr and stdout to the text widget."""
        self._stderr_stream = meta.TextWidgetStream(
            self._logtext,
            'STDERR',
            self.log,
        )
        sys.stderr = self._stderr_stream

        self._stdout_stream = meta.TextWidgetStream(
            self._logtext,
            'STDOUT',
            self.log,
        )
        sys.stdout = self._stdout_stream

    def _setup_toolbar(self):
        """Setup the toolbar with control buttons."""
        self.add_toolbar_button(
            "Clear",
            self.clear_log_window
        )

    def _log_message(self, message: str, tag: str = 'INFO'):
        """Log a message directly to the text widget."""
        try:
            self._logtext.config(state='normal')

            # Insert message
            start_idx = self._logtext.index('end-1c')
            self._logtext.insert('end', message)
            end_idx = self._logtext.index('end-1c')

            # Apply tag
            self._logtext.tag_add(message, start_idx, end_idx)
            black = meta.PyroxDefaultTheme.widget_background
            white = meta.PyroxDefaultTheme.foreground_selected
            self._logtext.tag_configure(message,
                                        foreground=black if tag == 'WARNING' else white,
                                        background='yellow' if tag == 'WARNING' else 'red' if tag == 'ERROR' else black,
                                        font=('Courier New', 12, 'bold'))

            # Auto-scroll and limit lines
            self._logtext.see('end')
            lines = int(self._logtext.index('end-1c').split('.')[0])
            if lines > 1000:
                self._logtext.delete('1.0', f'{lines-1000}.0')

            self._logtext.config(state='disabled')

        except tk.TclError as e:
            print(f'Error logging message: {e}')

    def log(self, message: str):
        """Log a message with automatic severity detection."""
        # Detect severity from message content
        if '| ERROR |' in message:
            tag = 'ERROR'
        elif '| WARNING |' in message:
            tag = 'WARNING'
        elif '| DEBUG |' in message:
            tag = 'DEBUG'
        else:
            tag = 'INFO'

        if not message.endswith('\n'):
            message += '\n'
        self._log_message(message, tag)

    def clear_log_window(self):
        """Clear all text from the log window."""
        try:
            self._logtext.config(state='normal')
            self._logtext.delete('1.0', 'end')
            self._logtext.config(state='disabled')
            self.update()
        except tk.TclError as e:
            print(f'Error clearing log window: {e}')

    def destroy(self):
        """Clean up stream redirection when destroying the widget."""
        # Restore original streams
        if self._stderr_stream:
            self._stderr_stream.close()
            if sys.stderr == self._stderr_stream:
                sys.stderr = self._original_stderr

        if self._stdout_stream:
            self._stdout_stream.close()
            if sys.stdout == self._stdout_stream:
                sys.stdout = self._original_stdout

        super().destroy()

    def add_toolbar_button(self, text: str, command: callable):
        """Add a custom button to the toolbar."""

        button = ttk.Button(
            self._toolbar,
            text=text,
            command=command,
        )
        button.pack(side=tk.LEFT, fill=tk.Y)
        return button


class OrganizerWindow(meta.PyroxFrame):
    """Organizer Window for application purposes
    """

    def __init__(self, master):
        super().__init__(master)
        self._notebook: meta.PyroxNotebook = meta.PyroxNotebook(
            master=self,
            tab_pos='wn',
        )
        self._notebook.pack(fill=tk.BOTH, expand=True)

    def register_tab(self, frame: tk.Frame, text: str) -> None:
        """Register a new tab in the organizer window.

        Args:
            frame (Frame): The frame to add as a tab.
            text (str): The text label for the tab.
        """
        self._notebook.add(frame, text=text, sticky='nsew')


class TaskFrame(tk.Frame):
    """A frame for tasks in the application with title bar and close button.

    This frame provides a standardized interface for task windows with
    a title bar containing a close button and title label. It includes
    callback support for cleanup operations when the frame is destroyed.

    Args:
        *args: Variable length argument list passed to Frame.
        name (str, optional): The name/title of the task frame. Defaults to 'Task Frame'.
        **kwargs: Arbitrary keyword arguments passed to Frame.

    Attributes:
        _name (str): The name of the task frame.
        _shown (bool): Whether the frame is currently shown.
        _shown_var (BooleanVar): Tkinter variable tracking the shown state.
        _title_bar (Frame): The title bar frame containing controls.
        _close_button (Button): The close button in the title bar.
        _title_label (Label): The title label in the title bar.
        _content_frame (Frame): The main content area of the frame.
        _on_destroy (list[callable]): List of callbacks to execute on destroy.
    """

    def __init__(self,
                 *args,
                 name: str = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name or 'Task Frame'
        self._shown: bool = False
        self._shown_var: tk.BooleanVar = tk.BooleanVar(value=self._shown)
        self._title_bar = tk.Frame(self, height=20, bg='lightgrey')

        self._close_button = tk.Button(self._title_bar,
                                       text='X',
                                       command=self.destroy,
                                       width=3,)
        self._close_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self._title_label = tk.Label(self._title_bar, text=name or 'Task Frame', bg='lightgrey')
        self._title_label.pack(side=tk.LEFT, padx=5, pady=5)

        self._title_bar.pack(fill=tk.X, side=tk.TOP)

        self._content_frame = tk.Frame(self)
        self._content_frame.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        self._on_destroy: list[callable] = []

    @property
    def content_frame(self) -> tk.Frame:
        """Get the content frame for adding widgets.

        Returns:
            Frame: The main content area where widgets should be added.
        """
        return self._content_frame

    @property
    def name(self) -> str:
        """Get the name of the task frame.

        Returns:
            str: The name/title of the task frame.
        """
        return self._name

    @property
    def on_destroy(self) -> list[callable]:
        """Get the list of destroy callbacks.

        Returns:
            list[callable]: List of functions to call when the frame is destroyed.
        """
        return self._on_destroy

    @property
    def shown(self) -> bool:
        """Get the shown state of the task frame.

        Returns:
            bool: True if the task frame is shown, False otherwise.
        """
        return self._shown

    @shown.setter
    def shown(self, value: bool):
        """Set the shown state of the task frame.

        Args:
            value (bool): True to mark the frame as shown, False to mark as hidden.

        Raises:
            TypeError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise TypeError(f'Expected bool, got {type(value)}')
        self._shown = value

    @property
    def shown_var(self) -> tk.BooleanVar:
        """Get the BooleanVar tracking the shown state.

        Returns:
            BooleanVar: Tkinter variable representing the shown state.
        """
        return self._shown_var

    def destroy(self):
        """Destroy the task frame and execute all registered callbacks.

        Calls all functions in the on_destroy list before destroying the frame.
        Non-callable items in the list generate warning messages.
        """
        for callback in self._on_destroy:
            if callable(callback):
                callback()
            else:
                self.logger.warning(f'Callback {callback} is not callable.')
        return super().destroy()

    @property
    def tree(self) -> LazyLoadingTreeView:
        """Get the treeview widget.

        Returns:
            LazyLoadingTreeView: The treeview widget in this window.
        """
        return self._tree


@dataclass
class ObjectEditField:
    """Configuration for an object property edit field.

    This dataclass defines how an object property should be displayed
    and edited in an ObjectEditTaskFrame.

    Attributes:
        property_name (str): The name of the property on the object.
        display_name (str): The human-readable name to display.
        display_type (Widget): The tkinter widget type to use for editing.
        editable (bool): Whether the field can be edited. Defaults to False.
    """
    property_name: str
    display_name: str
    display_type: Widget
    editable: bool = False


class ObjectEditTaskFrame(TaskFrame):
    """A task frame for editing object properties.

    This frame provides a form-based interface for editing object properties
    with Accept/Cancel buttons. The properties are defined using ObjectEditField
    configurations that specify the widget type and editability.

    Args:
        master (Optional[Widget]): The parent widget.
        object_ (Any): The object to edit (cannot be None).
        properties (list[ObjectEditField]): List of property configurations.

    Attributes:
        _object (Any): The object being edited.
        _properties (list[ObjectEditField]): The property configurations.
        _property_vars (dict): Mapping of property names to tkinter variables.

    Raises:
        ValueError: If object_ is None.
    """

    def __init__(self,
                 master: Optional[Widget],
                 object_: Any,
                 properties: list[ObjectEditField]):
        super().__init__(master=master,
                         name=f"Edit {getattr(object_, 'name', object_.__class__.__name__)}")
        if object_ is None:
            raise ValueError("Object to edit cannot be None")
        self._object = object_
        self._properties = properties
        self._property_vars = {}
        self._populate_entries(self._object, self._properties)
        btn_frame = tk.Frame(self.content_frame)
        btn_frame.grid(row=len(self._properties), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Accept", command=self._on_accept, width=10).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancel", command=self._on_cancel, width=10).pack(side='left', padx=5)

    def _on_accept(self):
        """Handle Accept button click.

        Attempts to set all editable properties on the object using the
        values from the form widgets. Shows error dialog if any property
        cannot be set, then destroys the frame.
        """
        for prop, var in self._property_vars.items():
            # Try to set the property if it has a setter
            try:
                setattr(self._object, prop, var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Could not set {prop}: {e}")
        self.destroy()

    def _on_cancel(self):
        """Handle Cancel button click.

        Destroys the frame without saving any changes.
        """
        self.destroy()

    def _populate_entries(self,
                          object_: Any,
                          properties: list[ObjectEditField]):
        """Populate the form with entry widgets for each property.

        Creates appropriate tkinter widgets based on the display_type
        specified in each ObjectEditField. Supported widget types include
        Label (displayed as Entry), Text, Entry, Checkbutton, and Combobox.

        Args:
            object_ (Any): The object whose properties are being edited.
            properties (list[ObjectEditField]): The property configurations.
        """
        for idx, prop in enumerate(properties):
            if prop.display_type is tk.Label:
                tk.Label(self.content_frame, text=prop.display_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
                value = getattr(object_, prop.property_name, "")
                var = tk.StringVar(value=str(value) if value is not None else "")
                entry = tk.Entry(self.content_frame, textvariable=var, width=40)
                entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
                entry.config(state='normal' if prop.editable else 'disabled')
                if prop.editable:
                    self._property_vars[prop.property_name] = var

            elif prop.display_type is tk.Text:
                tk.Label(self.content_frame, text=prop.display_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
                value = getattr(object_, prop.property_name, "")
                var = tk.StringVar(value=str(value) if value is not None else "")
                entry = tk.Text(self.content_frame, width=40, height=5)
                entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
                entry.insert(tk.END, var.get())
                entry.config(state='normal' if prop.editable else 'disabled')
                if prop.editable:
                    self._property_vars[prop.property_name] = var

            elif prop.display_type is ttk.Entry:
                tk.Label(self.content_frame, text=prop.display_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
                value = getattr(object_, prop.property_name, "")
                var = tk.StringVar(value=str(value) if value is not None else "")
                entry = ttk.Entry(self.content_frame, textvariable=var, width=40)
                entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
                entry.config(state='normal' if prop.editable else 'disabled')
                if prop.editable:
                    self._property_vars[prop.property_name] = var

            elif prop.display_type is tk.Checkbutton:
                tk.Label(self.content_frame, text=prop.display_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
                value = getattr(object_, prop.property_name, False)
                var = tk.BooleanVar(value=value)
                entry = tk.Checkbutton(self.content_frame, variable=var)
                entry.grid(row=idx, column=1, sticky='w', padx=5, pady=2)
                entry.config(state='normal' if prop.editable else 'disabled')
                if prop.editable:
                    self._property_vars[prop.property_name] = var

            elif prop.display_type is ttk.Combobox:
                tk.Label(self.content_frame, text=prop.display_name).grid(row=idx, column=0, sticky='w', padx=5, pady=2)
                value = getattr(object_, prop.property_name, "")
                var = tk.StringVar(value=str(value) if value is not None else "")
                entry = ttk.Combobox(self.content_frame, textvariable=var, width=40)
                entry.grid(row=idx, column=1, sticky='ew', padx=5, pady=2)
                entry['values'] = []  # this needs to be updated later with actual choices
                entry.config(state='normal' if prop.editable else 'disabled')
                if prop.editable:
                    self._property_vars[prop.property_name] = var


class WatchTableTaskFrame(TaskFrame):
    """A task frame implementing a watch table for programming symbols.

    This frame provides a spreadsheet-like interface for watching and
    modifying programming symbols. Each row contains a combobox with
    auto-complete for symbol selection, a value field, and Write/Remove
    buttons. Supports dynamic adding/removing of rows.

    Args:
        master: The parent widget.
        watch_items (list[str], optional): Initial list of symbols to watch.
        all_symbols (list[str], optional): Complete list of symbols for auto-complete.
        name (str, optional): Frame name. Defaults to "Watch Table".
        on_write (callable, optional): Callback function(symbol, value) for write operations.

    Attributes:
        _watch_items (list[str]): Current list of watched symbols.
        _all_symbols (list[str]): Complete list of available symbols.
        _comboboxes (list): List of tuples containing row widgets and variables.
        _on_write (callable): Callback for write operations.
        _rows_frame (Frame): Container for the table rows.
    """

    def __init__(self, master, watch_items=None, all_symbols=None, name="Watch Table", on_write=None):
        """Initialize the watch table frame.

        Args:
            master: Parent widget.
            watch_items: List of initial watched symbols (strings).
            all_symbols: List of all possible symbols for auto-complete.
            name: Frame name.
            on_write: Optional callback(symbol, value) for writing data.
        """
        super().__init__(master=master, name=name)
        self._watch_items = watch_items or []
        self._all_symbols = all_symbols or []
        self._comboboxes: list[tuple[Widget, ttk.Entry, tk.StringVar, tk.StringVar, tk.Button]] = []
        self._on_write = on_write  # callback for writing data
        self._setup_table()

    def _setup_table(self):
        """Set up the table header and initial rows.

        Creates the column headers and adds rows for any initial watch items.
        """
        header = tk.Frame(self.content_frame)
        header.pack(fill=tk.X, pady=(5, 0))
        tk.Label(header, text="Symbol", width=30, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Value", width=20, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Write", width=6, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Button(header, text="+", command=self._add_row, width=3).pack(side=tk.LEFT, padx=5)

        self._rows_frame = tk.Frame(self.content_frame)
        self._rows_frame.pack(fill=tk.BOTH, expand=True)

        for symbol in self._watch_items:
            self._add_row(symbol)

    def _add_row(self, symbol=""):
        """Add a new row to the watch table.

        Args:
            symbol (str, optional): Initial symbol name for the row.
        """
        row = tk.Frame(self._rows_frame)
        row.pack(fill=tk.X, pady=2)

        symbol_var = tk.StringVar(value=symbol)
        value_var = tk.StringVar(value="")

        # Combobox with auto-complete and text entry
        combo = ttk.Combobox(row, textvariable=symbol_var, values=self._all_symbols, width=30)
        combo.pack(side=tk.LEFT, padx=5)
        combo['state'] = 'normal'  # allow text entry
        combo.bind('<KeyRelease>', lambda e, cb=combo: self._autocomplete(cb, e))
        combo.bind('<Return>', lambda e: self._on_enter_pressed(combo))
        combo.bind('<Tab>', lambda e: self._on_enter_pressed(combo))

        value_entry = ttk.Entry(row, textvariable=value_var, width=20)
        value_entry.pack(side=tk.LEFT, padx=5)
        value_entry.bind('<Return>', lambda e: self._on_enter_pressed(value_entry))
        value_entry.bind('<Tab>', lambda e: self._on_enter_pressed(value_entry))

        write_btn = tk.Button(row, text="Write", width=6,
                              command=lambda: self._on_write_click(symbol_var, value_var))
        write_btn.pack(side=tk.LEFT, padx=5)

        remove_btn = tk.Button(row, text="–", command=lambda: self._remove_row(row), width=3)
        remove_btn.pack(side=tk.LEFT, padx=5)

        self._comboboxes.append((combo, value_entry, symbol_var, value_var, write_btn))

    def _remove_row(self, row: Widget):
        """Remove a row from the watch table.

        Args:
            row (Widget): The row frame to remove.
        """
        for cb in self._comboboxes:
            parent = cb[0].master
            exists = cb[0].winfo_exists()
            if parent == row or exists is False:
                self._comboboxes.remove(cb)
                row.destroy()
                break

    def _autocomplete(self,
                      combobox: ttk.Combobox,
                      event: Optional[tk.Event] = None):
        """Handle auto-completion for symbol comboboxes.

        Args:
            combobox (ttk.Combobox): The combobox being typed in.
            event (Optional[tk.Event]): The key event that triggered auto-complete.
        """
        if event and event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down', 'Shift_L', 'Shift_R', 'Control_L', 'Control_R'):
            return

        if len(event.keysym) > 1:  # Ignore non-character keys
            return

        pattern = combobox.get()
        if not pattern:
            combobox['values'] = self._all_symbols
            return

        filtered = [s for s in self._all_symbols if pattern.lower() in s.lower()]
        combobox['values'] = filtered

        if filtered:
            for match in filtered:
                if match.lower().startswith(pattern.lower()) and match != pattern:
                    # Only autocomplete if the user hasn't already typed the match
                    def do_autocomplete():
                        combobox.set(match)
                        combobox.icursor(len(pattern))
                        combobox.selection_range(len(pattern), tk.END)
                    combobox.after_idle(do_autocomplete)
                    break

    def _on_enter_pressed(self, widget: Union[ttk.Combobox, ttk.Entry]):
        """Handle Enter key press to move focus.

        Args:
            widget (Union[ttk.Combobox, ttk.Entry]): The widget that received Enter.

        Returns:
            str: 'break' to prevent default Enter handling.
        """
        widget.icursor(tk.END)
        widget.selection_range(tk.END, tk.END)
        widget.master.focus_set()
        return 'break'

    def add_tag(self, symbol: str, value: str = ""):
        """Add a new row with the specified symbol and value.

        Args:
            symbol (str): The symbol name to add.
            value (str, optional): The initial value. Defaults to "".

        Raises:
            messagebox.showerror: If symbol is empty.
        """
        if not symbol:
            messagebox.showerror("Error", "Symbol cannot be empty.")
            return
        self._add_row(symbol)
        self.update_row_by_name(symbol, value)

    def get_watch_table(self):
        """Get all current watch table entries.

        Returns:
            list[tuple[str, str]]: List of (symbol, value) tuples for all rows
                that have non-empty symbols and are not currently focused.
        """
        result = []
        try:
            focus_widget = self.master.winfo_toplevel().focus_get()
        except KeyError:
            return result
        for combo, value_entry, symbol_var, value_var, _ in self._comboboxes:
            if not value_entry.winfo_exists() or not combo.winfo_exists():
                continue
            if focus_widget == value_entry or focus_widget == combo:
                continue
            symbol = symbol_var.get()
            value = value_var.get()
            if symbol:
                result.append((symbol, value))
        return result

    def update_row_by_name(self, symbol_name: str, new_value: str):
        """Update the value of a row by its symbol name.

        Args:
            symbol_name (str): The symbol name to find and update.
            new_value (str): The new value to set.
        """
        for combo, value_entry, symbol_var, value_var, _ in self._comboboxes:
            if symbol_var.get() == symbol_name:
                if not value_entry.winfo_exists():
                    return
                if value_entry == value_entry.focus_get():
                    return
                value_var.set(new_value)
                return

    def update_symbols(self, new_symbols: list[str]):
        """Update the list of available symbols for auto-complete.

        Args:
            new_symbols (list[str]): The new list of symbols.
        """
        self._all_symbols = new_symbols
        for combo, *_ in self._comboboxes:
            combo['values'] = new_symbols
            self._autocomplete(combo)

    def _on_write_click(self, symbol_var: tk.StringVar, value_var: tk.StringVar):
        """Handle Write button click for a row.

        Args:
            symbol_var (tk.StringVar): The symbol variable for this row.
            value_var (tk.StringVar): The value variable for this row.
        """
        symbol = symbol_var.get()
        value = value_var.get()
        if not symbol:
            messagebox.showerror("Error", "Symbol cannot be empty.")
            return
        if self._on_write:
            self._on_write(symbol, value)
        else:
            messagebox.showinfo("Write", f"Would write value '{value}' to symbol '{symbol}'.")
        self.master.focus_set()  # Return focus to the main window
