"""Stream service for directing output streams to files and managing logging streams.

This module provides functionality to create and manage file streams that can be
connected to loggers for report generation and output redirection.
"""

from __future__ import annotations
import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Callable, Any, Dict
from datetime import datetime


__all__ = [
    'StreamManager',
    'FileStream',
    'create_stream_to_file',
    'create_file_stream_manager',
]


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


class StreamManager:
    """Manager for multiple file streams with connection to loggers.

    This class manages multiple FileStream instances and provides functionality
    to connect them to loggers for report generation and output redirection.

    Attributes:
        streams (Dict[str, FileStream]): Dictionary of managed streams by name
    """

    def __init__(self):
        self.streams: Dict[str, FileStream] = {}
        self._lock = threading.Lock()

    def create_stream(
        self,
        name: str,
        file_path: str,
        mode: str = 'a',
        encoding: str = 'utf-8',
        auto_flush: bool = True,
        buffer_size: int = -1
    ) -> FileStream:
        """Create and register a new file stream.

        Args:
            name: Unique name for the stream
            file_path: Path to the target file
            mode: File open mode
            encoding: File encoding
            auto_flush: Whether to automatically flush after each write
            buffer_size: Buffer size for the stream

        Returns:
            Created FileStream instance

        Raises:
            ValueError: If stream name already exists
        """
        with self._lock:
            if name in self.streams:
                raise ValueError(f"Stream '{name}' already exists")

            stream = FileStream(
                file_path=file_path,
                mode=mode,
                encoding=encoding,
                auto_flush=auto_flush,
                buffer_size=buffer_size
            )

            self.streams[name] = stream
            print(f"Created stream '{name}' for file: {file_path}", file=sys.stderr)
            return stream

    def get_stream(self, name: str) -> Optional[FileStream]:
        """Get a stream by name.

        Args:
            name: Name of the stream

        Returns:
            FileStream instance or None if not found
        """
        return self.streams.get(name)

    def remove_stream(self, name: str) -> bool:
        """Remove and close a stream.

        Args:
            name: Name of the stream to remove

        Returns:
            True if removed successfully, False if not found
        """
        # Get the stream to close without holding the lock during close
        with self._lock:
            if name not in self.streams:
                return False
            stream = self.streams.pop(name)

        # Close the stream without holding the manager lock
        stream.close()
        print(f"Removed stream '{name}'", file=sys.stderr)
        return True

    def write_to_stream(self, name: str, text: str) -> bool:
        """Write text to a specific stream.

        Args:
            name: Name of the stream
            text: Text to write

        Returns:
            True if written successfully, False otherwise
        """
        stream = self.get_stream(name)
        if stream:
            return stream.write(text)
        return False

    def write_to_all(self, text: str) -> Dict[str, bool]:
        """Write text to all streams.

        Args:
            text: Text to write

        Returns:
            Dictionary mapping stream names to success status
        """
        results = {}
        for name, stream in self.streams.items():
            results[name] = stream.write(text)
        return results

    def flush_all(self) -> Dict[str, bool]:
        """Flush all streams.

        Returns:
            Dictionary mapping stream names to success status
        """
        results = {}
        for name, stream in self.streams.items():
            results[name] = stream.flush()
        return results

    def close_all(self) -> Dict[str, bool]:
        """Close all streams.

        Returns:
            Dictionary mapping stream names to success status
        """
        results = {}
        # Get a copy of streams to avoid holding the lock during close operations
        with self._lock:
            streams_to_close = list(self.streams.items())
            self.streams.clear()

        # Close streams without holding the manager lock to avoid deadlock
        for name, stream in streams_to_close:
            results[name] = stream.close()

        return results

    def get_stream_names(self) -> List[str]:
        """Get list of all stream names.

        Returns:
            List of stream names
        """
        return list(self.streams.keys())

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all streams.

        Returns:
            Dictionary mapping stream names to their statistics
        """
        return {name: stream.get_stats() for name, stream in self.streams.items()}

    @contextmanager
    def stream_context(self, name: str, file_path: str, **kwargs):
        """Context manager for temporary stream creation.

        Args:
            name: Unique name for the stream
            file_path: Path to the target file
            **kwargs: Additional arguments for FileStream
        """
        stream = self.create_stream(name, file_path, **kwargs)
        try:
            yield stream
        finally:
            self.remove_stream(name)

    def __len__(self) -> int:
        """Get number of managed streams."""
        return len(self.streams)

    def __contains__(self, name: str) -> bool:
        """Check if a stream name exists."""
        return name in self.streams

    def __iter__(self):
        """Iterate over stream names."""
        return iter(self.streams)


# Convenience functions for backward compatibility and ease of use
def create_stream_to_file(file_path: str, **kwargs) -> Optional[FileStream]:
    """Create a file stream for logging output.

    Args:
        file_path: Path to the target file
        **kwargs: Additional arguments for FileStream

    Returns:
        FileStream instance or None if creation failed
    """
    try:
        stream = FileStream(file_path, **kwargs)
        if stream.open():
            return stream
        return None
    except Exception as e:
        if sys.__stderr__:
            sys.__stderr__.write(f"Failed to create file stream: {e}\n")
        return None


def create_file_stream_manager() -> StreamManager:
    """Create a new StreamManager instance.

    Returns:
        New StreamManager instance
    """
    return StreamManager()
