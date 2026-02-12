"""Tkinter menu user classes.

This module provides menu implementations for the Pyrox GUI framework,
including abstract base classes and concrete implementations for various
menu types and menu item management.
"""
from tkinter import BooleanVar, Menu
from typing import Any, Callable, Optional, Union
from pyrox.interfaces import IApplicationGuiMenu, IGuiMenu
from pyrox.models.gui.theme import DefaultTheme
from pyrox.models.gui.tk.widget import TkinterGuiWidget


class TkinterMenu(IGuiMenu, TkinterGuiWidget):
    """Tkinter implementation of GuiMenu."""

    __slots__ = ('_menu',)

    def __init__(self) -> None:
        TkinterGuiWidget.__init__(self)

    @property
    def menu(self) -> Menu:
        """Get the underlying Tkinter Menu object.

        Returns:
            Menu: The Tkinter Menu object.

        Raises:
            RuntimeError: If the menu has not been initialized.
        """
        if self._widget is None:
            raise RuntimeError("Menu not initialized")
        return self._widget

    @menu.setter
    def menu(self, value: Menu) -> None:
        """Set the underlying Tkinter Menu object.

        Args:
            value (Menu): The Tkinter Menu object to set.
        """
        if not isinstance(value, Menu):
            raise TypeError(f'Expected tkinter.Menu, got {type(value)}')
        self._widget = value

    def _process_binding_info(self, kwargs: dict) -> None:
        binding_info = kwargs.pop('binding_info', None)
        if binding_info and isinstance(binding_info, tuple) and len(binding_info) == 2:
            from pyrox.services.gui import GuiManager
            backend = GuiManager.unsafe_get_backend()
            backend.bind_hotkey(binding_info[0], binding_info[1])

    def add_checkbutton(
        self,
        label: str,
        variable: BooleanVar,
        command: Callable[..., Any] | None = None,
        index: int | str = 'end',
        underline: int = -1,
        **kwargs
    ) -> None:
        # Process binding info if provided
        self._process_binding_info(kwargs)

        # Create a BooleanVar if a bool is provided
        bool_variable = BooleanVar(master=self.menu)

        # Set underline if specified
        if underline >= 0:
            kwargs['underline'] = underline

        # Default command if none provided
        def default_command(): return None
        command = command or default_command

        # Insert the checkbutton with the variable
        self.menu.insert_checkbutton(
            index,
            label=label,
            variable=bool_variable,
            command=command,
            **kwargs
        )

        # Update the variable reference
        bool_variable.set(variable if isinstance(variable, bool) else variable.get())
        self.menu.update_idletasks()

        return None

    def add_item(
        self,
        label: str,
        command: Optional[Callable] = None,
        accelerator: str = '',
        index: Union[int, str] = 'end',
        underline: int = -1,
        **kwargs
    ) -> None:
        self._process_binding_info(kwargs)

        if underline >= 0:
            kwargs['underline'] = underline

        def default_command(): return None
        command = command or default_command

        state_var = kwargs.pop('variable', None)

        if state_var is None:
            self.menu.insert_command(
                index,
                label=label,
                command=command,
                accelerator=accelerator,
                **kwargs
            )
        else:
            self.menu.insert_radiobutton(
                index,
                label=label,
                command=command,
                variable=state_var,
                accelerator=accelerator,
                **kwargs
            )
        return None

    def add_separator(self, index: Union[int, str] = 'end') -> None:
        self.menu.insert_separator(index)

    def insert_separator(self, index: Union[int, str]) -> None:
        self.menu.insert_separator(index)

    def add_submenu(
        self,
        label: str,
        submenu: IGuiMenu,
        **kwargs
    ) -> None:
        self._process_binding_info(kwargs)
        self.menu.add_cascade(
            label=label,
            menu=submenu.menu,
            **kwargs
        )

    def insert_submenu(
        self,
        index: Union[int, str],
        label: str,
        submenu: IGuiMenu,
        **kwargs
    ) -> None:
        self._process_binding_info(kwargs)
        self.menu.insert_cascade(
            index,
            label=label,
            menu=submenu.menu,
            **kwargs
        )

    def get_submenu(self, index: Union[int, str]) -> Optional[IGuiMenu]:
        try:
            submenu = self.menu.entrycget(index, 'menu')
            if submenu:
                return submenu
        except Exception:
            pass
        return None

    def clear(self) -> None:
        self.menu.delete(0, 'end')

    def config(self, **kwargs) -> None:
        self.menu.entryconfig(**kwargs)

    def config_item(self, index: Union[int, str], **kwargs) -> None:
        self.config(index=index, **kwargs)

    def destroy(self) -> None:
        self.menu.destroy()
        self._menu = None

    def enable_item(self, index: Union[int, str]) -> None:
        try:
            # Get the item type first to check if it supports state
            item_type = self.menu.type(index)
            # Only set state if the item type supports it (not separator)
            if item_type != 'separator':
                self.menu.entryconfig(index, state='normal')
        except Exception:
            # Silently ignore if the item doesn't exist or doesn't support state
            pass

    def disable_item(self, index: Union[int, str]) -> None:
        try:
            # Get the item type first to check if it supports state
            item_type = self.menu.type(index)
            # Only set state if the item type supports it (not separator)
            if item_type != 'separator':
                self.menu.entryconfig(index, state='disabled')
        except Exception:
            # Silently ignore if the item doesn't exist or doesn't support state
            pass

    def get_items(self) -> list[Any]:
        items = []
        length = self.menu.index('end')
        if length is None:
            return items
        for index in range(length + 1):
            items.append(self.menu.entrycget(index, 'label'))
        return items

    def get_height(self) -> int:
        return self.menu.winfo_height()

    def get_width(self) -> int:
        return self.menu.winfo_width()

    def get_x(self) -> int:
        return self.menu.winfo_x()

    def get_y(self) -> int:
        return self.menu.winfo_y()

    def initialize(self, **kwargs) -> bool:
        kwargs['background'] = DefaultTheme.background
        kwargs['foreground'] = DefaultTheme.foreground
        kwargs['bg'] = DefaultTheme.background
        kwargs['fg'] = DefaultTheme.foreground
        self._widget = Menu(**kwargs)
        return True

    def is_visible(self) -> bool:
        if self.menu.winfo_ismapped():
            return True
        return False

    def remove_item(
        self,
        index: Union[int, str] = 'end',
        **kwargs
    ) -> bool:
        self.menu.delete(index)
        return True

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.menu.winfo_toplevel().config(menu=self.menu)
        else:
            self.menu.winfo_toplevel().config(menu=None)  # type: ignore


