"""Built-in logging window with enhanced features (PyQt6 implementation).

Captures both logging and stderr/stdout streams.
"""
from collections import deque
import logging
from typing import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.theme import DefaultTheme
from pyrox.services.logging import LoggingManager


__all__ = ('LogFrame',)


class LogFrame(QFrame):
    """Enhanced log window that captures both logging and stderr/stdout.

    Automatically connects to the LoggingManager to display log messages
    from sys.stdout and sys.stderr.

    This is the PyQt6 equivalent of the Tk ``LogFrame``.
    """

    TRIM_LENGTH = 1000  # Max number of lines to keep in the visual log

    def __init__(
        self,
        parent: QWidget | None = None,
        name: str = 'logframe',
    ) -> None:
        super().__init__(parent)
        self.setObjectName(name)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._pending: deque[tuple[str, str]] = deque()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._setup_toolbar(layout)
        self._setup_separator(layout)
        self._setup_text_widget(layout)

        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(50)
        self._flush_timer.timeout.connect(self._flush_pending)
        self._flush_timer.start()

        self._fill_log_from_sys_streams()
        self._connect_to_logging_manager()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_toolbar(self, layout: QVBoxLayout) -> None:
        """Build the toolbar strip at the top of the frame."""
        self._toolbar = QFrame(self)
        self._toolbar.setFixedHeight(28)
        self._toolbar.setStyleSheet(
            f"background-color: {DefaultTheme.background};"
        )
        self._tb_layout = QHBoxLayout(self._toolbar)
        self._tb_layout.setContentsMargins(4, 2, 4, 2)
        self._tb_layout.setSpacing(4)

        self.add_toolbar_button("Clear", self.clear_log_window)

        log_levels = list(LoggingManager.get_all_logging_levels().keys())
        curr_level = logging.getLevelName(LoggingManager.curr_logging_level)
        if curr_level not in log_levels:
            raise ValueError(
                f'Current logging level "{curr_level}" not in available log levels.'
            )
        self._level_combo = self.add_toolbar_dropdown(
            log_levels,
            self._handle_dropdown_log_level_change,
            default_option=curr_level,
        )

        self._tb_layout.addStretch()
        layout.addWidget(self._toolbar)

    def _setup_separator(self, layout: QVBoxLayout) -> None:
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

    def _setup_text_widget(self, layout: QVBoxLayout) -> None:
        """Create the main read-only QTextEdit with Pyrox theme styling."""
        self._text_area = QTextEdit(self)
        self._text_area.setReadOnly(True)
        self._text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._text_area.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {DefaultTheme.widget_background};"
            f"  color: {DefaultTheme.foreground};"
            f"  font-family: '{DefaultTheme.font_family}';"
            f"  font-size: {DefaultTheme.font_size}pt;"
            f"  border: none;"
            f"}}"
        )
        layout.addWidget(self._text_area)

    # ------------------------------------------------------------------
    # LoggingManager integration
    # ------------------------------------------------------------------

    def _connect_to_logging_manager(self) -> None:
        """Subscribe to captured stream output from the LoggingManager."""
        LoggingManager.register_callback_to_captured_streams(self.log)

    def _fill_log_from_sys_streams(self) -> None:
        """Populate the log view from the current captured stderr buffer."""
        err_stream = LoggingManager.unsafe_get_captured_stderr()
        self.clear_log_window()
        lines = err_stream.get_lines()
        if len(lines) > self.TRIM_LENGTH:
            lines = lines[-self.TRIM_LENGTH:]
        self.log(lines)

    # ------------------------------------------------------------------
    # Level / tag helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_msg_colors(tag: str) -> tuple[str, str]:
        """Return ``(foreground, background)`` hex colour strings for *tag*."""
        match tag:
            case 'INFO':
                return DefaultTheme.stdout_text, DefaultTheme.widget_background
            case 'WARNING':
                return DefaultTheme.widget_background, DefaultTheme.warning_background
            case 'ERROR':
                return DefaultTheme.foreground_selected, DefaultTheme.error_background
            case 'DEBUG':
                return DefaultTheme.debug_text, DefaultTheme.widget_background
            case 'STDERR':
                return DefaultTheme.stderr_text, DefaultTheme.widget_background
            case 'STDOUT':
                return DefaultTheme.stdout_text, DefaultTheme.widget_background
            case 'SUCCESS':
                return DefaultTheme.stdout_text, DefaultTheme.widget_background
            case 'FAILURE':
                return DefaultTheme.error_background, DefaultTheme.widget_background
            case _:
                return DefaultTheme.foreground_selected, DefaultTheme.widget_background

    @staticmethod
    def _get_msg_tag(msg: str) -> str:
        """Infer a severity tag from the message content."""
        if 'ERROR' in msg or 'Error' in msg or 'error' in msg:
            return 'ERROR'
        elif 'WARNING' in msg or 'Warning' in msg or 'warning' in msg:
            return 'WARNING'
        elif 'DEBUG' in msg or 'Debug' in msg or 'debug' in msg:
            return 'DEBUG'
        else:
            return 'INFO'

    def _message_is_within_log_level(self, tag: str) -> bool:
        """Return True if *tag* should be displayed at the current log level."""
        match tag:
            case 'DEBUG':
                return LoggingManager.curr_logging_level <= logging.DEBUG
            case 'INFO':
                return LoggingManager.curr_logging_level <= logging.INFO
            case 'WARNING':
                return LoggingManager.curr_logging_level <= logging.WARNING
            case 'ERROR':
                return LoggingManager.curr_logging_level <= logging.ERROR
            case 'CRITICAL':
                return LoggingManager.curr_logging_level <= logging.CRITICAL
            case _:
                return True

    def _handle_dropdown_log_level_change(self, selection: str) -> None:
        """Apply the chosen log level and refresh the display."""
        for level_name, level in LoggingManager.get_all_logging_levels().items():
            if selection == level_name:
                LoggingManager.set_logging_level(level)
                self._fill_log_from_sys_streams()
                return
        self.log(f'| ERROR | Unknown log level selected: {selection}\n')

    # ------------------------------------------------------------------
    # Internal write path
    # ------------------------------------------------------------------

    def _log(
        self,
        message: str,
        levelname: str = 'INFO',
        skip_finalize: bool = False,
    ) -> None:
        if not message.endswith('\n'):
            message += '\n'
        self._log_message(message, levelname, skip_finalize)

    def _log_message(
        self,
        message: str,
        tag: str = 'INFO',
        skip_finalize: bool = False,
    ) -> None:
        if not self._message_is_within_log_level(tag):
            if not skip_finalize:
                self._finalize_msg_log()
            return

        fg, bg = self._get_msg_colors(tag)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(fg))
        fmt.setBackground(QColor(bg))

        cursor = self._text_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message, fmt)

        if not skip_finalize:
            self._finalize_msg_log()

    def _finalize_msg_log(self) -> None:
        """Scroll to the end and trim excess lines."""
        self._trim_log_lines()
        self._text_area.moveCursor(QTextCursor.MoveOperation.End)

    def _trim_log_lines(self) -> None:
        """Trim the document to at most TRIM_LENGTH blocks (lines)."""
        doc = self._text_area.document()
        if doc is None:
            return
        excess = doc.blockCount() - self.TRIM_LENGTH
        if excess <= 0:
            return

        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.NextBlock,
            QTextCursor.MoveMode.KeepAnchor,
            excess,
        )
        cursor.removeSelectedText()

    # ------------------------------------------------------------------
    # Toolbar extension API  (mirrors the Tk LogFrame)
    # ------------------------------------------------------------------

    def _flush_pending(self) -> None:
        """Drain the pending-message queue and write to the text area in one batch."""
        if not self._pending:
            return
        while self._pending:
            msg, levelname = self._pending.popleft()
            self._log(msg, levelname, skip_finalize=True)
        self._finalize_msg_log()

    def add_toolbar_button(
        self,
        text: str,
        command: Callable,
    ) -> QPushButton:
        """Add a button to the toolbar. Returns the created ``QPushButton``."""
        btn = QPushButton(text, self._toolbar)
        btn.setFixedWidth(60)
        btn.clicked.connect(command)
        # Insert before the trailing stretch (last item)
        stretch_idx = self._tb_layout.count()
        self._tb_layout.insertWidget(stretch_idx, btn)
        return btn

    def add_toolbar_dropdown(
        self,
        options: list[str],
        command: Callable,
        default_option: str | None = None,
    ) -> QComboBox:
        """Add a drop-down selector to the toolbar. Returns the ``QComboBox``."""
        if not options:
            raise ValueError('Options list cannot be empty.')
        if default_option is None:
            default_option = options[0]
        if default_option not in options:
            raise ValueError(
                f'Default option "{default_option}" not in options list.'
            )

        combo = QComboBox(self._toolbar)
        for opt in options:
            combo.addItem(opt)
        combo.setCurrentText(default_option)
        combo.setFixedWidth(90)
        combo.currentTextChanged.connect(command)
        stretch_idx = self._tb_layout.count()
        self._tb_layout.insertWidget(stretch_idx, combo)
        return combo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, text: str) -> None:
        """Append *text* to the log (alias for ``log`` with severity detection)."""
        self.log(text)

    def clear_log_window(self) -> None:
        """Clear all text from the log view."""
        self._text_area.clear()

    def fill_log_from_stream(self, stream) -> None:
        """Write every line from *stream* into the log."""
        if not stream:
            return
        for line in stream:
            self.log(line)

    def log(
        self,
        message: str | list[str],
        **kwargs,
    ) -> None:
        """Enqueue *message* for display. Actual rendering is deferred to the
        next timer tick so the event loop stays responsive during long operations.

        Args:
            message: A single string or a list of strings to log.
            **kwargs: Optional ``levelname`` override (e.g. ``levelname='ERROR'``).
        """
        messages = [message] if isinstance(message, str) else message
        for msg in messages:
            levelname = kwargs.get('levelname', self._get_msg_tag(msg))
            self._pending.append((msg, levelname))
