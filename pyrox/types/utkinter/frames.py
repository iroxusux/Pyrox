"""tkinter user made frames
    """
from __future__ import annotations


from tkinter import BOTH, BOTTOM, HORIZONTAL, LabelFrame, LEFT, Scrollbar, Tk, VERTICAL, X, Y

if __name__ == '__main__':
    from pyrox import UserListbox
else:
    from .listbox import UserListbox


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
