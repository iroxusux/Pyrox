"""
Text Editor Widget for Pyrox applications.

This module provides a GUI widget for editing text (primarily YAML) files with
syntax highlighting, validation, and convenient save/load operations.  The
editor integrates with the Pyrox theming system and provides real-time YAML
validation.

Usage:
    Embedded in an application::

        >>> from pyrox.models.gui.texteditor import TextEditorFrame
        >>> editor = TextEditorFrame(parent=my_widget)
        >>> editor.set_content("key: value")

    Standalone demo::

        >>> python pyrox/models/gui/texteditor.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

import yaml
from pyrox.models.gui.frame import TaskFrame
from PyQt6.QtCore import Qt, QRect, QSize, QTimer
from PyQt6.QtGui import (
    QColor, QFont, QKeySequence, QPainter, QShortcut,
    QSyntaxHighlighter, QTextCharFormat,
)
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QMessageBox, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from pyrox.models.gui.theme import DefaultTheme

__all__ = ('TextEditorFrame',)


# ---------------------------------------------------------------------------
# Syntax Highlighter
# ---------------------------------------------------------------------------

class _YamlHighlighter(QSyntaxHighlighter):
    """Lightweight YAML syntax highlighter for QTextDocument."""

    def __init__(self, doc) -> None:
        super().__init__(doc)

        def _fmt(color: str) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            return f

        self._comment_fmt = _fmt('#6a9955')
        self._key_fmt = _fmt('#9cdcfe')
        self._string_fmt = _fmt('#ce9178')
        self._number_fmt = _fmt('#b5cea8')
        self._bool_null_fmt = _fmt('#569cd6')

        self._bool_re = re.compile(r'\b(true|false|yes|no|on|off)\b', re.IGNORECASE)
        self._null_re = re.compile(r'\b(null|none|~)\b', re.IGNORECASE)
        self._number_re = re.compile(r'\b-?\d+(?:\.\d+)?\b')
        self._key_re = re.compile(r'^(\s*(?:-\s+)?)(\S[^:]*?)(?=\s*:(?:\s|$))')
        self._comment_re = re.compile(r'#.*')

    def highlightBlock(self, text: str | None) -> None:  # type: ignore[override]
        if not text:
            return
        # Key (text before colon)
        m = self._key_re.match(text)
        if m:
            self.setFormat(m.start(2), m.end(2) - m.start(2), self._key_fmt)

        # String value (text after ': ')
        colon_pos = text.find(':')
        if colon_pos >= 0 and colon_pos + 1 < len(text):
            value_part = text[colon_pos + 1:]
            value_strip = value_part.strip()
            if value_strip and not value_strip.startswith('#'):
                val_start = colon_pos + 1 + len(value_part) - len(value_part.lstrip())
                self.setFormat(val_start, len(value_strip), self._string_fmt)

        # Booleans / nulls / numbers (override string colour)
        for pattern, fmt in (
            (self._bool_re, self._bool_null_fmt),
            (self._null_re, self._bool_null_fmt),
            (self._number_re, self._number_fmt),
        ):
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)

        # Comments — must be applied last so they override everything
        m = self._comment_re.search(text)
        if m:
            self.setFormat(m.start(), len(text) - m.start(), self._comment_fmt)


# ---------------------------------------------------------------------------
# Line Number Area
# ---------------------------------------------------------------------------

class _LineNumberArea(QWidget):
    """Narrow left-side widget that draws line numbers for _EditorWidget."""

    def __init__(self, editor: '_EditorWidget') -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self._editor.paint_line_numbers(event)


# ---------------------------------------------------------------------------
# Internal QPlainTextEdit subclass
# ---------------------------------------------------------------------------

class _EditorWidget(QPlainTextEdit):
    """QPlainTextEdit that hosts the optional line-number gutter and handles Tab."""

    def __init__(self, frame: 'TextEditorFrame') -> None:
        super().__init__(frame.root)
        self._frame = frame
        self._line_number_area: Optional[_LineNumberArea] = None

        if frame._show_line_numbers:
            self._line_number_area = _LineNumberArea(self)
            self.blockCountChanged.connect(self._update_width)
            self.updateRequest.connect(self._update_area)
            self._update_width()

    # -- line number helpers --

    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 4 + self.fontMetrics().horizontalAdvance('9') * (digits + 1)

    def _update_width(self, _: int = 0) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_area(self, rect: QRect, dy: int) -> None:
        if self._line_number_area is None:
            return
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )
        vp = self.viewport()
        if vp is not None and rect.contains(vp.rect()):
            self._update_width()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self._line_number_area is not None:
            cr = self.contentsRect()
            self._line_number_area.setGeometry(
                QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
            )

    def paint_line_numbers(self, event) -> None:
        if self._line_number_area is None:
            return
        t = DefaultTheme()
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(t.background))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor('#858585'))
                painter.drawText(
                    0, top,
                    self._line_number_area.width() - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_num + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_num += 1

    # -- Tab / Shift+Tab indentation --

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText(' ' * self._frame._tab_size)
            return
        if event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()
            block_text = cursor.block().text()
            spaces = self._frame._tab_size
            if block_text.startswith(' ' * spaces):
                cursor.movePosition(cursor.MoveOperation.StartOfLine)
                cursor.movePosition(
                    cursor.MoveOperation.Right,
                    cursor.MoveMode.KeepAnchor,
                    spaces,
                )
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
            return
        super().keyPressEvent(event)


# ---------------------------------------------------------------------------
# Main Frame Widget
# ---------------------------------------------------------------------------

class TextEditorFrame(TaskFrame):
    """
    A text editor widget with YAML syntax highlighting and validation.

    Features:
    - Load and save YAML files
    - Real-time YAML validation
    - Syntax highlighting for YAML structures
    - Optional line number gutter
    - Undo/redo via Ctrl+Z / Ctrl+Y
    - Auto-indentation (Tab inserts spaces, Shift+Tab removes them)
    - Validation error panel
    - Pyrox theme integration
    - File path and modified-state tracking

    Args:
        parent: Parent widget.
        font: Editor font (default: Consolas 10).
        auto_validate: Enable debounced validation on content change.
        show_line_numbers: Display a line number gutter.
        tab_size: Spaces inserted per Tab key press.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        font: Optional[QFont] = None,
        auto_validate: bool = True,
        show_line_numbers: bool = True,
        tab_size: int = 2,
    ) -> None:
        if parent is None:
            app = QApplication
            if app is None:
                raise RuntimeError("TextEditorFrame requires a parent widget or an active QApplication.")
            parent = app.activeWindow() or QWidget()

        super().__init__(name='Text Editor Frame', parent=parent)

        self._font = font or QFont('Consolas', 10)
        self._auto_validate = auto_validate
        self._show_line_numbers = show_line_numbers
        self._tab_size = tab_size

        # State
        self._current_file: Optional[Path] = None
        self._modified: bool = False
        self._last_validated_content: str = ""
        self._validation_errors: list[str] = []

        # Debounce timer for auto-validation
        self._validate_timer = QTimer(self.root)
        self._validate_timer.setSingleShot(True)
        self._validate_timer.setInterval(500)
        self._validate_timer.timeout.connect(self.validate_yaml)

        # User-assignable callbacks
        self.on_file_loaded: Optional[Callable[[Path], None]] = None
        self.on_file_saved: Optional[Callable[[Path], None]] = None
        self.on_content_changed: Optional[Callable[[str], None]] = None
        self.on_validation_changed: Optional[Callable[[bool, list[str]], None]] = None
        self.on_modified_changed: Optional[Callable[[bool], None]] = None

        self._build_ui()
        self._setup_bindings()
        self._update_status()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        t = DefaultTheme()
        root = QVBoxLayout(self.root)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._make_hsep())

        self._text_editor = _EditorWidget(self)
        self._text_editor.setFont(self._font)
        self._text_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._text_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {t.widget_background};
                color: #d4d4d4;
                selection-background-color: #264f78;
                selection-color: white;
                border: none;
            }}
        """)
        root.addWidget(self._text_editor, stretch=1)

        self._highlighter = _YamlHighlighter(self._text_editor.document())

        root.addWidget(self._make_hsep())

        self._lbl_status = QLabel("Untitled | Valid YAML")
        self._lbl_status.setStyleSheet(f"padding: 2px 4px; color: {t.foreground};")
        root.addWidget(self._lbl_status)

        # Validation error panel (hidden by default)
        self._error_group = QGroupBox("Validation Errors")
        err_layout = QVBoxLayout(self._error_group)
        err_layout.setContentsMargins(4, 4, 4, 4)
        self._error_display = QPlainTextEdit()
        self._error_display.setReadOnly(True)
        self._error_display.setMaximumHeight(80)
        self._error_display.setFont(QFont('Consolas', 9))
        self._error_display.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {t.background};
                color: #f48771;
                border: none;
            }}
        """)
        err_layout.addWidget(self._error_display)
        self._error_group.setVisible(False)
        root.addWidget(self._error_group)

    def _build_toolbar(self) -> QWidget:
        toolbar = QWidget()
        h = QHBoxLayout(toolbar)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(2)

        for text, slot in (
            ("New",     self.new_file),
            ("Open",    self.open_file),
            ("Save",    self.save_file),
            ("Save As", self.save_file_as),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addWidget(self._make_vsep())

        for text, slot in (
            ("Validate", self.validate_yaml),
            ("Format",   self.format_yaml),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            h.addWidget(btn)

        h.addStretch()

        self._lbl_modified = QLabel("")
        self._lbl_modified.setStyleSheet("color: red; font-weight: bold;")
        h.addWidget(self._lbl_modified)

        return toolbar

    @staticmethod
    def _make_hsep() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    @staticmethod
    def _make_vsep() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        return sep

    # ------------------------------------------------------------------
    # Event bindings / shortcuts
    # ------------------------------------------------------------------

    def _setup_bindings(self) -> None:
        doc = self._text_editor.document()
        assert doc is not None
        doc.contentsChanged.connect(self._on_content_changed)
        if self._auto_validate:
            doc.contentsChanged.connect(lambda: self._validate_timer.start())
        QShortcut(QKeySequence.StandardKey.Save, self._text_editor, self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self._text_editor, self.save_file_as)

    # ------------------------------------------------------------------
    # Content change / modified state
    # ------------------------------------------------------------------

    def _on_content_changed(self) -> None:
        self._set_modified(True)
        if self.on_content_changed:
            try:
                self.on_content_changed(self.get_content())
            except Exception as e:
                print(f"Error in on_content_changed callback: {e}")

    def _set_modified(self, modified: bool) -> None:
        if self._modified != modified:
            self._modified = modified
            self._update_status()
            if self.on_modified_changed:
                try:
                    self.on_modified_changed(modified)
                except Exception as e:
                    print(f"Error in on_modified_changed callback: {e}")

    def _update_status(self) -> None:
        self._lbl_modified.setText("●" if self._modified else "")
        name = self._current_file.name if self._current_file else "Untitled"
        n_err = len(self._validation_errors)
        status = f"File: {name}" if self._current_file else name
        status += f" | {n_err} validation error(s)" if n_err else " | Valid YAML"
        self._lbl_status.setText(status)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def new_file(self) -> None:
        """Clear the editor and reset state."""
        if self._modified and not self._confirm_discard():
            return
        self._text_editor.clear()
        self._current_file = None
        self._validation_errors = []
        self._set_modified(False)
        self._update_status()

    def open_file(self, file_path: Optional[Path] = None) -> bool:
        """Open a YAML file, prompting for a path if none is provided."""
        if self._modified and not self._confirm_discard():
            return False

        if file_path is None:
            path_str, _ = QFileDialog.getOpenFileName(
                self.root, "Open YAML File", "",
                "YAML files (*.yaml *.yml);;All files (*.*)",
            )
            if not path_str:
                return False
            file_path = Path(path_str)

        try:
            content = file_path.read_text(encoding='utf-8')
            self._text_editor.setPlainText(content)
            self._current_file = file_path
            self._set_modified(False)
            self.validate_yaml()
            if self.on_file_loaded:
                try:
                    self.on_file_loaded(file_path)
                except Exception as e:
                    print(f"Error in on_file_loaded callback: {e}")
            QMessageBox.information(self.root, "Success", f"File opened: {file_path.name}")
            return True
        except Exception as e:
            QMessageBox.critical(self.root, "Error", f"Failed to open file:\n{e}")
            return False

    def save_file(self) -> bool:
        """Save to the current file, or prompt for a path if unsaved."""
        if self._current_file is None:
            return self.save_file_as()
        return self._save_to_file(self._current_file)

    def save_file_as(self) -> bool:
        """Prompt for a new path and save."""
        path_str, _ = QFileDialog.getSaveFileName(
            self.root, "Save YAML File As", "",
            "YAML files (*.yaml);;YML files (*.yml);;All files (*.*)",
        )
        if not path_str:
            return False
        return self._save_to_file(Path(path_str))

    def _save_to_file(self, file_path: Path) -> bool:
        try:
            if not self.validate_yaml():
                reply = QMessageBox.question(
                    self.root, "Validation Error",
                    "The YAML contains validation errors. Save anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return False

            file_path.write_text(self.get_content(), encoding='utf-8')
            self._current_file = file_path
            self._set_modified(False)
            if self.on_file_saved:
                try:
                    self.on_file_saved(file_path)
                except Exception as e:
                    print(f"Error in on_file_saved callback: {e}")
            QMessageBox.information(self.root, "Success", f"File saved: {file_path.name}")
            return True
        except Exception as e:
            QMessageBox.critical(self.root, "Error", f"Failed to save file:\n{e}")
            return False

    def _confirm_discard(self) -> bool:
        """Prompt to save/discard changes. Returns True if safe to proceed."""
        reply = QMessageBox.question(
            self.root, "Unsaved Changes",
            "You have unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            return self.save_file()
        return True  # Discard

    # ------------------------------------------------------------------
    # YAML validation
    # ------------------------------------------------------------------

    def validate_yaml(self) -> bool:
        """Validate the current content as YAML. Returns True if valid."""
        content = self.get_content()
        if content == self._last_validated_content:
            return not self._validation_errors

        self._last_validated_content = content
        self._validation_errors = []

        if not content.strip():
            self._error_group.setVisible(False)
            self._update_status()
            if self.on_validation_changed:
                try:
                    self.on_validation_changed(True, [])
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")
            return True

        try:
            yaml.safe_load(content)
            self._error_group.setVisible(False)
            self._update_status()
            if self.on_validation_changed:
                try:
                    self.on_validation_changed(True, [])
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")
            return True
        except yaml.YAMLError as exc:
            self._validation_errors.append(str(exc))
            self._error_display.setPlainText(str(exc))
            self._error_group.setVisible(True)
            self._update_status()
            if self.on_validation_changed:
                try:
                    self.on_validation_changed(False, self._validation_errors)
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")
            return False

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def format_yaml(self) -> None:
        """Re-format the YAML content using yaml.dump."""
        content = self.get_content()
        if not content.strip():
            QMessageBox.information(self.root, "Format", "Nothing to format")
            return
        try:
            data = yaml.safe_load(content)
            formatted = yaml.dump(
                data, default_flow_style=False, sort_keys=False, indent=self._tab_size
            )
            self._text_editor.setPlainText(formatted)
            QMessageBox.information(self.root, "Success", "YAML formatted successfully")
        except yaml.YAMLError as e:
            QMessageBox.critical(self.root, "Error", f"Cannot format invalid YAML:\n{e}")

    # ------------------------------------------------------------------
    # Content access
    # ------------------------------------------------------------------

    def get_content(self) -> str:
        """Return the current editor text."""
        return self._text_editor.toPlainText()

    def set_content(self, content: str) -> None:
        """Replace the editor text."""
        self._text_editor.setPlainText(content)

    def get_yaml_data(self) -> Optional[Any]:
        """Parse and return the YAML data, or None if invalid."""
        if not self.validate_yaml():
            return None
        try:
            return yaml.safe_load(self.get_content())
        except Exception:
            return None

    def set_yaml_data(self, data: Any) -> None:
        """Set the editor content from a Python object."""
        try:
            content = yaml.dump(
                data, default_flow_style=False, sort_keys=False, indent=self._tab_size
            )
            self.set_content(content)
        except Exception as e:
            QMessageBox.critical(self.root, "Error", f"Failed to convert data to YAML:\n{e}")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_file(self) -> Optional[Path]:
        """The path of the currently loaded file, or None."""
        return self._current_file

    @property
    def is_modified(self) -> bool:
        """True if the editor has unsaved changes."""
        return self._modified

    @property
    def is_valid(self) -> bool:
        """True if the current content is valid YAML."""
        return not self._validation_errors

    @property
    def validation_errors(self) -> list[str]:
        """A copy of the current validation error messages."""
        return self._validation_errors.copy()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Pyrox Text Editor Demo")
    window.resize(1000, 700)

    editor = TextEditorFrame(auto_validate=True, show_line_numbers=True)
    window.setCentralWidget(editor.root)

    sample_yaml = """\
# Sample YAML Configuration
application:
  name: MyApp
  version: 1.0.0
  author: John Doe

database:
  host: localhost
  port: 5432
  name: mydb
  credentials:
    username: admin
    password: secret123

features:
  - authentication
  - logging
  - caching
  - monitoring

settings:
  debug: true
  timeout: 30
  max_connections: 100
"""

    editor.set_content(sample_yaml)

    def on_validation(is_valid: bool, errors: list[str]) -> None:
        status = "OK" if is_valid else f"FAIL ({len(errors)} error(s))"
        print(f"Validation: {status}")

    editor.on_validation_changed = on_validation

    window.show()
    sys.exit(app.exec())
