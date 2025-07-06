"""tkinter user made frames
    """
from __future__ import annotations
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Widget
from logging import INFO, WARNING, ERROR
from typing import Any, Optional
from tkinter import (
    BOTH,
    Button,
    BOTTOM,
    GROOVE,
    Entry,
    Frame,
    LabelFrame,
    Label,
    LEFT,
    RIGHT,
    Scrollbar,
    TclError,
    Text,
    TOP,
    Toplevel,
    VERTICAL,
    X,
    Y
)


from .treeview import LazyLoadingTreeView
from ..abc.meta import Loggable


class PyroxFrame(LabelFrame, Loggable):

    def __init__(self, *args, **kwargs):
        if 'context_menu' in kwargs:  # this is gross, but it works
            del kwargs['context_menu']
        if 'controller' in kwargs:  # this is gross, but it works
            del kwargs['controller']
        if 'parent' in kwargs:  # this is gross, but it works
            del kwargs['parent']
        LabelFrame.__init__(self,
                            *args,
                            borderwidth=4,
                            padx=4,
                            pady=4,
                            relief=GROOVE,
                            **kwargs)
        Loggable.__init__(self)


class PyroxTopLevelFrame(Toplevel, Loggable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def center(self):
        """Center the toplevel window on the screen."""
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')


class LogWindow(PyroxFrame):
    """tkinter :class:`LabelFrame` with user logic and attributes packed on top.

    Intended for use as a log window

    .. ------------------------------------------------------------

    .. package:: types.utkinter.frames

    .. ------------------------------------------------------------

    Attributes
    -----------
    xxx

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         text='Logger',
                         **kwargs)

        self._logtext = Text(self, state='disabled', background='black', foreground='white', wrap='word')
        vscrollbar = Scrollbar(self, orient=VERTICAL, command=self._logtext.yview)
        self._logtext['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._logtext.pack(side=BOTTOM, fill=BOTH, expand=True)

    @property
    def log_text(self) -> Optional[Text]:
        """get the log entry text attr

        Returns:
            Text | None: text
        """
        return self._logtext

    def log(self, message: str):
        """Log a message to the log text area.

        Args:
            message (str): The message to log.
        """

        severity = WARNING if '| WARNING | ' in message else \
            ERROR if '| ERROR | ' in message else INFO

        try:
            self._logtext.config(state='normal')
            msg_begin = self._logtext.index('end-1c')
            self._logtext.insert('end', f'{message}\n')
            msg_end = self._logtext.index('end-1c')
            self._logtext.tag_add(message, msg_begin, msg_end)
            self._logtext.tag_config(message,
                                     foreground='black' if severity == WARNING else 'white',
                                     background='yellow' if severity == WARNING else 'red' if severity == ERROR else 'black',
                                     font=('Courier New', 12, 'bold'))
            self._logtext.see('end')
            line_count = self._logtext.count('1.0', 'end', 'lines')[0]
            if line_count > 100:
                dlt_count = abs(line_count - 100) + 1
                self._logtext.delete('1.0', float(dlt_count))
            self._logtext.config(state='disabled')
        except TclError as e:
            print('Tcl error, original msg -> %s' % e)
        self.update()


class FrameWithTreeViewAndScrollbar(PyroxFrame):
    def __init__(self,
                 *args,
                 base_gui_class: type = None,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)

        self._tree: LazyLoadingTreeView = LazyLoadingTreeView(master=self,
                                                              base_gui_class=base_gui_class,
                                                              columns=('Value',),
                                                              show='tree headings',
                                                              context_menu=kwargs.get('context_menu', None))
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')

        vscrollbar = Scrollbar(self,
                               orient=VERTICAL,
                               command=self._tree.yview)
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._tree.pack(fill=BOTH, expand=True)

    @property
    def tree(self) -> LazyLoadingTreeView:
        """get the tree view of this organizer window

        Returns:
            ttk.Treeview: tree view
        """
        return self._tree

    @tree.setter
    def tree(self, value: LazyLoadingTreeView):
        """set the tree view of this organizer window

        Args:
            value (ttk.Treeview): tree view to set
        """
        if isinstance(value, LazyLoadingTreeView):
            self._tree = value
            self._tree.pack(fill=BOTH, expand=True)
        else:
            raise TypeError(f'Expected LazyLoadingTreeView, got {type(value)}')


class TaskFrame(Frame):
    """A frame for tasks in the application.

    This frame is intended to be used as a base class for task-specific frames.
    It inherits from `PyroxFrame` and can be extended with additional functionality.

    .. ------------------------------------------------------------

    .. package:: models.utkinter.frames

    .. ------------------------------------------------------------
    """

    def __init__(self,
                 *args,
                 name: str = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name or 'Task Frame'
        self._title_bar = Frame(self, height=20, bg='lightgrey')

        self._close_button = Button(self._title_bar,
                                    text='X',
                                    command=self.destroy,
                                    width=3,)
        self._close_button.pack(side=RIGHT, padx=5, pady=5)

        self._title_label = Label(self._title_bar, text=name or 'Task Frame', bg='lightgrey')
        self._title_label.pack(side=LEFT, padx=5, pady=5)

        self._title_bar.pack(fill=X, side=TOP)

        self._content_frame = Frame(self)
        self._content_frame.pack(fill=BOTH, expand=True, side=TOP)

        self._on_destroy: list[callable] = []

    @property
    def content_frame(self) -> Frame:
        """get the content frame of this task frame

        Returns:
            Frame: content frame
        """
        return self._content_frame

    @property
    def name(self) -> str:
        """get the name of this task frame

        Returns:
            str: name of the task frame
        """
        return self._name

    @property
    def on_destroy(self) -> list[callable]:
        """get the list of callbacks to be called on destroy

        Returns:
            list[callable]: list of callbacks
        """
        return self._on_destroy

    def destroy(self):
        """Destroy the task frame and call all registered callbacks."""
        for callback in self._on_destroy:
            if callable(callback):
                callback()
            else:
                self.logger.warning(f'Callback {callback} is not callable.')
        return super().destroy()


class ToplevelWithTreeViewAndScrollbar(PyroxTopLevelFrame):
    def __init__(self,
                 *args,
                 text: str = None,
                 **kwargs):
        super().__init__(*args,
                         text=text,
                         **kwargs)

        self._tree: LazyLoadingTreeView = LazyLoadingTreeView(master=self,
                                                              columns=('Value',),
                                                              show='tree headings')
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')

        vscrollbar = Scrollbar(self,
                               orient=VERTICAL,
                               command=self._tree.yview)
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._tree.pack(fill=BOTH, expand=True)

    @property
    def tree(self) -> LazyLoadingTreeView:
        """get the tree view of this organizer window

        Returns:
            ttk.Treeview: tree view
        """
        return self._tree


@dataclass
class ObjectEditField:
    property_name: str
    display_name: str
    display_type: Widget
    editable: bool = False


class ObjectEditTaskFrame(TaskFrame):
    """A task frame for editing objects.

    This frame is intended to be used as a base class for object-specific edit frames.
    It inherits from `TaskFrame` and can be extended with additional functionality.

    .. ------------------------------------------------------------

    .. package:: models.gui.frames

    .. ------------------------------------------------------------
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
        for prop, var in self._property_vars.items():
            # Try to set the property if it has a setter
            try:
                setattr(self._object, prop, var.get())
            except Exception as e:
                messagebox.showerror("Error", f"Could not set {prop}: {e}")
        self.destroy()

    def _on_cancel(self):
        self.destroy()

    def _populate_entries(self,
                          object_: Any,
                          properties: list[ObjectEditField]):
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


class ValueEditPopup(PyroxTopLevelFrame):
    """
    Popup dialog for editing a value.
    Usage:
        popup = ValueEditPopup(parent, value, callback)
        - parent: parent window
        - value: initial value to display
        - callback: function(new_value) called if user accepts
    """

    def __init__(self,
                 parent,
                 value,
                 callback,
                 title="Modify Value"):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.callback = callback
        self.result = None

        self.label = Label(self, text="Modify value:")
        self.label.pack(padx=10, pady=(10, 0))

        self.entry = Entry(self)
        self.entry.insert(0, str(value))
        self.entry.pack(padx=10, pady=5, fill='x')
        self.entry.focus_set()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=(0, 10))

        self.ok_button = Button(button_frame, text="OK", width=10, command=self.on_ok)
        self.ok_button.pack(side='left', padx=5)
        self.cancel_button = Button(button_frame, text="Cancel", width=10, command=self.on_cancel)
        self.cancel_button.pack(side='left', padx=5)

        self.bind("<Return>", lambda event: self.on_ok())
        self.bind("<Escape>", lambda event: self.on_cancel())

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.wait_window(self)

    def on_ok(self):
        self.result = self.entry.get()
        if self.callback:
            self.callback(self.result)
        self.destroy()

    def on_cancel(self):
        self.destroy()


