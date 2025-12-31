"""
YAML Editor Widget for Pyrox applications.

This module provides a GUI widget for editing YAML files with syntax highlighting,
validation, and convenient save/load operations. The editor integrates with the
Pyrox theming system and provides real-time YAML validation.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable, Any
from pathlib import Path
import yaml


class PyroxYamlEditor(ttk.Frame):
    """
    A YAML editor widget with syntax highlighting and validation.

    Features:
    - Load and save YAML files
    - Real-time syntax validation
    - Syntax highlighting for YAML structures
    - Line numbers
    - Undo/redo support
    - Find and replace functionality
    - Auto-indentation
    - Validation error display
    - Theme integration
    - File path tracking
    - Modified state tracking

    Args:
        master: Parent widget
        width (int): Width of the editor in characters (default: 80)
        height (int): Height of the editor in lines (default: 24)
        font (tuple): Font specification (default: ('Consolas', 10))
        auto_validate (bool): Enable automatic validation on content change
        show_line_numbers (bool): Display line numbers
        tab_size (int): Number of spaces for tab character
        **kwargs: Additional arguments passed to ttk.Frame
    """

    def __init__(
        self,
        master=None,
        width: int = 80,
        height: int = 24,
        font: tuple = ('Consolas', 10),
        auto_validate: bool = True,
        show_line_numbers: bool = True,
        tab_size: int = 2,
        **kwargs
    ) -> None:
        """Initialize the YAML editor widget."""
        super().__init__(master, **kwargs)

        # Configuration
        self._width = width
        self._height = height
        self._font = font
        self._auto_validate = auto_validate
        self._show_line_numbers = show_line_numbers
        self._tab_size = tab_size

        # State tracking
        self._current_file: Optional[Path] = None
        self._modified: bool = False
        self._last_validated_content: str = ""
        self._validation_errors: list[str] = []

        # Callbacks
        self.on_file_loaded: Optional[Callable[[Path], None]] = None
        self.on_file_saved: Optional[Callable[[Path], None]] = None
        self.on_content_changed: Optional[Callable[[str], None]] = None
        self.on_validation_changed: Optional[Callable[[bool, list[str]], None]] = None
        self.on_modified_changed: Optional[Callable[[bool], None]] = None

        # Build the UI
        self._build_ui()
        self._configure_style()
        self._setup_bindings()

        # Initial state
        self._update_status()

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main container
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Toolbar frame
        self._toolbar = ttk.Frame(self)
        self._toolbar.grid(row=0, column=0, sticky='ew', padx=5, pady=(5, 0))

        # Toolbar buttons
        self._btn_new = ttk.Button(self._toolbar, text="New", command=self.new_file, width=8)
        self._btn_new.pack(side=tk.LEFT, padx=2)

        self._btn_open = ttk.Button(self._toolbar, text="Open", command=self.open_file, width=8)
        self._btn_open.pack(side=tk.LEFT, padx=2)

        self._btn_save = ttk.Button(self._toolbar, text="Save", command=self.save_file, width=8)
        self._btn_save.pack(side=tk.LEFT, padx=2)

        self._btn_save_as = ttk.Button(self._toolbar, text="Save As", command=self.save_file_as, width=8)
        self._btn_save_as.pack(side=tk.LEFT, padx=2)

        ttk.Separator(self._toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self._btn_validate = ttk.Button(self._toolbar, text="Validate", command=self.validate_yaml, width=10)
        self._btn_validate.pack(side=tk.LEFT, padx=2)

        self._btn_format = ttk.Button(self._toolbar, text="Format", command=self.format_yaml, width=10)
        self._btn_format.pack(side=tk.LEFT, padx=2)

        # Modified indicator
        self._lbl_modified = ttk.Label(self._toolbar, text="", foreground='red')
        self._lbl_modified.pack(side=tk.RIGHT, padx=5)

        # Editor frame with line numbers
        self._editor_frame = ttk.Frame(self)
        self._editor_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self._editor_frame.columnconfigure(1, weight=1)
        self._editor_frame.rowconfigure(0, weight=1)

        # Line numbers (if enabled)
        if self._show_line_numbers:
            self._line_numbers = tk.Text(
                self._editor_frame,
                width=4,
                padx=3,
                pady=5,
                takefocus=0,
                border=0,
                background='#2b2b2b',
                foreground='#858585',
                state='disabled',
                wrap='none',
                font=self._font
            )
            self._line_numbers.grid(row=0, column=0, sticky='ns')

        # Main text editor
        self._text_editor = tk.Text(
            self._editor_frame,
            width=self._width,
            height=self._height,
            wrap='none',
            undo=True,
            maxundo=-1,
            font=self._font,
            bg='#1e1e1e',
            fg='#d4d4d4',
            insertbackground='white',
            selectbackground='#264f78',
            selectforeground='white'
        )
        self._text_editor.grid(row=0, column=1, sticky='nsew')

        # Scrollbars
        self._vscroll = ttk.Scrollbar(self._editor_frame, orient=tk.VERTICAL, command=self._text_editor.yview)
        self._vscroll.grid(row=0, column=2, sticky='ns')
        self._text_editor.config(yscrollcommand=self._on_vscroll)

        self._hscroll = ttk.Scrollbar(self._editor_frame, orient=tk.HORIZONTAL, command=self._text_editor.xview)
        self._hscroll.grid(row=1, column=1, sticky='ew')
        self._text_editor.config(xscrollcommand=self._hscroll.set)

        # Validation/Status frame
        self._status_frame = ttk.Frame(self)
        self._status_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=(0, 5))

        # Status label
        self._lbl_status = ttk.Label(self._status_frame, text="Ready", anchor=tk.W)
        self._lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Error display
        self._error_frame = ttk.LabelFrame(self, text="Validation Errors", padding=5)
        self._error_text = tk.Text(
            self._error_frame,
            height=4,
            wrap='word',
            bg='#2b2b2b',
            fg='#f48771',
            font=('Consolas', 9),
            state='disabled'
        )
        self._error_text.pack(fill=tk.BOTH, expand=True)
        # Error frame is hidden by default
        self._error_frame.grid_remove()

    def _configure_style(self) -> None:
        """Configure syntax highlighting tags."""
        # YAML syntax highlighting tags
        self._text_editor.tag_configure('key', foreground='#9cdcfe')
        self._text_editor.tag_configure('string', foreground='#ce9178')
        self._text_editor.tag_configure('number', foreground='#b5cea8')
        self._text_editor.tag_configure('boolean', foreground='#569cd6')
        self._text_editor.tag_configure('comment', foreground='#6a9955')
        self._text_editor.tag_configure('null', foreground='#569cd6')
        self._text_editor.tag_configure('list_marker', foreground='#d4d4d4')
        self._text_editor.tag_configure('error', background='#5a1d1d')

    def _setup_bindings(self) -> None:
        """Set up event bindings."""
        # Content change tracking
        self._text_editor.bind('<<Modified>>', self._on_text_modified)
        self._text_editor.bind('<KeyRelease>', self._on_key_release)

        # Tab key handling
        self._text_editor.bind('<Tab>', self._on_tab)
        self._text_editor.bind('<Shift-Tab>', self._on_shift_tab)

        # Save shortcuts
        self._text_editor.bind('<Control-s>', lambda e: self.save_file())
        self._text_editor.bind('<Control-Shift-S>', lambda e: self.save_file_as())

        # Line number synchronization
        if self._show_line_numbers:
            self._text_editor.bind('<MouseWheel>', self._on_scroll)
            self._text_editor.bind('<Button-4>', self._on_scroll)
            self._text_editor.bind('<Button-5>', self._on_scroll)

    def _on_vscroll(self, *args) -> None:
        """Handle vertical scrolling and sync line numbers."""
        self._vscroll.set(*args)
        if self._show_line_numbers:
            self._line_numbers.yview_moveto(args[0])

    def _on_scroll(self, event) -> None:
        """Handle scroll events to sync line numbers."""
        if self._show_line_numbers:
            self._line_numbers.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_text_modified(self, event) -> None:
        """Handle text modification events."""
        if self._text_editor.edit_modified():
            self._set_modified(True)
            self._update_line_numbers()

            if self._auto_validate:
                self.after(500, self.validate_yaml)  # Debounced validation

            self._text_editor.edit_modified(False)

    def _on_key_release(self, event) -> None:
        """Handle key release for syntax highlighting."""
        # Apply syntax highlighting (simplified)
        if event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
            self.after(50, self._apply_syntax_highlighting)

    def _on_tab(self, event) -> str:
        """Handle Tab key press."""
        # Insert spaces instead of tab
        self._text_editor.insert(tk.INSERT, ' ' * self._tab_size)
        return 'break'

    def _on_shift_tab(self, event) -> str:
        """Handle Shift+Tab key press."""
        # Remove indentation
        line_start = self._text_editor.index('insert linestart')
        line_end = self._text_editor.index('insert lineend')
        line_text = self._text_editor.get(line_start, line_end)

        if line_text.startswith(' ' * self._tab_size):
            self._text_editor.delete(line_start, f"{line_start}+{self._tab_size}c")
        return 'break'

    def _update_line_numbers(self) -> None:
        """Update the line numbers display."""
        if not self._show_line_numbers:
            return

        line_count = int(self._text_editor.index('end-1c').split('.')[0])
        line_numbers = '\n'.join(str(i) for i in range(1, line_count + 1))

        self._line_numbers.config(state='normal')
        self._line_numbers.delete('1.0', tk.END)
        self._line_numbers.insert('1.0', line_numbers)
        self._line_numbers.config(state='disabled')

    def _apply_syntax_highlighting(self) -> None:
        """Apply basic YAML syntax highlighting."""
        # Remove existing tags
        for tag in ['key', 'string', 'number', 'boolean', 'comment', 'null', 'list_marker']:
            self._text_editor.tag_remove(tag, '1.0', tk.END)

        content = self._text_editor.get('1.0', tk.END)
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Comments
            if '#' in line:
                comment_pos = line.index('#')
                comment_start = f"{line_num}.{comment_pos}"
                end = f"{line_num}.end"
                self._text_editor.tag_add('comment', comment_start, end)
                line = line[:comment_pos]  # Process rest without comment

            # List markers
            stripped = line.lstrip()
            if stripped.startswith('- '):
                indent = len(line) - len(stripped)
                start = f"{line_num}.{indent}"
                end = f"{line_num}.{indent + 1}"
                self._text_editor.tag_add('list_marker', start, end)

            # Keys (simple pattern: text followed by colon)
            if ':' in line:
                key_end = line.index(':')
                key_start = 0
                # Find start of key (skip whitespace)
                for i, ch in enumerate(line):
                    if ch not in ' \t-':
                        key_start = i
                        break

                if key_start < key_end:
                    start = f"{line_num}.{key_start}"
                    end = f"{line_num}.{key_end}"
                    self._text_editor.tag_add('key', start, end)

                # Value after colon
                value = line[key_end + 1:].strip()
                if value:
                    value_start = key_end + 1 + len(line[key_end + 1:]) - len(value)

                    # Boolean values
                    if value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off']:
                        start = f"{line_num}.{value_start}"
                        end = f"{line_num}.{value_start + len(value)}"
                        self._text_editor.tag_add('boolean', start, end)
                    # Null values
                    elif value.lower() in ['null', 'none', '~']:
                        start = f"{line_num}.{value_start}"
                        end = f"{line_num}.{value_start + len(value)}"
                        self._text_editor.tag_add('null', start, end)
                    # Numbers
                    elif value.replace('.', '').replace('-', '').isdigit():
                        start = f"{line_num}.{value_start}"
                        end = f"{line_num}.{value_start + len(value)}"
                        self._text_editor.tag_add('number', start, end)
                    # Strings (quoted or not)
                    else:
                        start = f"{line_num}.{value_start}"
                        end = f"{line_num}.{value_start + len(value)}"
                        self._text_editor.tag_add('string', start, end)

    def _set_modified(self, modified: bool) -> None:
        """Set the modified state."""
        if self._modified != modified:
            self._modified = modified
            self._update_status()

            if self.on_modified_changed:
                try:
                    self.on_modified_changed(modified)
                except Exception as e:
                    print(f"Error in on_modified_changed callback: {e}")

    def _update_status(self) -> None:
        """Update the status display."""
        # Update modified indicator
        if self._modified:
            self._lbl_modified.config(text="●")
        else:
            self._lbl_modified.config(text="")

        # Update status label
        if self._current_file:
            file_name = self._current_file.name
            status = f"File: {file_name}"
        else:
            status = "Untitled"

        if self._validation_errors:
            status += f" | {len(self._validation_errors)} validation error(s)"
        else:
            status += " | Valid YAML"

        self._lbl_status.config(text=status)

    def new_file(self) -> None:
        """Create a new empty file."""
        if self._modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new file?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes
                if not self.save_file():
                    return

        self._text_editor.delete('1.0', tk.END)
        self._current_file = None
        self._set_modified(False)
        self._validation_errors = []
        self._update_line_numbers()
        self._update_status()

    def open_file(self, file_path: Optional[Path] = None) -> bool:
        """
        Open a YAML file.

        Args:
            file_path: Path to the file to open. If None, shows file dialog.

        Returns:
            True if file was opened successfully, False otherwise.
        """
        if self._modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before opening a new file?"
            )
            if response is None:  # Cancel
                return False
            elif response:  # Yes
                if not self.save_file():
                    return False

        if file_path is None:
            file_path_str = filedialog.askopenfilename(
                title="Open YAML File",
                filetypes=[
                    ("YAML files", "*.yaml *.yml"),
                    ("All files", "*.*")
                ]
            )
            if not file_path_str:
                return False
            file_path = Path(file_path_str)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._text_editor.delete('1.0', tk.END)
            self._text_editor.insert('1.0', content)
            self._current_file = file_path
            self._set_modified(False)
            self._update_line_numbers()
            self._apply_syntax_highlighting()
            self.validate_yaml()

            if self.on_file_loaded:
                try:
                    self.on_file_loaded(file_path)
                except Exception as e:
                    print(f"Error in on_file_loaded callback: {e}")

            messagebox.showinfo("Success", f"File opened: {file_path.name}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")
            return False

    def save_file(self) -> bool:
        """
        Save the current file.

        Returns:
            True if file was saved successfully, False otherwise.
        """
        if self._current_file is None:
            return self.save_file_as()

        return self._save_to_file(self._current_file)

    def save_file_as(self) -> bool:
        """
        Save the current file with a new name.

        Returns:
            True if file was saved successfully, False otherwise.
        """
        file_path_str = filedialog.asksaveasfilename(
            title="Save YAML File As",
            defaultextension=".yaml",
            filetypes=[
                ("YAML files", "*.yaml"),
                ("YML files", "*.yml"),
                ("All files", "*.*")
            ]
        )
        if not file_path_str:
            return False

        file_path = Path(file_path_str)
        return self._save_to_file(file_path)

    def _save_to_file(self, file_path: Path) -> bool:
        """Save content to a file."""
        try:
            # Validate before saving
            if not self.validate_yaml():
                response = messagebox.askyesno(
                    "Validation Error",
                    "The YAML contains validation errors. Do you want to save anyway?"
                )
                if not response:
                    return False

            content = self._text_editor.get('1.0', 'end-1c')

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self._current_file = file_path
            self._set_modified(False)
            self._update_status()

            if self.on_file_saved:
                try:
                    self.on_file_saved(file_path)
                except Exception as e:
                    print(f"Error in on_file_saved callback: {e}")

            messagebox.showinfo("Success", f"File saved: {file_path.name}")
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")
            return False

    def validate_yaml(self) -> bool:
        """
        Validate the current YAML content.

        Returns:
            True if YAML is valid, False otherwise.
        """
        content = self._text_editor.get('1.0', 'end-1c')

        # Skip validation if content hasn't changed
        if content == self._last_validated_content:
            return len(self._validation_errors) == 0

        self._last_validated_content = content
        self._validation_errors = []

        # Clear error highlighting
        self._text_editor.tag_remove('error', '1.0', tk.END)

        if not content.strip():
            # Empty content is valid
            self._error_frame.grid_remove()
            self._update_status()
            if self.on_validation_changed:
                try:
                    self.on_validation_changed(True, [])
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")
            return True

        try:
            # Parse YAML
            yaml.safe_load(content)

            # Valid YAML
            self._error_frame.grid_remove()
            self._update_status()

            if self.on_validation_changed:
                try:
                    self.on_validation_changed(True, [])
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")

            return True

        except yaml.YAMLError as e:
            # Parse error
            error_msg = str(e)
            self._validation_errors.append(error_msg)

            # Show error frame
            self._error_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=(0, 5))
            self._error_text.config(state='normal')
            self._error_text.delete('1.0', tk.END)
            self._error_text.insert('1.0', error_msg)
            self._error_text.config(state='disabled')

            # Try to highlight error line
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark  # type: ignore
                if mark:
                    line = mark.line + 1
                    col = mark.column
                    start = f"{line}.{col}"
                    end = f"{line}.end"
                    self._text_editor.tag_add('error', start, end)

            self._update_status()

            if self.on_validation_changed:
                try:
                    self.on_validation_changed(False, self._validation_errors)
                except Exception as e:
                    print(f"Error in on_validation_changed callback: {e}")

            return False

    def format_yaml(self) -> None:
        """Format the YAML content."""
        content = self._text_editor.get('1.0', 'end-1c')

        if not content.strip():
            messagebox.showinfo("Format", "Nothing to format")
            return

        try:
            # Parse and dump to format
            data = yaml.safe_load(content)
            formatted = yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                indent=self._tab_size
            )

            # Update editor
            self._text_editor.delete('1.0', tk.END)
            self._text_editor.insert('1.0', formatted)
            self._apply_syntax_highlighting()
            self._update_line_numbers()

            messagebox.showinfo("Success", "YAML formatted successfully")

        except yaml.YAMLError as e:
            messagebox.showerror("Error", f"Cannot format invalid YAML:\n{str(e)}")

    def get_content(self) -> str:
        """Get the current editor content."""
        return self._text_editor.get('1.0', 'end-1c')

    def set_content(self, content: str) -> None:
        """Set the editor content."""
        self._text_editor.delete('1.0', tk.END)
        self._text_editor.insert('1.0', content)
        self._apply_syntax_highlighting()
        self._update_line_numbers()
        self._set_modified(True)

    def get_yaml_data(self) -> Optional[Any]:
        """
        Parse and return the YAML data.

        Returns:
            Parsed YAML data, or None if invalid.
        """
        if not self.validate_yaml():
            return None

        try:
            content = self.get_content()
            return yaml.safe_load(content)
        except Exception:
            return None

    def set_yaml_data(self, data: Any) -> None:
        """
        Set the editor content from Python data.

        Args:
            data: Python data to convert to YAML
        """
        try:
            content = yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                indent=self._tab_size
            )
            self.set_content(content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert data to YAML:\n{str(e)}")

    @property
    def current_file(self) -> Optional[Path]:
        """Get the current file path."""
        return self._current_file

    @property
    def is_modified(self) -> bool:
        """Check if the content has been modified."""
        return self._modified

    @property
    def is_valid(self) -> bool:
        """Check if the current YAML is valid."""
        return len(self._validation_errors) == 0

    @property
    def validation_errors(self) -> list[str]:
        """Get the list of validation errors."""
        return self._validation_errors.copy()


if __name__ == "__main__":
    """Demo/test harness for PyroxYamlEditor widget."""
    print("Starting PyroxYamlEditor demo...")

    # Create test window
    root = tk.Tk()
    root.title("Pyrox YAML Editor Demo")
    root.geometry("1000x700")
    root.configure(bg='#2b2b2b')

    # Main frame
    main_frame = tk.Frame(root, bg='#2b2b2b')
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Title
    title_label = tk.Label(
        main_frame,
        text="Pyrox YAML Editor Demo",
        bg='#2b2b2b',
        fg='white',
        font=('Segoe UI', 16, 'bold')
    )
    title_label.pack(pady=(0, 10))

    # Create the YAML editor
    yaml_editor = PyroxYamlEditor(
        main_frame,
        width=90,
        height=30,
        auto_validate=True,
        show_line_numbers=True
    )
    yaml_editor.pack(fill=tk.BOTH, expand=True)

    # Add some sample YAML content
    sample_yaml = """# Sample YAML Configuration
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

