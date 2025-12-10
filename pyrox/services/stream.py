"""Stream service for directing output streams to files and managing logging streams.

This module provides functionality to create and manage file streams that can be
connected to loggers for report generation and output redirection.
"""

from __future__ import annotations
import sys
import threading
from contextlib import contextmanager
from typing import Optional, List, Any, Dict
from pyrox.models.abc.stream import FileStream


__all__ = [
    'StreamManager',
    'create_stream_to_file',
    'create_file_stream_manager',
]


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
