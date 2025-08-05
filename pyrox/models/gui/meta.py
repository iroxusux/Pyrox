"""meta gui classes for Pyrox applications.
"""
import tkinter as tk
from tkinter import Text
from typing import Callable, Optional


__all__ = [
    'TextWidgetStream',
]


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
