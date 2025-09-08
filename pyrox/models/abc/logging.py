"""Logging module for pyrox applications.
"""
from __future__ import annotations
import logging
import sys


DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


class LoggingManager:
    """A Logging manager for the pyrox application environment.
    """
    curr_logging_level = logging.INFO
    _curr_loggers = {}

    @classmethod
    def _create_logger(cls,
                       name: str = __name__
                       ) -> logging.Logger:
        """Create a logger that outputs to stderr (which gets captured)."""
        logger = cls._setup_standard_logger(name=name)
        cls._curr_loggers[name] = logger
        return logger

    @classmethod
    def _get_or_create_logger(
        cls,
        name: str = __name__,
    ) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return cls._curr_loggers.get(name, cls._create_logger(name=name))

    @classmethod
    def _get_standard_handler(cls, stream) -> logging.StreamHandler:
        """Get a standard logging handler that outputs to the specified stream.

        Args:
            stream: The stream to output logs to (default is sys.stderr).

        Returns:
            logging.StreamHandler: A configured StreamHandler instance.
        """
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)
        handler.setFormatter(formatter)
        handler.setLevel(cls.curr_logging_level)
        return handler

    @classmethod
    def _setup_standard_logger(
        cls,
        name: str = None
    ) -> logging.Logger:
        """Get a standard logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: A configured Logger instance.
        """
        logger = logging.getLogger(name)
        cls._remove_all_handlers(logger)
        handler = cls._get_standard_handler(sys.stderr)
        logger.addHandler(handler)
        logger.setLevel(cls.curr_logging_level)
        logger.propagate = False
        return logger

    @staticmethod
    def _remove_all_handlers(logger: logging.Logger) -> None:
        """Remove all handlers from the specified logger.

        Args:
            logger: The logger from which to remove handlers.
        """
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    @classmethod
    def get_or_create_logger(
        cls,
        name: str = __name__
    ) -> logging.Logger:
        """Get or create a logger with the specified name.

        Args:
            name: The name for the logger.

        Returns:
            logging.Logger: The logger instance.
        """
        return cls._get_or_create_logger(name=name)

    @classmethod
    def force_all_loggers_to_stderr(cls):
        """Force all existing loggers to use sys.stderr."""

        # Update root logger
        cls._setup_standard_logger()

        # Update all existing loggers in the manager
        for name in list(logging.Logger.manager.loggerDict.keys()):
            cls._setup_standard_logger(name)

        # Update the Loggable class loggers too
        for name, _ in Loggable._curr_loggers.items():
            cls._setup_standard_logger(name)

    @classmethod
    def set_logging_level(
        cls,
        log_level: int = logging.INFO
    ) -> None:
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
    """An easier mixin class that doesn't require a name property for logging.
    \n Rather, it uses the inheriting class's builtin name.
    """

    logger: logging.Logger = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Create logger for each subclass
        if not hasattr(cls, 'logger') or cls.logger is None:
            cls.logger = LoggingManager.get_or_create_logger(name=cls.__name__)