class TkinterApplicationMenu(IApplicationGuiMenu, TkinterMenu):
    """Application Main Menu.

    Tkinter implementation of an application main menu.

    Attributes:
        edit: The Edit Menu for this MainApplicationMenu.
        file: The File Menu for this MainApplicationMenu.
        help: The Help Menu for this MainApplicationMenu.
        tools: The Tools Menu for this MainApplicationMenu.
        view: The View Menu for this MainApplicationMenu.
    """
    __slots__ = (
        '_edit',
        '_file',
        '_help',
        '_tools',
        '_view',
    )

    def initialize(self, **kwargs) -> bool:
        from pyrox.models.gui.theme import DefaultTheme
        kwargs['background'] = DefaultTheme.background
        kwargs['foreground'] = DefaultTheme.foreground
        kwargs['bg'] = DefaultTheme.background
        kwargs['fg'] = DefaultTheme.foreground
        super().initialize(**kwargs)

        self._file = TkinterMenu()
        self._edit = TkinterMenu()
        self._tools = TkinterMenu()
        self._view = TkinterMenu()
        self._help = TkinterMenu()
        self._file.initialize(master=self.menu, name='file', tearoff=0)
        self._edit.initialize(master=self.menu, name='edit', tearoff=0)
        self._tools.initialize(master=self.menu, name='tools', tearoff=0)
        self._view.initialize(master=self.menu, name='view', tearoff=0)
        self._help.initialize(master=self.menu, name='help', tearoff=0)

        self.menu.add_cascade(label='File', menu=self._file.menu, accelerator='<Alt>F', underline=0)
        self.menu.add_cascade(label='Edit', menu=self._edit.menu, accelerator='<Alt>E', underline=0)
        self.menu.add_cascade(label='Tools', menu=self._tools.menu, accelerator='<Alt>T', underline=0)
        self.menu.add_cascade(label='View', menu=self._view.menu, accelerator='<Alt>V', underline=0)
        self.menu.add_cascade(label='Help', menu=self._help.menu, accelerator='<Alt>H', underline=0)

        from pyrox.services.gui import GuiManager
        root = GuiManager.unsafe_get_backend().get_root_window()
        root.config(menu=self.menu)
        return True

    def get_edit_menu(self) -> TkinterMenu:
        return self._edit

    def get_file_menu(self) -> TkinterMenu:
        return self._file

    def get_help_menu(self) -> TkinterMenu:
        return self._help

    def get_tools_menu(self) -> TkinterMenu:
        return self._tools

    def get_view_menu(self) -> TkinterMenu:
        return self._view
