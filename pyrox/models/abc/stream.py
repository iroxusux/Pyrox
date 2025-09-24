from __future__ import annotations
import sys
from typing import Callable

__all__ = (
    'SimpleStream',
    'MultiStream',
)


class SimpleStream:
    """A simple stream that writes to a single provided callback.

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
        """Write text to the callback."""
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
    """A stream that writes to multiple destinations simultaneously."""

    def __init__(self, *streams):
        self.streams = list(streams)
        self.closed = False

    def _fallback_write(self, text):
        """Fallback method to write to sys.__stderr__ if write fails."""
        if sys.__stderr__:
            sys.__stderr__.write(f"MultiStream error: {text}\n")

    def write(self, text):
        """Write text to all streams."""
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
        """Add another stream to write to."""
        if stream not in self.streams:
            self.streams.append(stream)

    def remove_stream(self, stream):
        """Remove a stream from the list."""
        if stream in self.streams:
            self.streams.remove(stream)
