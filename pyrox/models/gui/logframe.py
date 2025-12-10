"""Built-in logging window with enhanced features.
Captures both logging and stderr/stdout streams.
"""
import logging
from typing import Callable, Optional, TextIO, Union
import tkinter as tk
from tkinter import ttk
from pyrox.models.gui import meta
from pyrox.models.gui.frame import PyroxFrameContainer
from pyrox.services.logging import LoggingManager, log


__all__ = ('LogFrame',)


class LogFrame(PyroxFrameContainer):
    """Enhanced log window that captures both logging and stderr/stdout.

    Automatically connects to the LoggingManager to display log messages from sys.stdout and sys.stderr.
    """
    TRIM_LENGTH = 1000  # Max number of lines to keep in visual log

    def __init__(
        self,
        parent
    ) -> None:
        super().__init__(master=parent)

        # Create toolbar frame
        self._toolbar = PyroxFrameContainer(
            master=self.frame.root,
            height=30,
        )
        self._toolbar.frame.pack(
            fill=tk.X,
            side=tk.TOP
        )
        self._toolbar.frame.pack_propagate(False)

        self._setup_toolbar()
        self._setup_text_widget()
        self._setup_text_tags()
        self._fill_log_from_sys_streams()
        self._connect_to_logging_manager()

    def _connect_to_logging_manager(self):
        """Connect log frame to logging manager."""
        LoggingManager.register_callback_to_captured_streams(self.log)

    def _fill_log_from_sys_streams(self):
        """Fill the log window from sys.stdout and sys.stderr."""
        err_stream = LoggingManager.unsafe_get_captured_stderr()
        self.clear_log_window()
        lines = err_stream.get_lines()
        if len(lines) > self.TRIM_LENGTH:
            lines = lines[-self.TRIM_LENGTH:]
        self.log(lines)

    def _finalize_msg_log(self) -> None:
        self._logtext.see('end')
        self._trim_log_text_lines()
        self._logtext.config(state='disabled')
        self._logtext.update_idletasks()
        self.frame.update_idletasks()

    @staticmethod
    def _get_msg_colors(tag: str) -> tuple[str, str]:
        match tag:
            case 'INFO':
                foreground = meta.DefaultTheme.stdout_text
                background = meta.DefaultTheme.widget_background
            case 'WARNING':
                foreground = meta.DefaultTheme.widget_background
                background = meta.DefaultTheme.warning_background
            case 'ERROR':
                foreground = meta.DefaultTheme.foreground_selected
                background = meta.DefaultTheme.error_background
            case 'DEBUG':
                foreground = meta.DefaultTheme.debug_text
                background = meta.DefaultTheme.widget_background
            case 'STDERR':
                foreground = meta.DefaultTheme.stderr_text
                background = meta.DefaultTheme.widget_background
            case 'STDOUT':
                foreground = meta.DefaultTheme.stdout_text
                background = meta.DefaultTheme.widget_background
            case 'SUCCESS':
                foreground = meta.DefaultTheme.stdout_text
                background = meta.DefaultTheme.widget_background
            case 'FAILURE':
                foreground = meta.DefaultTheme.error_background
                background = meta.DefaultTheme.widget_background
            case _:
                foreground = meta.DefaultTheme.foreground_selected
                background = meta.DefaultTheme.widget_background
        return foreground, background

    @staticmethod
    def _get_msg_tag(msg: str) -> str:
        """Determine the tag for a log message based on its content."""
        if 'ERROR' in msg or 'Error' in msg or 'error' in msg:
            return 'ERROR'
        elif 'WARNING' in msg or 'Warning' in msg or 'warning' in msg:
            return 'WARNING'
        elif 'DEBUG' in msg or 'Debug' in msg or 'debug' in msg:
            return 'DEBUG'
        else:
            return 'INFO'

    def _handle_dropdown_log_level_change(self, selection: str):
        """Handle changes in log level from dropdown."""
        for level_name, level in LoggingManager.get_all_logging_levels().items():
            if selection == level_name:
                LoggingManager.set_logging_level(level)
                self._fill_log_from_sys_streams()
                return

        self.log(f'| ERROR | Unknown log level selected: {selection}\n')

    def _setup_text_widget(self):
        """Setup the main text widget and scrollbar."""
        text_frame = ttk.Frame(self.frame.root)
        text_frame.pack(
            side=tk.BOTTOM,
            fill=tk.BOTH,
            expand=True
        )

        self._logtext = meta.PyroxText(
            text_frame,
            state='disabled',
            wrap='word',
            font=('Consolas', 9),
            insertbackground='white'
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
            foreground=meta.DefaultTheme.foreground,
            background=meta.DefaultTheme.widget_background
        )
        self._logtext.tag_configure(
            'WARNING',
            foreground=meta.DefaultTheme.widget_background,
            background='yellow'
        )
        self._logtext.tag_configure(
            'ERROR',
            foreground=meta.DefaultTheme.foreground,
            background='red'
        )
        self._logtext.tag_configure(
            'DEBUG',
            foreground='cyan',
            background=meta.DefaultTheme.widget_background
        )

        # Stream types
        self._logtext.tag_configure(
            'STDERR',
            foreground='orange',
            background=meta.DefaultTheme.widget_background
        )
        self._logtext.tag_configure(
            'STDOUT',
            foreground='lightgreen',
            background=meta.DefaultTheme.widget_background
        )

    def _setup_toolbar(self):
        """Setup the toolbar with control buttons."""
        self.add_toolbar_button(
            "Clear",
            self.clear_log_window
        )

        log_levels = list(LoggingManager.get_all_logging_levels().keys())
        curr_level = logging.getLevelName(LoggingManager.curr_logging_level)

        if curr_level not in log_levels:
            raise ValueError(f'Current logging level "{curr_level}" not in available log levels.')

        self.add_toolbar_dropdown(
            log_levels,
            self._handle_dropdown_log_level_change,
            default_option=curr_level
        )

    def _log(
        self,
        message: str,
        levelname: str = 'INFO',
        skip_finalize: bool = False,
    ) -> None:
        """Log a message directly to the text widget."""

        if not message.endswith('\n'):
            message += '\n'

        self._log_message(
            message,
            levelname,
            skip_finalize
        )

    def _log_message(
        self,
        message: str,
        tag: str = 'INFO',
        skip_finalize: bool = False,
    ) -> None:
        """Log a message directly to the text widget."""
        if self._message_is_within_log_level(tag):
            try:
                self._logtext.config(state='normal')

                # Insert message
                start_idx = self._logtext.index('end-1c')
                self._logtext.insert('end', message)
                end_idx = self._logtext.index('end-1c')

                # Apply tag
                foreground, background = self._get_msg_colors(tag)
                self._logtext.tag_add(message, start_idx, end_idx)
                self._logtext.tag_configure(
                    message,
                    foreground=foreground,
                    background=background,
                )

            except tk.TclError as e:
                print(f'Error logging message: {e}')

        if skip_finalize is True:
            return

        self._finalize_msg_log()

    def _message_is_within_log_level(self, tag: str) -> bool:
        match tag:
            case 'DEBUG':
                if LoggingManager.curr_logging_level > logging.DEBUG:
                    return False
            case 'INFO':
                if LoggingManager.curr_logging_level > logging.INFO:
                    return False
            case 'WARNING':
                if LoggingManager.curr_logging_level > logging.WARNING:
                    return False
            case 'ERROR':
                if LoggingManager.curr_logging_level > logging.ERROR:
                    return False
            case 'CRITICAL':
                if LoggingManager.curr_logging_level > logging.CRITICAL:
                    return False
            case 'STDERR' | 'STDOUT' | 'SUCCESS' | 'FAILURE':
                return True
            case _:
                return True
        return True  # Default to True but this should not be reached

    def _trim_log_text_lines(self):
        """Trim log text widget to last 1000 lines."""
        if not self._logtext.cget('state') == 'normal':
            self._logtext.config(state='normal')

        lines = int(self._logtext.index('end-1c').split('.')[0])
        if lines > self.TRIM_LENGTH:
            self._logtext.delete('1.0', f'{lines-self.TRIM_LENGTH}.0')

    def add_toolbar_button(
        self,
        text: str, command: Callable
    ) -> ttk.Button:
        """Add a custom button to the toolbar."""

        button = ttk.Button(
            self._toolbar.frame.root,
            text=text,
            command=command,
            width=8,
            style='TButton'
        )
        button.pack(side=tk.LEFT, fill=tk.Y)
        return button

    def add_toolbar_dropdown(
        self,
        options: list[str],
        command: Callable,
        default_option: Optional[str] = None
    ) -> ttk.OptionMenu:
        """Add a custom dropdown to the toolbar."""
        variable = tk.StringVar(self._toolbar.frame.root)

        if len(options) == 0:
            raise ValueError('Options list cannot be empty.')

        if not default_option:
            default_option = options[0]

        if default_option not in options:
            raise ValueError(f'Default option "{default_option}" not in options list.')

        dropdown = ttk.OptionMenu(
            self._toolbar.frame.root,
            variable,
            default_option,
            *options,
            command=command,
            style='TMenubutton',
        )
        dropdown.pack(side=tk.LEFT, fill=tk.Y)
        dropdown.configure(width=10)  # Width in characters
        return dropdown

    def clear_log_window(self):
        """Clear all text from the log window."""
        try:
            self._logtext.config(state='normal')
            self._logtext.delete('1.0', 'end')
            self._logtext.config(state='disabled')
            self.frame.update()
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

    def log(
        self,
        message: Union[str, list[str]],
        **kwargs
    ) -> None:
        """Log a message with automatic severity detection.
        """
        if isinstance(message, str):
            messages = [message]
        else:
            messages = message

        for msg in messages:
            self._log(
                msg,
                kwargs.get('levelname', self._get_msg_tag(msg)),
                msg is not messages[-1]
            )


if __name__ == '__main__':
    root = tk.Tk()
    root.title("LogFrame Test")
    root.geometry("1000x600")

    toolbar = ttk.Frame(root, height=30)
    toolbar.pack(fill=tk.X, side=tk.TOP)

    generate_pushbutton = ttk.Button(
        toolbar,
        text="Generate 100 Log Messages One-by-One",
        width=20,
        command=lambda: [log('test').info(f"Generated log message {x}.") for x in range(100)]
    )
    generate_pushbutton.pack(side=tk.LEFT, padx=5, pady=5)

    log_frame = LogFrame(root)
    log_frame.frame.pack(fill=tk.BOTH, expand=True)

    # Test logging
    log('test').info("This is an info message.")
    log('test').warning("This is a warning message.")
    log('test').error("This is an error message.")
    log('test').debug("This is a debug message.")
    log('test').info("This is another info message.")

    root.mainloop()
