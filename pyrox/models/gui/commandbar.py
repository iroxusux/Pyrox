"""
Command Bar Widget for Pyrox applications.

This module provides a command bar widget that allows easy programmatic
adding and removal of command buttons for user interactions. The command
bar follows the Pyrox GUI patterns and theming system.
"""
from __future__ import annotations

from typing import List, Optional, Callable
from dataclasses import dataclass


@dataclass
class CommandButton:
    """Configuration for a command button.

    Attributes:
        id (str): Unique identifier for the button.
        text (str): Text displayed on the button.
        command (Callable): Function to call when button is clicked.
        tooltip (Optional[str]): Tooltip text for the button.
        icon (Optional[str]): Icon path or Unicode character for the button.
        enabled (bool): Whether the button is initially enabled.
        visible (bool): Whether the button is initially visible.
        selectable (bool): Whether the button is selectable (toggle).
        width (Optional[int]): Button width in characters.
    """
    id: str
    text: str
    command: Callable[[], None]
    tooltip: Optional[str] = None
    icon: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    selectable: bool = False
    width: Optional[int] = None


@dataclass
class CommandDropdown:
    """Configuration for a command bar dropdown.

    Attributes:
        id (str): Unique identifier for the dropdown.
        options (List[str]): List of selectable options.
        command (Optional[Callable[[str], None]]): Function called with the selected
            value whenever the selection changes. May be None.
        label (Optional[str]): Optional prefix label displayed before the combobox.
        default (Optional[str]): Initial selected value. Defaults to the first option.
        tooltip (Optional[str]): Tooltip text shown on hover.
        enabled (bool): Whether the dropdown is initially enabled.
        visible (bool): Whether the dropdown is initially visible.
        width (Optional[int]): Combobox width in characters.
    """
    id: str
    options: List[str]
    command: Optional[Callable[[str], None]] = None
    label: Optional[str] = None
    default: Optional[str] = None
    tooltip: Optional[str] = None
    enabled: bool = True
    visible: bool = True
    width: Optional[int] = None
