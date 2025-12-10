"""Meta definitions for GUI interfaces.
"""
from enum import Enum


class GuiFramework(Enum):
    """Supported GUI frameworks."""
    TKINTER = "tkinter"
    QT = "qt"
    WX = "wx"
    KIVY = "kivy"
    PYGAME = "pygame"
    CONSOLE = "console"