servers:
  production:
    url: https://prod.example.com
    ssl: true
  staging:
    url: https://staging.example.com
    ssl: true
  development:
    url: http://localhost:8000
    ssl: false
"""

    yaml_editor.set_content(sample_yaml)

    # Event log frame
    log_frame = tk.LabelFrame(
        main_frame,
        text="Event Log",
        bg='#2b2b2b',
        fg='white',
        font=('Segoe UI', 10, 'bold')
    )
    log_frame.pack(fill=tk.X, pady=(10, 0))

    log_text = tk.Text(
        log_frame,
        bg='#1e1e1e',
        fg='#00ff00',
        font=('Consolas', 9),
        height=6,
        state='disabled'
    )
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def log_message(message: str):
        """Add a message to the log."""
        log_text.config(state='normal')
        log_text.insert(tk.END, f"{message}\n")
        log_text.see(tk.END)
        log_text.config(state='disabled')

    # Set up callbacks
    def on_file_loaded(path: Path):
        log_message(f"✓ File loaded: {path.name}")

    def on_file_saved(path: Path):
        log_message(f"✓ File saved: {path.name}")

    def on_validation_changed(is_valid: bool, errors: list[str]):
        if is_valid:
            log_message("✓ YAML is valid")
        else:
            log_message(f"✗ YAML validation failed: {len(errors)} error(s)")

    def on_modified_changed(is_modified: bool):
        status = "modified" if is_modified else "saved"
        log_message(f"• Content {status}")

    yaml_editor.on_file_loaded = on_file_loaded
    yaml_editor.on_file_saved = on_file_saved
    yaml_editor.on_validation_changed = on_validation_changed
    yaml_editor.on_modified_changed = on_modified_changed

    # Control panel
    control_frame = tk.Frame(main_frame, bg='#2b2b2b')
    control_frame.pack(fill=tk.X, pady=(10, 0))

    def load_sample_1():
        """Load a simple sample."""
        sample = """name: Simple Config
