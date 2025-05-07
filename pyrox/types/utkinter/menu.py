"""tkinter menu user classes
    """
from __future__ import annotations


from tkinter import Menu, Event
from typing import Any, Optional


class ContextMenu(Menu):
    """tkinter :class:`Menu` with user logic and attributes packed on top.

    Intended to be used as a right-click context menu

    .. ------------------------------------------------------------

    .. package:: types.utkinter.menu

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
                 *args,
                 resolver: Optional[Any] = None,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)
        self._data_resolver = resolver
        self._instance_data: Optional[Any] = None

    @property
    def data_resolver(self) -> Any:
        """get this context menu's resolver
        to help parse menu data passed

        Returns:
            Resolver.value: which resolver to use on the instance data
        """
        return self._data_resolver

    @property
    def instance_data(self) -> Any | None:
        """instance data of this menu

        Returns:
            Any | None: data associated with the menu
        """
        return self._instance_data

    def event_show(self,
                   event: Event,
                   data):
        """show this context menu at the event location

        Args:
            event (Event): event
        """
        self._instance_data = data
        self.post(event.x_root, event.y_root)
