"""A loggable entity, using the `logging.Loggable` class.
    """
from __future__ import annotations


import logging
from typing import Optional


__all__ = (
    'ConsolePanelHandler',
    'Loggable',
)


DEF_FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
DEF_DATE_FMT = "%m/%d/%Y, %H:%M:%S"


class ConsolePanelHandler(logging.Handler):
    """A handler for logging that emits messages to specified callbacks.

    .. ------------------------------------------------------------

    .. package:: types.loggable

    .. ------------------------------------------------------------

    Arguments
    -----------

    callback: :class:`callable`
        Callback to call when emitting a message


    """

    def __init__(self, callback: callable):
        super().__init__()
        self._callback = callback
        self.formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

    def emit(self, record):
        self._callback(self.format(record))


class Loggable:
    """A loggable entity, using the `logging.Loggable` class.

    .. ------------------------------------------------------------

    .. package:: types.loggable

    .. ------------------------------------------------------------

    Arguments
    -----------

    name: Optional[:class:`str`]
        Name to assign to this handler.

        Otherwise, defaults to `self.__class__.__name__`.

    Attributes
    -----------
    logger: :class:`logging.Logger`
        `Logger` for this loggable object.


    """

    _curr_loggers = {}

    def __init__(self,
                 name: Optional[str] = None):
        self._logger: logging.Logger = self._get(name=name if name else self.__class__.__name__)

    @property
    def logger(self) -> logging.Logger:
        """`Logger` for this loggable object.

        .. ------------------------------------------------------------

        Returns
        --------
            logger: :class:`logging.Logger`
        """
        return self._logger

    @staticmethod
    def _get(name: str = __name__):

        if Loggable._curr_loggers.get(name):
            return Loggable._curr_loggers.get(name)

        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        cons = logging.StreamHandler()
        cons.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt=DEF_FORMATTER, datefmt=DEF_DATE_FMT)

        cons.setFormatter(formatter)
        _logger.addHandler(cons)

        Loggable._curr_loggers[name] = _logger

        return _logger

    def add_handler(self,
                    handler: logging.Handler):
        """Add a log :class:`logging.Handler` to this logger object.

        .. ------------------------------------------------------------

        Arguments
        --------
        handler: :class:`logging.Handler`
            Handler to add to this logging object.

        """
        self._logger.addHandler(handler)

    def error(self,
              msg: str):
        """Send `error` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        self._logger.error(msg)

    def info(self,
             msg: str):
        """Send `info` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        self._logger.info(msg)

    def warning(self,
                msg: str):
        """Send `warning` message to logger handler.

        .. ------------------------------------------------------------

        Arguments
        --------
        msg: :class:`str`
            Message to post to handler.

        """
        self._logger.warning(msg)