version: 1.0
enabled: true
"""
        yaml_editor.set_content(sample)
        log_message("Loaded Sample 1: Simple Config")

    def load_sample_2():
        """Load a complex sample."""
        sample = """server:
  host: localhost
  port: 8080
  options:
    timeout: 30
    retry: 3

users:
  - name: Alice
    role: admin
    active: true
  - name: Bob
    role: user
    active: false
"""
        yaml_editor.set_content(sample)
        log_message("Loaded Sample 2: Complex Config")

    def load_invalid():
        """Load invalid YAML."""
        invalid = """key: value
  bad_indent: this is wrong
another_key: [unclosed list
"""
        yaml_editor.set_content(invalid)
        log_message("Loaded invalid YAML for testing")

    def show_data():
        """Show parsed YAML data."""
        data = yaml_editor.get_yaml_data()
        if data:
            log_message(f"Parsed data: {type(data).__name__}")
            messagebox.showinfo("YAML Data", f"Parsed successfully!\n\nType: {type(data).__name__}")
        else:
            messagebox.showerror("Error", "Invalid YAML - cannot parse")

    tk.Button(
        control_frame,
        text="Load Sample 1",
        command=load_sample_1,
        bg='#4b4b4b',
        fg='white',
        relief=tk.FLAT
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        control_frame,
        text="Load Sample 2",
        command=load_sample_2,
        bg='#4b4b4b',
        fg='white',
        relief=tk.FLAT
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        control_frame,
        text="Load Invalid",
        command=load_invalid,
        bg='#4b4b4b',
        fg='white',
        relief=tk.FLAT
    ).pack(side=tk.LEFT, padx=5)

    tk.Button(
        control_frame,
        text="Show Parsed Data",
        command=show_data,
        bg='#4b4b4b',
        fg='white',
        relief=tk.FLAT
    ).pack(side=tk.LEFT, padx=5)

    # Initial log message
    log_message("=== PyroxYamlEditor Demo Started ===")
    log_message("• Use the toolbar buttons to interact with the editor")
    log_message("• Try editing the YAML to see real-time validation")
    log_message("• Use Ctrl+S to save, or buttons to load samples")

    print("PyroxYamlEditor demo window created")
    print("Editor features:")
    print("  - Syntax highlighting")
    print("  - Line numbers")
    print("  - Real-time validation")
    print("  - Save/Load functionality")
    print("  - Auto-formatting")

    # Start the demo
    root.mainloop()
