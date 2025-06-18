"""tkinter listbox user classes
    """
from __future__ import annotations


from tkinter import END, Event, Listbox
from typing import Optional


from .menu import ContextMenu


class UserListbox(Listbox):
    """tkinter :class:`Listbox` with user logic and attributes packed on top.

    .. ------------------------------------------------------------

    .. package:: types.utkinter.listbox

    .. ------------------------------------------------------------

    Arguments
    -----------

    context_menu: Optional[:class:`ContextMenu`]
        Right-click tkinter :class:`Menu`. Defaults to `None`.

    .. ------------------------------------------------------------

    Attributes
    -----------
    context_menu: Optional[:class:`ContextMenu`]
        Right-click tkinter :class:`Menu`. Defaults to `None`.

    view_model: Optional[:class:`ViewModel`]
        Child `ViewModel` of this :class:`Model`.

    """

    def __init__(self,
                 *args,
                 context_menu: Optional[ContextMenu] = None,
                 **kwargs):
        super().__init__(*args,
                         **kwargs)

        self.bind('<Button-3>', self._select_item)
        self._context_menu = context_menu

    def __len__(self) -> int:
        return len(self.get(0, END))

    @property
    def context_menu(self) -> Optional[ContextMenu]:
        """Right-click tkinter :class:`Menu`. Defaults to `None`.

        .. ------------------------------------------------------------

        Returns
        --------
            context_menu: Optional[:class:`ContextMenu`]
        """
        return self._context_menu

    @context_menu.setter
    def context_menu(self, menu: ContextMenu):
        self._context_menu = menu

        # reset binds to old menu and re-assert new right-click binds
        self.unbind_all('<Button-3>')
        if self._context_menu:
            self.bind('<Button-3>', self._select_and_send)

    def _select_and_send(self,
                         event: Event):
        self._select_item(event)
        self._context_menu.event_show(event, self.get(self.curselection()))

    def _select_item(self,
                     event: Event):
        self.selection_clear(0, END)
        self.selection_set(self.nearest(event.y))
        self.activate(self.nearest(event.y))

    def clear(self) -> None:
        """ Clear the listbox of all entries

        """
        self.delete(0, END)

    def fill(self,
             data: list[str]) -> None:
        """ Fill the listbox with a provided list of string names

        .. ------------------------------------------------------------

        Arguments
        -----------

        data: list[:class:`str`]
            Data to set into the listbox.

        """
        self.clear()

        if not isinstance(data, list):
            data = [data]

        for index, value in enumerate(data):
            self.insert(END, value)
