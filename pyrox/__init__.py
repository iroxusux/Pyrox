""" A python based application framework.

iroxusux
"""

from . import (
    interfaces,
    services,
    models,
)


def bootstrap() -> None:
    """Bootstrap the Pyrox framework by initializing all services."""
    services.GuiManager.initialize(
        services.EnvManager.get('UI_FRAMEWORK', default=None)
    )


bootstrap()


__all__ = (
    'interfaces',
    'services',
    'models',
)
