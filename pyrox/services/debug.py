"""debug module for hot reloading and development use."""


def debug() -> None:
    """public debug method for development use.
    """
    from pyrox.models.abc.logging import LoggingManager
    LoggingManager.debug_loggers()
