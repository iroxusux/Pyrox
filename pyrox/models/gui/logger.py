from typing import Callable, Optional, TextIO
import tkinter as tk
from tkinter import ttk
from pyrox.models.gui import meta


__all__ = (
    'LogFrame',
)


class LogFrame(meta.PyroxFrame):
    """Enhanced log window that captures both logging and stderr/stdout."""

    def __init__(
        self,
        parent
    ) -> None:
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
            cyan = meta.PyroxDefaultTheme.debug_text
            yellow = meta.PyroxDefaultTheme.warning_background
            red = meta.PyroxDefaultTheme.error_background
            orange = meta.PyroxDefaultTheme.stderr_text
            lightgreen = meta.PyroxDefaultTheme.stdout_text

            match tag:
                case 'INFO':
                    foreground = white
                    background = black
                case 'WARNING':
                    foreground = black
                    background = yellow
                case 'ERROR':
                    foreground = white
                    background = red
                case 'DEBUG':
                    foreground = cyan
                    background = black
                case 'STDERR':
                    foreground = orange
                    background = black
                case 'STDOUT':
                    foreground = lightgreen
                    background = black
                case 'SUCCESS':
                    foreground = lightgreen
                    background = black
                case 'FAILURE':
                    foreground = red
                    background = black
                case _:
                    foreground = white
                    background = black
            self._logtext.tag_configure(message,
                                        foreground=foreground,
                                        background=background,
                                        font=('Courier New', 12, 'bold'))

            # Auto-scroll and limit lines
            self._logtext.see('end')
            lines = int(self._logtext.index('end-1c').split('.')[0])
            if lines > 1000:
                self._logtext.delete('1.0', f'{lines-1000}.0')

            self._logtext.config(state='disabled')

            self._logtext.update_idletasks()
            self.update_idletasks()

        except tk.TclError as e:
            print(f'Error logging message: {e}')

    def add_toolbar_button(
        self,
        text: str, command: Callable
    ) -> ttk.Button:
        """Add a custom button to the toolbar."""

        button = ttk.Button(
            self._toolbar,
            text=text,
            command=command,
        )
        button.pack(side=tk.LEFT, fill=tk.Y)
        return button

    def clear_log_window(self):
        """Clear all text from the log window."""
        try:
            self._logtext.config(state='normal')
            self._logtext.delete('1.0', 'end')
            self._logtext.config(state='disabled')
            self.update()
        except tk.TclError as e:
            print(f'Error clearing log window: {e}')

    def fill_log_from_stream(
        self,
        stream: TextIO,
    ) -> None:
        """Fill the log window from a stream (stdout/stderr)."""
        if not stream:
            return

        for line in stream:
            self.log(line)

    def log(self, message: str):
        """Log a message with automatic severity detection."""
        # Detect severity from message content
        if '| ERROR |' in message:
            tag = 'ERROR'
        elif '| WARNING |' in message:
            tag = 'WARNING'
        elif '| DEBUG |' in message:
            tag = 'DEBUG'
        elif '| SUCCESS |' in message:
            tag = 'SUCCESS'
        elif '| FAILURE |' in message:
            tag = 'FAILURE'
        else:
            tag = 'INFO'

        if not message.endswith('\n'):
            message += '\n'
        self._log_message(message, tag)
