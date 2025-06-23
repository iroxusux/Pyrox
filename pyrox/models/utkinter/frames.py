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
    TOP,
    Text,
    Tk,
    ttk,
    VERTICAL,
    Widget,
    X,
    Y
)
from tkinter.ttk import Treeview

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
    HOVERING_Y_TOP = 'hovering_y_top'
    HOVERING_Y_BOTTOM = 'hovering_y_bottom'
    RESIZING_X = 'resizing_x'
    RESIZING_Y_TOP = 'resizing_y_top'
    RESIZING_Y_BOTTOM = 'resizing_y_bottom'


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
        self._resize_data: Event = None

        self.bind('<ButtonPress-1>', self._on_button_press)
        self.bind('<ButtonRelease-1>', self._on_button_release)
        self.bind('<Motion>', self._on_motion)
        self.bind('<Leave>', self._on_motion)

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

        if self.current_action is FrameActions.RESIZING_X or      \
                self.current_action is FrameActions.RESIZING_Y_TOP or \
                self.current_action is FrameActions.RESIZING_Y_BOTTOM or \
                self.current_action is FrameActions.HOVERING_X or \
                self.current_action is FrameActions.HOVERING_Y_TOP or \
                self.current_action is FrameActions.HOVERING_Y_BOTTOM:
            self.config(cursor=TK_CURSORS.SIZING)
            return

        self._resize_data = None
        self.config(cursor=TK_CURSORS.ARROW)

    @property
    def resizing(self) -> bool:
        """check if the frame is currently resizing

        Returns:
            bool: True if resizing, False otherwise
        """
        return self.current_action is FrameActions.RESIZING_X or \
            self.current_action is FrameActions.RESIZING_Y_TOP or \
            self.current_action is FrameActions.RESIZING_Y_BOTTOM

    def _on_button_press(self,
                         event):
        """handle button press events"""
        if self.current_action is FrameActions.STANDARD or self.resizing:
            return

        self._resize_data = event

        if self.current_action is FrameActions.HOVERING_X:
            self.current_action = FrameActions.RESIZING_X

        elif self.current_action is FrameActions.HOVERING_Y_TOP:
            self.current_action = FrameActions.RESIZING_Y_TOP

        elif self.current_action is FrameActions.HOVERING_Y_BOTTOM:
            self.current_action = FrameActions.RESIZING_Y_BOTTOM

    def _on_button_release(self,
                           event):
        """handle button release events"""
        self.current_action = FrameActions.STANDARD
        self._resize_data = None

    def _on_motion_edge(self,
                        event):
        if self.resizing:
            return

        info = self.pack_info()
        edge_threshold = 5  # Adjust this value as needed
        x, y = event.x, event.y
        w, h = event.widget.winfo_width(), event.widget.winfo_height()

        # left edge
        if x <= edge_threshold and info['side'] == RIGHT:
            self.current_action = FrameActions.HOVERING_X
            return

        # right edge
        elif x >= w - edge_threshold and info['side'] == LEFT:
            self.current_action = FrameActions.HOVERING_X
            return

        # top edge
        elif y <= edge_threshold and info['side'] == BOTTOM:
            self.current_action = FrameActions.HOVERING_Y_TOP
            return

        # bottom edge
        elif y >= h - edge_threshold and info['side'] == TOP:
            self.current_action = FrameActions.HOVERING_Y_BOTTOM
            return

        # if not on an edge, reset cursor
        self.current_action = FrameActions.STANDARD

    def _on_motion_resize(self, event):
        """Handle motion events when resizing."""
        if not self.resizing:
            return

        self.pack_propagate(False)

        if self.current_action is FrameActions.RESIZING_X:
            delta_x = event.x - self._resize_data.x
            new_width = self._resize_data.x + delta_x
            if new_width > 0:
                self.configure(width=new_width)

        elif self.current_action is FrameActions.RESIZING_Y_BOTTOM:
            delta_y = self._resize_data.y - event.y
            new_height = self._resize_data.y + delta_y
            if new_height > 0:
                self.configure(height=new_height)

        elif self.current_action is FrameActions.RESIZING_Y_TOP:
            delta_y = self._resize_data.y - event.y
            new_height = self._resize_data.y + delta_y
            if new_height > 0:
                self.configure(height=new_height)

    def _on_motion(self,
                   event):
        self._on_motion_edge(event)
        self._on_motion_resize(event)

    def _retag(self, tag, *widgets: list[Widget]):
        for widget in widgets:
            widget.bindtags((tag,) + widget.bindtags())


def clear_widget(widget: Widget):
    if not widget:
        return

    for child in widget.winfo_children():
        child.pack_forget()


def populate_tree(tree: Treeview, parent, data):
    """
    Recursively populates a ttk.Treeview with keys and values from a dictionary or list.

    Parameters:
    - tree: ttk.Treeview widget
    - parent: parent node ID in the tree (use '' for root)
    - data: dictionary or list to populate the tree with
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                node = tree.insert(parent, 'end', text=str(key), values=['[...]'])
                populate_tree(tree, node, value)
            else:
                tree.insert(parent, 'end', text=str(key), values=(str(value),))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, dict) and '@Name' in item:
                node_label = item['@Name']
            elif isinstance(item, dict) and 'name' in item:
                node_label = item['name']
            else:
                node_label = f"[{index}]"
            if node_label == '' or node_label is None:
                node_label = f"[{index}]"
            if isinstance(item, (dict, list)):
                node = tree.insert(parent=parent, index='end', text=node_label, values=['[...]'])
                populate_tree(tree, node, item)
            else:
                tree.insert(parent, 'end', text=node_label, values=(str(item),))


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


class TreeViewGridFrame(LabelFrame):
    """...

    """

    def __init__(self,
                 *args,
                 data_dict: dict,
                 **kwargs):
        super().__init__(*args, **kwargs)

        self._tree: ttk.Treeview = create_tree_view(data_dict=data_dict,
                                                    parent=self)

        vscrollbar = Scrollbar(self, orient=VERTICAL, command=self._tree.yview)
        hscrollbar = Scrollbar(self, orient=HORIZONTAL, command=self._tree.xview)

        self._tree['yscrollcommand'] = vscrollbar.set
        self._tree['xscrollcommand'] = hscrollbar.set

        hscrollbar.pack(fill=X, side=BOTTOM)
        vscrollbar.pack(fill=Y, side=LEFT)
        self._tree.pack(fill=BOTH, side=LEFT, expand=True)

    @property
    def listbox(self) -> UserListbox:
        """The :class:`UserListbox` owned by this :class:`DecoratedListbox` frame.

        Returns
        ----------
            listbox: :class:`UserListbox`
        """
        return self._listbox


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
