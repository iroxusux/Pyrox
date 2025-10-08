"""Application ABC types for the Pyrox framework."""
from __future__ import annotations
from tkinter import (
    Menu,
    Tk,
    Toplevel,
)
from typing import Union
from pyrox.models.abc import Buildable


class BaseMenu(Buildable):
    """Base menu for use in a UI Application.

    Args:
        root: The root Tk object this menu belongs to.

    Attributes:
        menu: The Tk Menu instance for this BaseMenu.
        root: The parent root item of this menu.
    """
    __slots__ = ('_root', '_menu')

    def __init__(self, root: Union[Tk, Toplevel]):
        super().__init__()
        self._root: Union[Tk, Toplevel] = root
        self._menu: Menu = Menu(self._root)

    @property
    def menu(self) -> Menu:
        """The Tk Menu instance for this BaseMenu.

        Returns:
            Menu: The Tk Menu object.
        """
        return self._menu

    @property
    def root(self) -> Union[Tk, Toplevel]:
        """The parent root item of this menu.

        Returns:
            Union[Tk, Toplevel]: The parent root object.
        """
        return self._root

    @staticmethod
    def get_menu_commands(menu: Menu) -> dict:
        """Get all menu commands for a specified Tk Menu.

        Args:
            menu: Menu to get all commands for.

        Returns:
            dict: Dictionary of menu commands, where the key is the label and the value is the command.
        """
        if not isinstance(menu, Menu):
            raise TypeError('Menu must be a Tkinter Menu instance.')
        cmds = {}
        try:
            last_index = menu.index('end')
            if not last_index or last_index < 0:
                return cmds
            for x in range(last_index + 1):
                if menu.type(x) == 'command':
                    label = menu.entrycget(x, 'label')
                    cmd = menu.entrycget(x, 'command')
                    cmds[label] = cmd
        except TypeError:
            pass
        return cmds


class MainApplicationMenu(BaseMenu):
    """Application Main Menu.

    Inherited from BaseMenu, this class acts as the main menu for a root application.

    Args:
        root: The root Tk object this menu belongs to.

    Attributes:
        edit: The Edit Menu for this MainApplicationMenu.
        file: The File Menu for this MainApplicationMenu.
        help: The Help Menu for this MainApplicationMenu.
        tools: The Tools Menu for this MainApplicationMenu.
        view: The View Menu for this MainApplicationMenu.
    """
    __slots__ = ('_file', '_edit', '_tools', '_view', '_help')

    def __init__(self, root: Union[Tk, Toplevel]):
        super().__init__(root=root)
        self._file: Menu = Menu(self.menu, name='file', tearoff=0)
        self._edit: Menu = Menu(self.menu, name='edit', tearoff=0)
        self._tools: Menu = Menu(self.menu, name='tools', tearoff=0)
        self._view: Menu = Menu(self.menu, name='view', tearoff=0)
        self._help: Menu = Menu(self.menu, name='help', tearoff=0)

        self.menu.add_cascade(label='File', menu=self.file, accelerator='<Alt>F', underline=0)
        self.menu.add_cascade(label='Edit', menu=self.edit, accelerator='<Alt>E', underline=0)
        self.menu.add_cascade(label='Tools', menu=self.tools, accelerator='<Alt>T', underline=0)
        self.menu.add_cascade(label='View', menu=self.view, accelerator='<Alt>V', underline=0)
        self.menu.add_cascade(label='Help', menu=self.help, accelerator='<Alt>H', underline=0)

        self.root.config(menu=self.menu)

    @property
    def edit(self) -> Menu:
        """The Edit Menu for this MainApplicationMenu.

        Returns:
            Menu: The Edit menu object.
        """
        return self._edit

    @property
    def file(self) -> Menu:
        """The File Menu for this MainApplicationMenu.

        Returns:
            Menu: The File menu object.
        """
        return self._file

    @property
    def help(self) -> Menu:
        """The Help Menu for this MainApplicationMenu.

        Returns:
            Menu: The Help menu object.
        """
        return self._help

    @property
    def tools(self) -> Menu:
        """The Tools Menu for this MainApplicationMenu.

        Returns:
            Menu: The Tools menu object.
        """
        return self._tools

    @property
    def view(self) -> Menu:
        """The View Menu for this MainApplicationMenu.

        Returns:
            Menu: The View menu object.
        """
        return self._view
