"""Interactive Python terminal frame for Pyrox (PyQt6 implementation).

Provides a sidebar-embeddable console backed by ``code.InteractiveConsole``
so users can evaluate Python expressions against the live interpreter.
"""
import code
import contextlib
import io
import re
import rlcompleter
import sys

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QKeyEvent, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pyrox.models.gui.theme import DefaultTheme

__all__ = ('PythonTerminalFrame',)


def _common_prefix(strings: list[str]) -> str:
    """Return the longest common prefix shared by all strings in *strings*."""
    if not strings:
        return ''
    prefix = strings[0]
    for s in strings[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ''
    return prefix


class PythonTerminalFrame(QFrame):
    """An interactive Python console panel suitable for the sidebar.

    Embeds a ``code.InteractiveConsole`` so the user can evaluate arbitrary
    Python expressions and statements against the live interpreter environment.

    Features:
    - Output area showing stdout / stderr from evaluated code
    - Single-line input field with ``>>>`` / ``...`` prompt feedback
    - Command history navigated with the Up / Down arrow keys
    - Clear button to wipe the output area
    """

    _PROMPT = ">>> "
    _PROMPT_CONT = "... "

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("python_terminal")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self._console = code.InteractiveConsole()
        self._history: list[str] = []
        self._history_index: int = -1
        self._needs_more: bool = False  # waiting for continuation line

        self._setup_ui()
        self._write_welcome()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_separator())
        layout.addWidget(self._build_output_area(), stretch=1)
        layout.addWidget(self._build_input_row())

    def _build_toolbar(self) -> QWidget:
        toolbar = QFrame(self)
        toolbar.setFixedHeight(28)
        toolbar.setStyleSheet(f"background-color: {DefaultTheme.background};")
        tbl = QHBoxLayout(toolbar)
        tbl.setContentsMargins(4, 2, 4, 2)
        tbl.setSpacing(4)

        clear_btn = QPushButton("Clear", toolbar)
        clear_btn.setFixedHeight(22)
        clear_btn.clicked.connect(self._clear)
        tbl.addWidget(clear_btn)
        tbl.addStretch()
        return toolbar

    def _build_separator(self) -> QWidget:
        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"color: {DefaultTheme.bordercolor};")
        return sep

    def _build_output_area(self) -> QTextEdit:
        self._output = QTextEdit(self)
        self._output.setReadOnly(True)
        self._output.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._output.setStyleSheet(
            f"background-color: {DefaultTheme.widget_background};"
            f"color: {DefaultTheme.foreground};"
            f"font-family: {DefaultTheme.font_family}, 'Courier New', monospace;"
            f"font-size: {DefaultTheme.font_size + 2}px;"
            "border: none;"
        )
        return self._output

    def _build_input_row(self) -> QWidget:
        row = QFrame(self)
        row.setStyleSheet(f"background-color: {DefaultTheme.background};")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(4, 3, 4, 3)
        rl.setSpacing(4)

        self._prompt_label = QLabel(self._PROMPT, row)
        self._prompt_label.setStyleSheet(
            f"color: {DefaultTheme.stdout_text};"
            f"font-family: {DefaultTheme.font_family}, 'Courier New', monospace;"
            f"font-size: {DefaultTheme.font_size + 2}px;"
            "background: transparent;"
        )
        rl.addWidget(self._prompt_label)

        self._input = QLineEdit(row)
        self._input.setStyleSheet(
            f"background-color: {DefaultTheme.widget_background};"
            f"color: {DefaultTheme.foreground_selected};"
            f"font-family: {DefaultTheme.font_family}, 'Courier New', monospace;"
            f"font-size: {DefaultTheme.font_size + 2}px;"
            f"border: 1px solid {DefaultTheme.bordercolor};"
            "padding: 1px 4px;"
        )
        self._input.returnPressed.connect(self._on_enter)
        self._input.installEventFilter(self)
        rl.addWidget(self._input, stretch=1)
        return row

    # ------------------------------------------------------------------
    # Welcome message
    # ------------------------------------------------------------------

    def _write_welcome(self) -> None:
        self._append_text(
            f"Python {sys.version}\n"
            "Interactive console — type Python expressions and press Enter.\n\n",
            color=DefaultTheme.foreground,
        )

    # ------------------------------------------------------------------
    # Command execution
    # ------------------------------------------------------------------

    def _on_enter(self) -> None:
        command = self._input.text()
        self._input.clear()
        self._history_index = -1

        # Echo the prompt + command to the output area
        prompt = self._PROMPT_CONT if self._needs_more else self._PROMPT
        self._append_text(prompt + command + "\n", color=DefaultTheme.stdout_text)

        # Record non-empty commands in history
        if command.strip():
            self._history.insert(0, command)

        # Execute and capture stdout/stderr
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            self._needs_more = self._console.push(command)

        if stdout_buf.getvalue():
            self._append_text(stdout_buf.getvalue(), color=DefaultTheme.foreground_selected)
        if stderr_buf.getvalue():
            self._append_text(stderr_buf.getvalue(), color=DefaultTheme.stderr_text)

        # Update the prompt label for the next input
        self._prompt_label.setText(self._PROMPT_CONT if self._needs_more else self._PROMPT)

        # Scroll output to bottom
        self._output.moveCursor(QTextCursor.MoveOperation.End)

    # ------------------------------------------------------------------
    # History navigation & autocomplete (Up / Down / Tab keys)
    # ------------------------------------------------------------------

    def eventFilter(self, watched: object, event: QEvent) -> bool:  # type: ignore[override]
        if watched is self._input and event.type() == QEvent.Type.KeyPress:
            if not isinstance(event, QKeyEvent):
                return super().eventFilter(watched, event)
            # Ignore auto-repeat so holding the key doesn't race through history
            if event.isAutoRepeat():
                return True
            if event.key() == Qt.Key.Key_Up:
                self._history_up()
                return True
            if event.key() == Qt.Key.Key_Down:
                self._history_down()
                return True
            if event.key() == Qt.Key.Key_Tab:
                self._autocomplete()
                return True
        return super().eventFilter(watched, event)

    def _history_up(self) -> None:
        if not self._history:
            return
        self._history_index = min(self._history_index + 1, len(self._history) - 1)
        self._input.setText(self._history[self._history_index])

    def _history_down(self) -> None:
        if self._history_index <= 0:
            self._history_index = -1
            self._input.clear()
            return
        self._history_index -= 1
        self._input.setText(self._history[self._history_index])

    # ------------------------------------------------------------------
    # Autocomplete
    # ------------------------------------------------------------------

    def _autocomplete(self) -> None:
        """Tab-complete the token under the cursor using rlcompleter."""
        text = self._input.text()
        cursor_pos = self._input.cursorPosition()
        before_cursor = text[:cursor_pos]

        stem, completions = self._get_completions(before_cursor)
        if not completions:
            return

        if len(completions) == 1:
            # Single match — replace the stem with the full completion
            replacement = completions[0].rstrip('(')  # strip trailing '(' for callables
            # Preserve anything after the cursor
            after_cursor = text[cursor_pos:]
            new_text = before_cursor[: len(before_cursor) - len(stem)] + replacement + after_cursor
            self._input.setText(new_text)
            self._input.setCursorPosition(len(new_text) - len(after_cursor))
        else:
            # Multiple matches — apply longest common prefix and list options
            common = _common_prefix(completions)
            if len(common) > len(stem):
                after_cursor = text[cursor_pos:]
                new_text = before_cursor[: len(before_cursor) - len(stem)] + common + after_cursor
                self._input.setText(new_text)
                self._input.setCursorPosition(len(new_text) - len(after_cursor))

            # Print the candidates to the output area
            self._append_text(
                "\t".join(c.rstrip('(') for c in completions) + "\n",
                color=DefaultTheme.foreground,
            )

    def _get_completions(self, before_cursor: str) -> tuple[str, list[str]]:
        """Return *(stem, completions)* for the Python token at end of *before_cursor*."""
        match = re.search(r'[\w.]*$', before_cursor)
        stem = match.group(0) if match else ''

        completer = rlcompleter.Completer(self._console.locals)
        completions: list[str] = []
        state = 0
        while True:
            try:
                result = completer.complete(stem, state)
            except Exception:
                break
            if result is None:
                break
            completions.append(result)
            state += 1
        return stem, completions

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------

    def _append_text(self, text: str, color: str = "#cccccc") -> None:
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self._output.setTextCursor(cursor)

    def _clear(self) -> None:
        self._output.clear()
        self._write_welcome()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def focus_input(self) -> None:
        """Give keyboard focus to the input line."""
        self._input.setFocus()
