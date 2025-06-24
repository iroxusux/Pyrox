"""tkinter user made frames
    """
from __future__ import annotations


from enum import Enum
from typing import Optional
from tkinter import (
    BOTH,
    BOTTOM,
    GROOVE,
    Event,
    HORIZONTAL,
    LabelFrame,
    LEFT,
    RIGHT,
    Scrollbar,
    Text,
    Tk,
    ttk,
    VERTICAL,
    Widget,
    X,
    Y
)

if __name__ == '__main__':
    from pyrox import UserListbox
else:
    from .listbox import UserListbox

from ..abc.meta import TK_CURSORS, Loggable


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

        self._current_action = FrameActions.STANDARD
        self._resize_data = None
        self._resize_edge = None
        self._orig_geom = None

        self.bind('<ButtonPress-1>', self._on_button_press)
        self.bind('<ButtonRelease-1>', self._on_button_release)
        self.bind('<Motion>', self._on_motion)
        self.bind('<Leave>', self._on_leave)

    @property
    def current_action(self):
        """get the current action of this frame

        Returns:
            str | None: current action
        """
        return self._current_action

    @current_action.setter
    def current_action(self, action: FrameActions):
        """set the current action of this frame

        Args:
            action (FrameActions): the action to set
        """
        if isinstance(action, FrameActions):
            self._current_action = action
        else:
            raise TypeError(f'Expected FrameActions, got {type(action)}')

        # Set cursor based on action
        if self._current_action in FrameActions.sizing_x():
            self.config(cursor=TK_CURSORS.SIZING)
        elif self._current_action in FrameActions.sizing_y():
            self.config(cursor=TK_CURSORS.SIZING)
        else:
            self.config(cursor=TK_CURSORS.ARROW)

    @property
    def resizing(self) -> bool:
        """check if the frame is currently resizing

        Returns:
            bool: True if resizing, False otherwise
        """
        return self.current_action in FrameActions.sizing_all()

    def _on_button_press(self, event):
        """handle button press events"""
        edge, edge_pos = self._detect_edge(event, return_edge_pos=True)
        if edge:
            self._resize_edge = edge
            self._resize_edge_pos = edge_pos  # 'top' or 'bottom' for y
            self._resize_data = (event.x, event.y, self.winfo_width(), self.winfo_height(), self.winfo_y())
            if edge == 'x':
                self.current_action = FrameActions.RESIZING_X
            elif edge == 'y':
                self.current_action = FrameActions.RESIZING_Y
        else:
            self._resize_edge = None
            self._resize_data = None
            self.current_action = FrameActions.STANDARD

    def _on_button_release(self,
                           event):
        """handle button release events"""
        self.current_action = FrameActions.STANDARD
        self._resize_data = None
        self._resize_edge = None

    def _on_motion(self, event):
        if self.resizing and self._resize_data:
            self._perform_resize(event)
        else:
            edge, _ = self._detect_edge(event, return_edge_pos=True)
            if edge == 'x':
                self.current_action = FrameActions.HOVERING_X
            elif edge == 'y':
                self.current_action = FrameActions.HOVERING_Y
            else:
                self.current_action = FrameActions.STANDARD

    def _on_leave(self,
                  event):
        if not self.resizing:
            self.current_action = FrameActions.STANDARD

    def _detect_edge(self, event: Event, threshold=5, return_edge_pos=False):
        x, y = event.x, event.y
        w, h = self.winfo_width(), self.winfo_height()
        # Detect left or right edge
        if x <= threshold or x >= w - threshold:
            return ('x', None) if return_edge_pos else 'x'
        # Detect top or bottom edge as a single 'y' edge, but return which
        if y <= threshold:
            return ('y', 'top') if return_edge_pos else 'y'
        if y >= h - threshold:
            return ('y', 'bottom') if return_edge_pos else 'y'
        return (None, None) if return_edge_pos else None

    def _perform_resize(self, event):
        self.pack_propagate(False)
        x0, y0, w0, h0, _ = self._resize_data
        dx = event.x - x0
        dy = event.y - y0
        if self._resize_edge == 'x':
            new_width = max(20, w0 + dx)
            self.config(width=new_width)
        elif self._resize_edge == 'y':
            if getattr(self, '_resize_edge_pos', None) == 'top':
                # Dragging top edge: increase height as you drag up (do not move y)
                new_height = max(20, h0 - dy)
                self.config(height=new_height)
            else:
                # Dragging bottom edge: increase height as you drag down
                new_height = max(20, h0 + dy)
                self.config(height=new_height)

    @property
    def resize_data(self):
        """get the resize data of this frame

        Returns:
            tuple | None: resize data (x, y, width, height)
        """
        return self._resize_data

    @resize_data.setter
    def resize_data(self, data):
        """set the resize data of this frame

        Args:
            data (tuple): resize data (x, y, width, height) to set
        """
        self._resize_data = data

    @property
    def resize_edge(self):
        """get the resize edge of this frame

        Returns:
            str | None: resize edge
        """
        return self._resize_edge

    @resize_edge.setter
    def resize_edge(self, edge):
        """set the resize edge of this frame

        Args:
            edge (str): resize edge to set
        """
        self._resize_edge = edge

    @property
    def orig_geom(self):
        """get the original geometry of this frame

        Returns:
            tuple | None: original geometry (x, y, width, height)
        """
        return self._orig_geom

    @orig_geom.setter
    def orig_geom(self, geom):
        """set the original geometry of this frame

        Args:
            geom (tuple): original geometry (x, y, width, height) to set
        """
        self._orig_geom = geom

    def _retag(self, tag, *widgets: list[Widget]):
        for widget in widgets:
            widget.bindtags((tag,) + widget.bindtags())


