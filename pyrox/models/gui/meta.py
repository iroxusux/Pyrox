"""meta gui classes for Pyrox applications.
"""
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from tkinter import Text
from tkinter.ttk import Widget as TtkWidget
from typing import Callable, Optional, Union
from .theme import DefaultTheme

__all__ = [
    'ObjectEditField',
    'TextWidgetStream',
    'PyroxNotebook',
    'PyroxPanedWindow',
    'PyroxTreeview',
]


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
    display_type: type[Union[tk.Widget, TtkWidget]]
    editable: bool = False


class PyroxNotebook(ttk.Notebook):
    """A notebook widget with Pyrox default theme."""

    def __init__(
        self,
        master=None,
        tab_pos: str = 'n',
    ) -> None:
        self._configure_style(tab_pos)
        super().__init__(master)

    def _configure_style(self, tab_pos) -> None:
        # Ensure shared theme is created and applied

        style = ttk.Style()
        style.configure('TNotebook', tabposition=tab_pos)


class PyroxPanedWindow(ttk.PanedWindow):
    """A custom PanedWindow with built-in logging capabilities.
    """

    def __init__(self, master=None) -> None:
        super().__init__(master)


class PyroxText(Text):
    """A text widget with Pyrox default theme."""

    def __init__(
        self,
        master=None,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self._configure_style()

    def _configure_style(self) -> None:
        self.configure(
            background=DefaultTheme.widget_background,
            foreground=DefaultTheme.foreground,
            insertbackground=DefaultTheme.foreground_selected,
            font=(DefaultTheme.font_family, DefaultTheme.font_size),
            borderwidth=DefaultTheme.borderwidth,
            relief=DefaultTheme.relief,  # type: ignore
        )


class PyroxTreeview(ttk.Treeview):
    """A treeview widget with Pyrox default theme."""

    def __init__(
        self,
        master=None,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self._configure_style()
        self.bind('<Motion>', self._on_hover)

    def _configure_style(self) -> None:
        self._setup_hover_tags()

    def _on_hover(self, event):
        """Handle mouse hover over items."""
        item = self.identify_row(event.y)
        self.tk.call(self, 'tag', 'remove', 'hover')
        self.tk.call(self, 'tag', 'add', 'hover', item)

    def _setup_hover_tags(self):
        """Set up tags for hover effects."""
        # Configure hover tag with your desired color
        self.tag_configure('hover',
                           foreground=DefaultTheme.foreground_hover,
                           background=DefaultTheme.background_hover)

    def clear_all(self) -> None:
        """Clear all items from the treeview."""
        for item in self.get_children():
            self.delete(item)

    def expand_all(self, item: str = '') -> None:
        """Expand all items in the treeview."""
        for child in self.get_children(item):
            self.item(child, open=True)
            self.expand_all(child)

    def collapse_all(self, item: str = '') -> None:
        """Collapse all items in the treeview."""
        for child in self.get_children(item):
            self.item(child, open=False)
            self.collapse_all(child)


class TextWidgetStream:
    """A file-like object that redirects writes to a tkinter Text widget."""

    def __init__(
        self,
        text_widget: Text,
        tag: Optional[str] = None,
        write_callback: Optional[Callable] = None,
    ) -> None:
        self.text_widget = text_widget
        self.tag = tag
        self._closed = False
        self._write_callback: Optional[Callable] = write_callback

    def write(self, string: str) -> int:
        """Write string to the text widget immediately."""
        if self._closed or not string or not string.strip():
            return len(string)

        try:
            if not self.text_widget.winfo_exists():
                return len(string)

            # Force immediate GUI update
            self._write_immediately(string)

        except (tk.TclError, RuntimeError):
            pass
        except Exception:
            pass

        return len(string)

    def _write_immediately(self, text: str):
        """Write to widget immediately without queuing."""
        if self._write_callback:
            return self._write_callback(text)
        try:
            state = self.text_widget.cget('state')
            self.text_widget.config(state='normal')

            self.text_widget.insert('end', text)
            if self.tag:
                start_idx = self.text_widget.index('end-1c linestart')
                end_idx = self.text_widget.index('end-1c')
                self.text_widget.tag_add(self.tag, start_idx, end_idx)

            # Auto-scroll to bottom
            self.text_widget.see('end')

            # Limit text length (keep last 1000 lines)
            lines = int(self.text_widget.index('end-1c').split('.')[0])
            if lines > 1000:
                self.text_widget.delete('1.0', f'{lines-1000}.0')

            self.text_widget.config(state=state)

            # CRITICAL: Force immediate GUI update
            self.text_widget.update_idletasks()

        except tk.TclError as e:
            print(f'Error while writing stream: {e}')

    def flush(self) -> None:
        """Force flush - update GUI immediately."""
        try:
            if self.text_widget.winfo_exists():
                self.text_widget.update_idletasks()
        except Exception:
            pass

    def writelines(self, lines) -> None:
        for line in lines:
            self.write(line)

    def close(self) -> None:
        self._closed = True
