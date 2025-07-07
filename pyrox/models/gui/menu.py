"""tkinter menu user classes
    """
from __future__ import annotations

from dataclasses import dataclass
from tkinter import Event, Menu
from typing import Any, Optional

from ..abc.meta import Loggable, PyroxObject


@dataclass
class MenuItem:
    """Data class for menu items

    Attributes:
        label (str): The label of the menu item.
        command (callable): The function to call when the menu item is selected.
        accelerator (str, optional): The keyboard shortcut for the menu item.
    """
    label: str
    command: callable
    accelerator: Optional[str] = None


class ContextMenu(Loggable, Menu):
    """tkinter :class:`Menu` with user logic and attributes packed on top.

    Intended to be used as a right-click context menu

    .. ------------------------------------------------------------

    .. package:: models.utkinter.menu

    .. ------------------------------------------------------------

    Arguments
    -----------

    resolver: Optional[:class:`Any`]
        WIP - Intended to be an enum of sorts to help sort out a callback for a given action

    .. ------------------------------------------------------------

    Attributes
    -----------
    data_resolver: Optional[:class:`Any`]
        WIP...

    instance_data: Optional[:class:`Any`]
        Current instance data if this menu.

    """

    def __init__(self,
                 **kwargs):
        Loggable.__init__(self)
        Menu.__init__(self, **kwargs)

    def _build_menu(self, items: list[MenuItem]) -> None:
        """Build the context menu with the given items.

        Args:
            items (list[MenuItem]): List of MenuItem objects to add to the menu.
        """
        self.delete(0, 'end')
        for item in items:
            self.add_command(label=item.label,
                             command=item.command,
                             accelerator=item.accelerator)
            if item.accelerator:
                self.bind_all(f'<Control-{item.accelerator}>',
                              lambda event, cmd=item.command: cmd(event))

    def compile_menu_from_item(self,
                               event: Event,
                               treeview_item: str,
                               edit_object: PyroxObject,
                               lookup_attribute: str) -> list[MenuItem]:
        """Compile the context menu from the given item.

        This method should be overridden in subclasses to provide specific menu items.

        .. -------------------------------------------------------------

        Args
        -----------
        item (str, optional): The item to compile the menu from.
            Defaults to None.

        data (Optional[Any], optional): Additional data to use for compiling the menu.
            Defaults to None.

        .. -------------------------------------------------------------

        Returns
        -----------
        list[MenuItem]: A list of MenuItem objects to be added to the context menu.
        """
        return []

    def on_right_click(self,
                       event: Event,
                       treeview_item: str,
                       edit_object: Any,
                       lookup_attribute: str) -> None:
        """Handle right-click events to show the context menu"""
        self._build_menu(self.compile_menu_from_item(event=event,
                                                     treeview_item=treeview_item,
                                                     edit_object=edit_object,
                                                     lookup_attribute=lookup_attribute))
        self.post(event.x_root, event.y_root)
