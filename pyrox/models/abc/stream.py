"""Stream handling ABC types for the Pyrox framework.

This module provides stream handling classes for redirecting and managing output streams,
including simple streams, multi-streams, and file streams with context management.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path
import sys
import threading
from typing import Any, Callable, List, Dict

__all__ = (
    'FileStream',
    'SimpleStream',
    'MultiStream',
)


class SimpleStream:
    """A simple stream that writes to a single provided callback.

    This class provides a file-like interface that redirects all write operations
    to a provided callback function, useful for custom logging or output handling.

    Attributes:
        callback: A callable that will be called with the text to write.
        closed: Whether the stream is closed.
    """

    def __init__(self, callback: Callable):
        if not callable(callback):
            raise TypeError('Callback must be a callable function.')
        self.callback = callback
        self.closed = False

    def write(self, text: str):
        """Write text to the callback.

        Args:
            text: The text to write to the callback function.
        """
        if self.closed:
            return
        try:
            self.callback(text)
        except Exception as e:
            if sys.__stderr__:
                sys.__stderr__.write(f"SimpleStream error: {e}\n")

    def flush(self):
        """Flush the stream (no-op for SimpleStream)."""
        pass

    def close(self):
        """Close the stream."""
        self.closed = True


class MultiStream:
    """A stream that writes to multiple destinations simultaneously.

    This class provides a file-like interface that broadcasts write operations
    to multiple stream destinations, useful for logging to multiple outputs
    or creating stream multiplexers.

    Attributes:
        streams: List of stream objects to write to.
        closed: Whether the stream is closed.
    """

    def __init__(self, *streams):
        self.streams = list(streams)
        self.closed = False
        self._context_stream = None

    def _fallback_write(self, text):
        """Fallback method to write to sys.__stderr__ if write fails.

        Args:
            text: The text or error to write to stderr.
        """
        if sys.__stderr__:
            sys.__stderr__.write(f"MultiStream error: {text}\n")

    def write(self, text):
        """Write text to all streams.

        Args:
            text: The text to write to all registered streams.
        """
        if self.closed:
            return

        for stream in self.streams:
            try:
                if hasattr(stream, 'write'):
                    stream.write(text)
            except Exception as e:
                self._fallback_write(e)

    def flush(self):
        """Flush all streams."""
        for stream in self.streams:
            try:
                if hasattr(stream, 'flush'):
                    stream.flush()
            except Exception as e:
                self._fallback_write(e)

    def close(self):
        """Close all streams."""
        self.closed = True
        for stream in self.streams:
            try:
                if hasattr(stream, 'close') and stream not in (sys.__stdout__, sys.__stderr__):
                    stream.close()
            except Exception as e:
                self._fallback_write(e)

    def add_stream(self, stream):
        """Add another stream to write to.

        Args:
            stream: The stream object to add to the list of destinations.
        """
        if stream not in self.streams:
            self.streams.append(stream)

    def remove_stream(self, stream):
        """Remove a stream from the list.

        Args:
            stream: The stream object to remove from the list of destinations.
        """
        if stream in self.streams:
            self.streams.remove(stream)

    @contextmanager
    def temporary_stream(self, stream):
        """Context manager to temporarily add a stream.

        Args:
            stream: The stream to temporarily add.

        Yields:
            MultiStream: The MultiStream instance with the temporary stream added.
        """
        self.add_stream(stream)
        try:
            yield self
        finally:
            self.remove_stream(stream)


class FileStream:
    """A managed file stream for logging and output redirection.

    This class wraps a file stream and provides additional functionality for
    managing the stream lifecycle, including automatic flushing, error handling,
    and metadata tracking.

    Args:
        file_path: Path to the target file
        mode: File open mode (default: 'a' for append)
        encoding: File encoding (default: 'utf-8')
        auto_flush: Whether to automatically flush after each write
        buffer_size: Buffer size for the stream (-1 for system default)

    Attributes:
        file_path (str): Path to the target file
        mode (str): File open mode
        encoding (str): File encoding
        auto_flush (bool): Auto-flush setting
        is_open (bool): Whether the stream is currently open
        created_at (datetime): When the stream was created
        bytes_written (int): Total bytes written to the stream
    """

    def __init__(
        self,
        file_path: str,
        mode: str = 'a',
        encoding: str = 'utf-8',
        auto_flush: bool = True,
        buffer_size: int = -1
    ):
        self.file_path = str(Path(file_path).resolve())
        self.mode = mode
        self.encoding = encoding
        self.auto_flush = auto_flush
        self.buffer_size = buffer_size
        self.created_at = datetime.now()
        self.bytes_written = 0

        self._stream: Any = None  # File stream object
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[str], None]] = []

    @property
    def is_open(self) -> bool:
        """Check if the stream is currently open."""
        return self._stream is not None and not self._stream.closed

    def _open(self) -> bool:
        """Internal open method without locking (assumes lock is already held).

        Returns:
            True if opened successfully, False otherwise
        """
        if self.is_open:
            return True

        try:
            # Ensure parent directory exists
            parent_dir = Path(self.file_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            self._stream = open(
                self.file_path,
                self.mode,
                encoding=self.encoding,
                buffering=self.buffer_size
            )
            print(f"Opened file stream: {self.file_path}", file=sys.stderr)
            return True

        except Exception as e:
            print(f"Failed to open file stream {self.file_path}: {e}", file=sys.stderr)
            return False

    def open(self) -> bool:
        """Open the file stream.

        Returns:
            True if opened successfully, False otherwise
        """
        with self._lock:
            return self._open()

    def write(self, text: str) -> bool:
        """Write text to the stream.

        Args:
            text: Text to write

        Returns:
            True if written successfully, False otherwise
        """
        with self._lock:
            if not self.is_open:
                if not self._open():
                    return False

            try:
                bytes_written = self._stream.write(text)
                self.bytes_written += bytes_written

                if self.auto_flush:
                    self._stream.flush()

                # Call any registered callbacks
                for callback in self._callbacks:
                    try:
                        callback(text)
                    except Exception as e:
                        print(f"Callback error in stream {self.file_path}: {e}", file=sys.stderr)

                return True

            except Exception as e:
                print(f"Write error in stream {self.file_path}: {e}", file=sys.stderr)
                return False

    def writelines(self, lines: List[str]) -> bool:
        """Write multiple lines to the stream.

        Args:
            lines: List of strings to write

        Returns:
            True if all lines written successfully, False otherwise
        """
        success = True
        for line in lines:
            if not self.write(line):
                success = False
        return success

    def flush(self) -> bool:
        """Flush the stream buffer.

        Returns:
            True if flushed successfully, False otherwise
        """
        with self._lock:
            if not self.is_open:
                return False

            try:
                self._stream.flush()
                return True
            except Exception as e:
                print(f"Flush error in stream {self.file_path}: {e}", file=sys.stderr)
                return False

    def close(self) -> bool:
        """Close the file stream.

        Returns:
            True if closed successfully, False otherwise
        """
        with self._lock:
            if not self.is_open:
                return True

            try:
                self._stream.close()
                print(f"Closed file stream: {self.file_path}", file=sys.stderr)
                return True
            except Exception as e:
                print(f"Close error in stream {self.file_path}: {e}", file=sys.stderr)
                return False
            finally:
                self._stream = None

    def add_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback function to be called on each write.

        Args:
            callback: Function that takes the written text as argument
        """
        if callable(callback):
            self._callbacks.append(callback)
        else:
            raise TypeError("Callback must be callable")

    def remove_callback(self, callback: Callable[[str], None]) -> bool:
        """Remove a callback function.

        Args:
            callback: Callback function to remove

        Returns:
            True if callback was removed, False if not found
        """
        try:
            self._callbacks.remove(callback)
            return True
        except ValueError:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get stream statistics.

        Returns:
            Dictionary with stream statistics
        """
        return {
            'file_path': self.file_path,
            'mode': self.mode,
            'encoding': self.encoding,
            'is_open': self.is_open,
            'created_at': self.created_at.isoformat(),
            'bytes_written': self.bytes_written,
            'file_exists': os.path.exists(self.file_path),
            'file_size': os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0,
        }

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Destructor to ensure stream is closed."""
        try:
            if hasattr(self, '_stream') and self.is_open:
                self.close()
        except Exception:
            pass  # Ignore errors during cleanup
