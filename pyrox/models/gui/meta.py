"""meta gui classes for Pyrox applications.
"""
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from tkinter import Text
from typing import Callable, Optional


__all__ = [
    'TextWidgetStream',
    'PyroxNotebook',
    'PyroxTreeview',
    'PyroxThemeManager',
    'PyroxDefaultTheme',
]


@dataclass
class PyroxDefaultTheme:
    """Default theme for Pyrox applications."""
    name: str = 'pyrox_default'
    background: str = "#2b2b2b"
    background_selected: str = '#4b4b4b'
    background_hover: str = '#3b3b3b'
    widget_background: str = '#101010'
    borderwidth: int = 1
    foreground: str = '#aaaaaa'
    foreground_selected: str = '#FFFFFF'
    foreground_hover: str = "#DDDDDD"
    relief: str = 'flat'
    font_family: str = 'Consolas'
    font_size: int = 10
    button_color: str = '#2b2b2b'
    button_hover: str = '#6e6e6e'
    button_active: str = '#2b2b2b'


class PyroxThemeManager:
    """Centralized theme manager for all Pyrox widgets."""

    _theme_created = False
    _theme_name = 'pyrox_shared_theme'

    @classmethod
    def ensure_theme_created(cls):
        """Ensure the Pyrox theme is created and applied."""
        if cls._theme_created:
            return cls._theme_name

        style = ttk.Style()

        try:
            # Create the shared theme with all widget configurations
            style.theme_create(cls._theme_name, parent='default', settings={
                # Notebook styling
                'TNotebook': {
                    'configure': {
                        'background': PyroxDefaultTheme.background,
                        'borderwidth': 0,
                    }
                },
                'TNotebook.Tab': {
                    'configure': {
                        'width': 8,
                        'padding': (8, 6),
                        'anchor': 'center',
                        'background': PyroxDefaultTheme.background,
                        'foreground': PyroxDefaultTheme.foreground,
                        'borderwidth': 0,
                        'focuscolor': 'none'
                    },
                    'map': {
                        'background': [
                            ('selected', PyroxDefaultTheme.button_color),
                            ('active', PyroxDefaultTheme.button_hover),
                            ('!active', PyroxDefaultTheme.background)
                        ],
                        'foreground': [
                            ('selected', PyroxDefaultTheme.foreground_selected),
                            ('active', PyroxDefaultTheme.foreground_hover),
                            ('!active', PyroxDefaultTheme.foreground)
                        ],
                    }
                },
                # Treeview styling
                'Treeview': {
                    'configure': {
                        'background': PyroxDefaultTheme.widget_background,
                        'foreground': PyroxDefaultTheme.foreground,
                        'fieldbackground': PyroxDefaultTheme.widget_background,
                        'borderwidth': 0,
                        'relief': 'flat',
                        'focuscolor': 'none',
                        'font': (PyroxDefaultTheme.font_family, PyroxDefaultTheme.font_size),
                        'rowheight': 20,
                    },
                    'map': {
                        'background': [
                            ('selected', PyroxDefaultTheme.background_selected),
                        ],
                        'foreground': [
                            ('selected', PyroxDefaultTheme.foreground_selected),
                        ]
                    }
                },
                'Treeview.Heading': {
                    'configure': {
                        'background': PyroxDefaultTheme.widget_background,
                        'foreground': PyroxDefaultTheme.foreground_selected,
                        'borderwidth': 0,
                        'relief': 'raised',
                        'font': (PyroxDefaultTheme.font_family, PyroxDefaultTheme.font_size, 'bold'),
                        'padding': (5, 5),
                    },
                },
            })

            # Apply the theme once
            style.theme_use(cls._theme_name)
            cls._theme_created = True

        except tk.TclError as e:
            print(f"Could not create shared Pyrox theme: {e}")
            cls._theme_name = style.theme_use()  # Fall back to current theme

        return cls._theme_name


class PyroxNotebook(ttk.Notebook):
    """A notebook widget with Pyrox default theme."""

    def __init__(
        self,
        master=None,
        tab_pos: str = 'n',
    ) -> None:
        super().__init__(
            master,
        )
        self._configure_style(tab_pos)

    def _configure_style(self, tab_pos) -> None:
        # Ensure shared theme is created and applied
        PyroxThemeManager.ensure_theme_created()

        style = ttk.Style()
        style.configure('TNotebook', tabposition=tab_pos)


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
        PyroxThemeManager.ensure_theme_created()
        self._configure_additional_options()
        self._setup_hover_tags()

    def _configure_additional_options(self) -> None:
        """Configure additional treeview-specific options."""
        self.configure(show='tree headings')

    def _on_hover(self, event):
        """Handle mouse hover over items."""
        item = self.identify_row(event.y)
        self.tk.call(self, 'tag', 'remove', 'hover')
        self.tk.call(self, 'tag', 'add', 'hover', item)

    def _setup_hover_tags(self):
        """Set up tags for hover effects."""
        # Configure hover tag with your desired color
        self.tag_configure('hover',
                           foreground=PyroxDefaultTheme.foreground_hover,
                           background=PyroxDefaultTheme.background_hover)

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
