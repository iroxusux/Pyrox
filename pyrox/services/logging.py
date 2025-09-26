"""Logging module for pyrox applications.
"""
from __future__ import annotations
import logging
import sys
import io
from typing import Optional, TextIO
import os

from .decorate import deprecated

DEF_FORMATTER = os.getenv('PYROX_LOG_FORMAT', default='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
DEF_DATE_FMT = os.getenv('PYROX_LOG_DATE_FORMAT', default='%Y-%m-%d %H:%M:%S')


class StreamCapture(io.StringIO):
    """A StringIO subclass that captures stream output and maintains readability."""

    def __init__(self, original_stream: Optional[TextIO] = None):
        super().__init__()
        self.original_stream = original_stream
        self._lines = []
        self._callbacks = []

    def write(self, s: str) -> int:
        """Write to both the capture buffer and optionally the original stream."""
        # Write to our buffer
        result = super().write(s)

        # Also write to original stream if it exists and is writable
        if (self.original_stream and
            hasattr(self.original_stream, 'write') and
                not self.original_stream.closed):
            try:
                self.original_stream.write(s)
                self.original_stream.flush()
            except (OSError, ValueError):
                pass  # Ignore errors writing to original stream

        # Store line for iteration
        if '\n' in s:
            self._lines.extend(s.splitlines(keepends=True))

        # Call any registered callbacks
        for callback in self._callbacks:
            try:
                callback(s)
            except Exception:
                pass  # Ignore errors in callbacks

        return result

    def flush(self):
        """Flush both buffers."""
        super().flush()
        if (self.original_stream and
            hasattr(self.original_stream, 'flush') and
                not self.original_stream.closed):
            try:
                self.original_stream.flush()
            except (OSError, ValueError):
                pass

    def get_lines(self) -> list[str]:
        """Get all captured lines."""
        return self._lines.copy()

    def clear_lines(self):
        """Clear the captured lines buffer."""
        self._lines.clear()

    def readable(self) -> bool:
        """Always return True - this stream is readable."""
        return True

    def register_callback(self, callback):
        """Register a callback to be called on each write."""
        if callable(callback):
            self._callbacks.append(callback)

    def seekable(self) -> bool:
        """Return True - StringIO is seekable."""
        return True


class LoggingManager:
    """A Logging manager for the pyrox application environment."""

    curr_logging_level = logging.DEBUG
    _curr_loggers = {}

    # Stream capture attributes
    _original_stdout: Optional[TextIO] = None
    _original_stderr: Optional[TextIO] = None
    _captured_stdout: Optional[StreamCapture] = None
    _captured_stderr: Optional[StreamCapture] = None
    _streams_captured = False

    @classmethod
    def capture_system_streams(cls) -> tuple[Optional[StreamCapture], Optional[StreamCapture]]:
        """Capture sys.stdout and sys.stderr at application boot.

        Returns:
            tuple[StreamCapture, StreamCapture]: (captured_stdout, captured_stderr)
        """
        if cls._streams_captured:
            return cls._captured_stdout, cls._captured_stderr

        # Store original streams
        cls._original_stdout = sys.stdout
        cls._original_stderr = sys.stderr

        # Create capturing streams
        cls._captured_stdout = StreamCapture(cls._original_stdout)
        cls._captured_stderr = StreamCapture(cls._original_stderr)

        # Replace system streams
        sys.stdout = cls._captured_stdout
        sys.stderr = cls._captured_stderr

        cls._streams_captured = True

        return cls._captured_stdout, cls._captured_stderr

    @classmethod
    def restore_system_streams(cls) -> None:
        """Restore original sys.stdout and sys.stderr."""
        if not cls._streams_captured:
            return

        if cls._original_stdout:
            sys.stdout = cls._original_stdout
        if cls._original_stderr:
            sys.stderr = cls._original_stderr

        cls._streams_captured = False

    @classmethod
    def get_captured_stdout(cls) -> Optional[StreamCapture]:
        """Get the captured stdout stream."""
        return cls._captured_stdout

    @classmethod
    def get_captured_stderr(cls) -> Optional[StreamCapture]:
        """Get the captured stderr stream."""
        return cls._captured_stderr

    @classmethod
    def get_stdout_content(cls) -> str:
        """Get all captured stdout content."""
        if cls._captured_stdout:
            current_pos = cls._captured_stdout.tell()
            cls._captured_stdout.seek(0)
            content = cls._captured_stdout.read()
            cls._captured_stdout.seek(current_pos)
            return content
        return ""

    @classmethod
    def get_stderr_content(cls) -> str:
        """Get all captured stderr content."""
        if cls._captured_stderr:
            current_pos = cls._captured_stderr.tell()
            cls._captured_stderr.seek(0)
            content = cls._captured_stderr.read()
            cls._captured_stderr.seek(current_pos)
            return content
        return ""

    @classmethod
    def get_stdout_lines(cls) -> list[str]:
        """Get captured stdout as a list of lines."""
        return cls._captured_stdout.get_lines() if cls._captured_stdout else []

    @classmethod
    def get_stderr_lines(cls) -> list[str]:
        """Get captured stderr as a list of lines."""
        return cls._captured_stderr.get_lines() if cls._captured_stderr else []

    @classmethod
    def clear_captured_streams(cls) -> None:
        """Clear the content of captured streams."""
        if cls._captured_stdout:
            cls._captured_stdout.seek(0)
            cls._captured_stdout.truncate(0)
            cls._captured_stdout.clear_lines()

        if cls._captured_stderr:
            cls._captured_stderr.seek(0)
            cls._captured_stderr.truncate(0)
            cls._captured_stderr.clear_lines()

    @classmethod
    def debug_loggers(cls):
        """Debug current logger state."""
        print("=== Current Loggers ===")
        for name, logger in cls._curr_loggers.items():
            print(f"Logger: {name}")
            print(f"  Level: {logger.level}")
            print(f"  Propagate: {logger.propagate}")
            print(f"  Handlers: {len(logger.handlers)}")
            for i, handler in enumerate(logger.handlers):
                print(f"    Handler {i}: {type(handler).__name__} -> {getattr(handler, 'stream', 'N/A')}")
            print()

    @classmethod
    def register_callback_to_captured_streams(
        cls,
        callback
    ) -> None:
        """Register a callback to be called on writes to the captured streams.

        Args:
            callback: A callable that takes a single string argument.
        """
        if cls._captured_stdout:
            cls._captured_stdout.register_callback(callback)
        if cls._captured_stderr:
            cls._captured_stderr.register_callback(callback)

    @classmethod
    def _create_logger(cls, name: str = __name__) -> logging.Logger:
        """Create a logger that outputs to the captured stderr."""
        cls._curr_loggers[name] = cls._setup_standard_logger(name=name)
        return cls._curr_loggers[name]

    @classmethod
    def _get_or_create_logger(cls, name: str = __name__) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return cls._curr_loggers.get(name, cls._create_logger(name=name))

    @classmethod
    def _get_standard_handler(cls, stream=None) -> logging.StreamHandler:
        """Get a standard logging handler that outputs to the specified stream.

        Args:
            stream: The stream to output logs to. If None, uses captured stderr.

        Returns:
            logging.StreamHandler: A configured StreamHandler instance.
        """
        if stream is None:
            # Use captured stderr if available, otherwise original stderr
            stream = cls._captured_stderr if cls._captured_stderr else sys.stderr

        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)
        handler.setFormatter(formatter)
        handler.setLevel(cls.curr_logging_level)
        return handler

    @classmethod
    def _setup_standard_logger(cls, name: Optional[str] = None) -> logging.Logger:
        """Get a standard logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: A configured Logger instance.
        """
        logger = logging.getLogger(name)
        cls._remove_all_handlers(logger)
        logger.addHandler(cls._get_standard_handler())
        logger.setLevel(cls.curr_logging_level)
        logger.propagate = False
        return logger

    @staticmethod
    def _remove_all_handlers(logger: logging.Logger) -> None:
        """Remove all handlers from the specified logger.

        Args:
            logger: The logger from which to remove handlers.
        """
        hdlrs = logger.handlers[:]
        for hdlr in hdlrs:
            logger.removeHandler(hdlr)

    @classmethod
    def get_or_create_logger(cls, name: str = __name__) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return cls._get_or_create_logger(name=name)

    @classmethod
    def force_all_loggers_to_captured_stderr(cls):
        """Force all existing loggers to use the captured stderr."""
        # Ensure streams are captured first
        if not cls._streams_captured:
            cls.capture_system_streams()

        # Update root logger
        cls._setup_standard_logger()

        # Update all existing loggers in the manager
        for name in list(logging.Logger.manager.loggerDict.keys()):
            cls._setup_standard_logger(name)

        # Update the Loggable class loggers too
        for name, _ in cls._curr_loggers.items():
            cls._setup_standard_logger(name)

    @classmethod
    def log(
        cls,
        caller: Optional[object] = None,
    ) -> logging.Logger:
        """Get a logger for the specified caller.

        Args:
            caller: The object or class requesting the logger. If None, uses the module logger.
        Returns:
            logging.Logger: The logger instance.
        """
        if caller is None:
            return cls.get_or_create_logger(name=__name__)
        elif isinstance(caller, str):
            return cls.get_or_create_logger(name=caller)
        elif isinstance(caller, type):
            return cls.get_or_create_logger(name=caller.__name__)
        else:
            return cls.get_or_create_logger(name=caller.__class__.__name__)

    @classmethod
    def set_logging_level(cls, log_level: int = logging.INFO) -> None:
        """Set the logging level for all current loggers.

        Args:
            log_level: The logging level to set for all current loggers.
        """
        cls.curr_logging_level = log_level
        for logger in cls._curr_loggers.values():
            logger.setLevel(log_level)
            for handler in logger.handlers:
                handler.setLevel(log_level)


class Loggable:
    """A mixin class to provide logging capabilities to subclasses.
    This allows logging through inheritance rather than importing the logging module directly.
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Ensure logger is registered in LoggingManager._curr_loggers
        LoggingManager._curr_loggers[cls.__name__] = LoggingManager.get_or_create_logger(name=cls.__name__)

    @classmethod
    @deprecated(reason="Use LoggingManager.log(cls) instead or pyrox.services.logging.log.", version="2.0")
    def log(cls) -> logging.Logger:
        """Get a logger for this instance's class.

        Returns:
            logging.Logger: The logger instance.
        """
        return LoggingManager.log(caller=cls.__name__)


def log(caller: Optional[object] = None) -> logging.Logger:
    """Get a logger for the specified caller.

    Args:
        caller: The object or class requesting the logger. If None, uses the module logger.
    Returns:
        logging.Logger: The logger instance.
    """
    return LoggingManager.log(caller=caller)


# Auto-capture streams when module is imported
LoggingManager.capture_system_streams()
