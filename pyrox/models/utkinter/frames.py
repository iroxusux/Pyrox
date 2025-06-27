"""tkinter user made frames
    """
from __future__ import annotations


from enum import Enum
from typing import Optional
from tkinter import (
    BOTH,
    BOTTOM,
    GROOVE,
    LabelFrame,
    RIGHT,
    Scrollbar,
    Text,
    ttk,
    VERTICAL,
    Y
)


from ..abc.meta import Loggable


class FrameActions(Enum):
    """enumeration of actions that can be performed on a frame
    """
    STANDARD = 'standard'
    HOVERING_X = 'hovering_x'
    HOVERING_Y = 'hovering_y'
    RESIZING_X = 'resizing_x'
    RESIZING_Y = 'resizing_y'

    @staticmethod
    def sizing_all() -> list:
        """get all sizing actions

        Returns:
            list[FrameActions]: all sizing actions
        """
        return [
            FrameActions.RESIZING_X,
            FrameActions.RESIZING_Y
        ]

    @staticmethod
    def sizing_x() -> list:
        return [
            FrameActions.HOVERING_X,
            FrameActions.RESIZING_X
        ]

    @staticmethod
    def sizing_y() -> list:
        return [
            FrameActions.HOVERING_Y,
            FrameActions.RESIZING_Y
        ]


class PyroxFrame(LabelFrame, Loggable):

    def __init__(self, *args, **kwargs):
        LabelFrame.__init__(self,
                            *args,
                            borderwidth=4,
                            padx=4,
                            pady=4,
                            relief=GROOVE,
                            **kwargs)
        Loggable.__init__(self)


class LogWindow(PyroxFrame):
    """tkinter :class:`LabelFrame` with user logic and attributes packed on top.

    Intended for use as a log window

    .. ------------------------------------------------------------

    .. package:: types.utkinter.frames

    .. ------------------------------------------------------------

    Attributes
    -----------
    xxx

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args,
                         text='Logger',
                         **kwargs)

        self._logtext = Text(self, state='disabled')
        vscrollbar = Scrollbar(self, orient=VERTICAL, command=self._logtext.yview)
        self._logtext['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._logtext.pack(side=BOTTOM, fill=BOTH, expand=True)

    @property
    def log_text(self) -> Optional[Text]:
        """get the log entry text attr

        Returns:
            Text | None: text
        """
        return self._logtext


class FrameWithTreeViewAndScrollbar(PyroxFrame):
    def __init__(self,
                 *args,
                 text: str = None,
                 **kwargs):
        super().__init__(*args,
                         text=text,
                         **kwargs)

        self._tree: ttk.Treeview = ttk.Treeview(master=self,
                                                columns=('Value',),
                                                show='tree headings')
        vscrollbar = Scrollbar(self,
                               orient=VERTICAL,
                               command=self._tree.yview)
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._tree.pack(fill=BOTH, expand=True)

    @property
    def tree(self) -> ttk.Treeview:
        """get the tree view of this organizer window

        Returns:
            ttk.Treeview: tree view
        """
        return self._tree

    @tree.setter
    def tree(self, value: ttk.Treeview):
        """set the tree view of this organizer window

        Args:
            value (ttk.Treeview): tree view to set
        """
        if isinstance(value, ttk.Treeview):
            self._tree = value
            self._tree.pack(fill=BOTH, expand=True)
        else:
            raise TypeError(f'Expected ttk.Treeview, got {type(value)}')