def clear_widget(widget: Widget):
    if not widget:
        return

    for child in widget.winfo_children():
        child.pack_forget()


def create_tree_view(data_dict, parent):
    # Create a Treeview widget
    columns = set()
    for key, value_list in data_dict.items():
        for item in value_list:
            columns.update(item.keys())
    columns = list(columns)
    tree = ttk.Treeview(parent, columns=columns, show='headings')

    # Define the column headings
    for col in columns:
        tree.heading(col, text=col)

    # Insert the data into the tree
    for key, value_list in data_dict.items():
        for item in value_list:
            tree.insert('', 'end', values=[item.get(col, '') for col in columns])

    # Return the Treeview object
    return tree


class DecoratedListboxFrame(LabelFrame):
    """tkinter :class:`LabelFrame` with user logic and attributes packed on top.

    Includes a dedicated :class:`UserListbox` for data display / interaction

    .. ------------------------------------------------------------

    .. package:: types.utkinter.frames

    .. ------------------------------------------------------------

    Attributes
    -----------
    listbox: :class:`UserListbox`
        The :class:`UserListbox` owned by this :class:`DecoratedListbox` frame.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._listbox = UserListbox(self)

        vscrollbar = Scrollbar(self, orient=VERTICAL, command=self._listbox.yview)
        hscrollbar = Scrollbar(self, orient=HORIZONTAL, command=self._listbox.xview)

        self._listbox['yscrollcommand'] = vscrollbar.set
        self._listbox['xscrollcommand'] = hscrollbar.set

        hscrollbar.pack(fill=X, side=BOTTOM)
        vscrollbar.pack(fill=Y, side=LEFT)
        self._listbox.pack(fill=BOTH, side=LEFT, expand=True)

    @property
    def listbox(self) -> UserListbox:
        """The :class:`UserListbox` owned by this :class:`DecoratedListbox` frame.

        Returns
        ----------
            listbox: :class:`UserListbox`
        """
        return self._listbox


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


if __name__ == '__main__':
    app = Tk()
    frame = DecoratedListboxFrame(app)
    frame.pack(fill=BOTH, expand=True)

    frame.listbox.fill([
        'Data0',
        'Data1',
        'Data2',
        'Data3',
        'Data4',
        'Data5',
        'Data6',
        'Data7',
        'Data8',
        'Data9',
    ])

    app.focus()
    app.mainloop()