class WatchTableTaskFrame(TaskFrame):
    """
    A task frame that behaves like a watch table for programming.
    Each entry is a drop-down (combobox) with auto-complete and allows text entry.
    """

    def __init__(self, master, watch_items=None, all_symbols=None, name="Watch Table"):
        """
        Args:
            master: Parent widget.
            watch_items: List of initial watched symbols (strings).
            all_symbols: List of all possible symbols for auto-complete.
            name: Frame name.
        """
        super().__init__(master=master, name=name)
        self._watch_items = watch_items or []
        self._all_symbols = all_symbols or []
        self._comboboxes = []
        self._setup_table()

    def _setup_table(self):
        header = tk.Frame(self.content_frame)
        header.pack(fill=tk.X, pady=(5, 0))
        tk.Label(header, text="Symbol", width=30, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Value", width=20, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Button(header, text="+", command=self._add_row, width=3).pack(side=tk.LEFT, padx=5)

        self._rows_frame = tk.Frame(self.content_frame)
        self._rows_frame.pack(fill=tk.BOTH, expand=True)

        for symbol in self._watch_items:
            self._add_row(symbol)

    def _add_row(self, symbol=""):
        row = tk.Frame(self._rows_frame)
        row.pack(fill=tk.X, pady=2)

        symbol_var = tk.StringVar(value=symbol)
        value_var = tk.StringVar(value="")

        # Combobox with auto-complete and text entry
        combo = ttk.Combobox(row, textvariable=symbol_var, values=self._all_symbols, width=30)
        combo.pack(side=tk.LEFT, padx=5)
        combo['state'] = 'normal'  # allow text entry

        # Optional: implement auto-complete on key release
        combo.bind('<KeyRelease>', lambda e, cb=combo: self._autocomplete(cb))

        value_entry = ttk.Entry(row, textvariable=value_var, width=20)
        value_entry.pack(side=tk.LEFT, padx=5)

        remove_btn = tk.Button(row, text="–", command=lambda: self._remove_row(row), width=3)
        remove_btn.pack(side=tk.LEFT, padx=5)

        self._comboboxes.append((combo, value_entry, symbol_var, value_var))

    def _remove_row(self, row):
        row.destroy()

    def _autocomplete(self, combobox):
        pattern = combobox.get()
        if not pattern:
            combobox['values'] = self._all_symbols
            return
        filtered = [s for s in self._all_symbols if pattern.lower() in s.lower()]
        combobox['values'] = filtered

    def get_watch_table(self):
        """Return a list of (symbol, value) for all rows."""
        result = []
        for combo, value_entry, symbol_var, value_var in self._comboboxes:
            symbol = symbol_var.get()
            value = value_var.get()
            if symbol:
                result.append((symbol, value))
        return result