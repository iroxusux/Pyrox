"""Theme definitions for Pyrox GUI applications.
"""
from dataclasses import dataclass


@dataclass
class DefaultTheme:
    """Default theme for Pyrox applications."""
    name: str = 'pyrox_default'
    background: str = "#2b2b2b"
    background_selected: str = '#4b4b4b'
    background_hover: str = '#3b3b3b'
    bordercolor: str = '#DDDDDD'
    borderwidth: int = 1
    button_color: str = '#2b2b2b'
    button_hover: str = '#6e6e6e'
    button_active: str = '#4b4b4b'
    debug_text: str = '#FFFFFF'
    error_background: str = "#be3232"
    font_family: str = 'Consolas'
    font_size: int = 10
    foreground: str = '#aaaaaa'
    foreground_selected: str = '#FFFFFF'
    foreground_hover: str = "#DDDDDD"
    relief: str = 'solid'
    stderr_text: str = '#FF4500'
    stdout_text: str = '#00FF00'
    warning_background: str = "#f7e822"
    widget_background: str = '#1e1e1e'
