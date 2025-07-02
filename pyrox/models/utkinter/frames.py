"""tkinter user made frames
    """
from __future__ import annotations


from typing import Optional
from tkinter import (
    BOTH,
    Button,
    BOTTOM,
    GROOVE,
    Frame,
    LabelFrame,
    Label,
    LEFT,
    RIGHT,
    Scrollbar,
    Text,
    TOP,
    Toplevel,
    VERTICAL,
    X,
    Y
)


from .treeview import LazyLoadingTreeView
from ..abc.meta import Loggable


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


class PyroxTopLevelFrame(Toplevel, Loggable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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

        self._tree: LazyLoadingTreeView = LazyLoadingTreeView(master=self,
                                                              columns=('Value',),
                                                              show='tree headings')
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')

        vscrollbar = Scrollbar(self,
                               orient=VERTICAL,
                               command=self._tree.yview)
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._tree.pack(fill=BOTH, expand=True)

    @property
    def tree(self) -> LazyLoadingTreeView:
        """get the tree view of this organizer window

        Returns:
            ttk.Treeview: tree view
        """
        return self._tree

    @tree.setter
    def tree(self, value: LazyLoadingTreeView):
        """set the tree view of this organizer window

        Args:
            value (ttk.Treeview): tree view to set
        """
        if isinstance(value, LazyLoadingTreeView):
            self._tree = value
            self._tree.pack(fill=BOTH, expand=True)
        else:
            raise TypeError(f'Expected LazyLoadingTreeView, got {type(value)}')


class TaskFrame(Frame):
    """A frame for tasks in the application.

    This frame is intended to be used as a base class for task-specific frames.
    It inherits from `PyroxFrame` and can be extended with additional functionality.

    .. ------------------------------------------------------------

    .. package:: models.utkinter.frames

    .. ------------------------------------------------------------
    """

    def __init__(self,
                 *args,
                 name: str = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name or 'Task Frame'
        self._title_bar = Frame(self, height=30, bg='lightgrey')

        self._close_button = Button(self._title_bar,
                                    text='X',
                                    command=self.destroy,
                                    width=3,)
        self._close_button.pack(side=RIGHT, padx=5, pady=5)

        self._title_label = Label(self._title_bar, text=name or 'Task Frame', bg='lightgrey')
        self._title_label.pack(side=LEFT, padx=5, pady=5)

        self._title_bar.pack(fill=X, side=TOP)

        self._content_frame = Frame(self)
        self._content_frame.pack(fill=BOTH, expand=True, side=TOP)

        self._on_destroy: list[callable] = []

    @property
    def content_frame(self) -> Frame:
        """get the content frame of this task frame

        Returns:
            Frame: content frame
        """
        return self._content_frame

    @property
    def name(self) -> str:
        """get the name of this task frame

        Returns:
            str: name of the task frame
        """
        return self._name

    @property
    def on_destroy(self) -> list[callable]:
        """get the list of callbacks to be called on destroy

        Returns:
            list[callable]: list of callbacks
        """
        return self._on_destroy

    def destroy(self):
        """Destroy the task frame and call all registered callbacks."""
        for callback in self._on_destroy:
            if callable(callback):
                callback()
            else:
                self.logger.warning(f'Callback {callback} is not callable.')
        return super().destroy()


class ToplevelWithTreeViewAndScrollbar(PyroxTopLevelFrame):
    def __init__(self,
                 *args,
                 text: str = None,
                 **kwargs):
        super().__init__(*args,
                         text=text,
                         **kwargs)

        self._tree: LazyLoadingTreeView = LazyLoadingTreeView(master=self,
                                                              columns=('Value',),
                                                              show='tree headings')
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')

        vscrollbar = Scrollbar(self,
                               orient=VERTICAL,
                               command=self._tree.yview)
        self._tree['yscrollcommand'] = vscrollbar.set

        vscrollbar.pack(fill=Y, side=RIGHT)
        self._tree.pack(fill=BOTH, expand=True)

    @property
    def tree(self) -> LazyLoadingTreeView:
        """get the tree view of this organizer window

        Returns:
            ttk.Treeview: tree view
        """
        return self._tree
