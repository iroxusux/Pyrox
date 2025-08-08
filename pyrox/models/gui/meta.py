"""meta gui classes for Pyrox applications.
"""
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
from tkinter import Text
from typing import Callable, Optional


__all__ = [
    'TextWidgetStream',
]


@dataclass
class PyroxDefaultTheme:
    """Default theme for Pyrox applications."""
    name: str = 'pyrox_default'
    background: str = '#202020'
    widget_background: str = '#2b2b2b'
    borderwidth: int = 1
    foreground: str = '#aaaaaa'
    foreground_selected: str = '#FFFFFF'
    relief: str = 'flat'
    font_family: str = 'Consolas'
    font_size: int = 10
    button_color: str = '#2b2b2b'
    button_hover_color: str = '#6e6e6e'
    button_active_color: str = '#2b2b2b'


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
                        'borderwidth': 1,
                    }
                },
                'TNotebook.Tab': {
                    'configure': {
                        'width': 8,
                        'padding': (8, 6),
                        'anchor': 'center',
                        'background': PyroxDefaultTheme.widget_background,
                        'foreground': PyroxDefaultTheme.foreground,
                        'borderwidth': 0,
                        'focuscolor': 'none'
                    },
                    'map': {
                        'background': [
                            ('selected', PyroxDefaultTheme.button_color),
                            ('active', PyroxDefaultTheme.button_hover_color),
                            ('!active', PyroxDefaultTheme.widget_background)
                        ],
                        'foreground': [
                            ('selected', PyroxDefaultTheme.foreground_selected),
                            ('active', PyroxDefaultTheme.foreground_selected),
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
                        'font': (PyroxDefaultTheme.font_family, PyroxDefaultTheme.font_size),
                        'rowheight': 20,
                    },
                    'map': {
                        'background': [
                            ('selected', PyroxDefaultTheme.button_color),
                            ('active', PyroxDefaultTheme.button_hover_color),
                            ('!active', PyroxDefaultTheme.widget_background)
                        ],
                        'foreground': [
                            ('selected', PyroxDefaultTheme.foreground_selected),
                            ('active', PyroxDefaultTheme.foreground_selected),
                            ('!active', PyroxDefaultTheme.foreground_selected)
                        ]
                    }
                },
                'Treeview.Heading': {
                    'configure': {
                        'background': PyroxDefaultTheme.background,
                        'foreground': PyroxDefaultTheme.foreground_selected,
                        'borderwidth': 0,
                        'relief': 'raised',
                        'font': (PyroxDefaultTheme.font_family, PyroxDefaultTheme.font_size, 'bold'),
                        'padding': (5, 5),
                    },
                    'map': {
                        'background': [
                            ('active', PyroxDefaultTheme.button_hover_color),
                            ('pressed', PyroxDefaultTheme.button_active_color),
                            ('!active', PyroxDefaultTheme.background)
                        ],
                        'foreground': [
                            ('active', PyroxDefaultTheme.foreground_selected),
                            ('pressed', PyroxDefaultTheme.foreground_selected),
                            ('!active', PyroxDefaultTheme.foreground_selected)
                        ]
                    }
                },
                'Treeview.Item': {
                    'configure': {
                        'padding': (2, 2),
                    },
                    'map': {
                        'background': [
                            ('selected', PyroxDefaultTheme.button_color),
                            ('active', PyroxDefaultTheme.button_hover_color),
                            ('!active', PyroxDefaultTheme.widget_background)
                        ],
                        'foreground': [
                            ('selected', PyroxDefaultTheme.foreground),
                            ('active', PyroxDefaultTheme.foreground_selected),
                            ('!active', PyroxDefaultTheme.foreground)
                        ]
                    }
                }
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
        show_tree_lines: bool = True,
        stripe_rows: bool = True,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        self.show_tree_lines = show_tree_lines
        self.stripe_rows = stripe_rows
        self._configure_style()

    def _configure_style(self) -> None:
        # Ensure shared theme is created and applied
        PyroxThemeManager.ensure_theme_created()
        self._configure_additional_options()

    def _fallback_styling(self) -> None:
        """Fallback styling if theme creation fails."""
        style = ttk.Style()

        # Create unique style name
        treeview_style = f'Pyrox{id(self)}.Treeview'
        heading_style = f'Pyrox{id(self)}.Treeview.Heading'

        # Configure treeview
        style.configure(
            treeview_style,
            background=PyroxDefaultTheme.widget_background,
            foreground=PyroxDefaultTheme.foreground,
            fieldbackground=PyroxDefaultTheme.widget_background,
            borderwidth=1,
            relief='flat',
            rowheight=25
        )

        # Configure headings
        style.configure(
            heading_style,
            background=PyroxDefaultTheme.background,
            foreground=PyroxDefaultTheme.foreground_selected,
            borderwidth=1,
            relief='raised',
            font=(PyroxDefaultTheme.font_family, PyroxDefaultTheme.font_size, 'bold')
        )

        # Map state-based styling
        style.map(
            treeview_style,
            background=[
                ('selected', PyroxDefaultTheme.button_color),
                ('active', PyroxDefaultTheme.button_hover_color)
            ],
            foreground=[
                ('selected', PyroxDefaultTheme.foreground_selected),
                ('active', PyroxDefaultTheme.foreground_selected)
            ]
        )

        style.map(
            heading_style,
            background=[('active', PyroxDefaultTheme.button_hover_color)],
            foreground=[('active', PyroxDefaultTheme.foreground_selected)]
        )

        # Apply styles
        self.configure(style=treeview_style)

    def _configure_additional_options(self) -> None:
        """Configure additional treeview-specific options."""
        # Configure selection mode
        self.configure(selectmode='extended')

        # Configure tree lines if requested
        if self.show_tree_lines:
            self.configure(show='tree headings')
        else:
            self.configure(show='headings')

        # Set up alternating row colors if requested
        if self.stripe_rows:
            self._setup_alternating_rows()

    def _setup_alternating_rows(self) -> None:
        """Set up alternating row colors for better readability."""
        # Configure tag for alternating rows
        self.tag_configure('oddrow',
                           background=PyroxDefaultTheme.widget_background,
                           foreground=PyroxDefaultTheme.foreground)
        self.tag_configure('evenrow',
                           background='#353535',  # Slightly lighter than widget_background
                           foreground=PyroxDefaultTheme.foreground)

        # Bind to item insertion to apply alternating colors
        self.bind('<<TreeviewSelect>>', self._on_treeview_select)

    def _on_treeview_select(self, event=None) -> None:
        """Handle treeview selection events."""
        # Custom selection handling can go here
        pass

    def insert_with_style(self, parent: str, index: str, iid: str = None, **kwargs) -> str:
        """Insert an item with automatic alternating row styling."""
        item_id = super().insert(parent, index, iid, **kwargs)

        if self.stripe_rows:
            # Apply alternating row colors
            children = self.get_children(parent)
            child_index = children.index(item_id)

            if child_index % 2 == 0:
                self.item(item_id, tags=('evenrow',))
            else:
                self.item(item_id, tags=('oddrow',))

        return item_id

    def configure_column(self, column: str, **options) -> None:
        """Enhanced column configuration with default styling."""
        default_options = {
            'anchor': 'w',
            'minwidth': 50,
            'stretch': True
        }
        default_options.update(options)

        self.column(column, **default_options)

        # Configure heading with default styling
        if 'text' in options:
            self.heading(column, text=options['text'], anchor='w')

    def add_column(self, column_id: str, text: str, width: int = 100, **options) -> None:
        """Add a column with consistent styling."""
        # Add to columns list
        current_columns = list(self['columns'])
        current_columns.append(column_id)
        self.configure(columns=current_columns)

        # Configure the column
        column_options = {
            'width': width,
            'text': text,
            **options
        }
        self.configure_column(column_id, **column_options)

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
