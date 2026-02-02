"""Gui Menu Interface Module.
"""
from abc import abstractmethod
from typing import Any, Callable, Optional, Union
from .component import IGuiComponent


class IGuiMenu(IGuiComponent):
    """Interface for GUI menus.

    Provides functionality for creating and managing menu items,
    submenus, separators, and menu actions.
    """

    @property
    def root(self) -> Any:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.menu

    @root.setter
    def root(self, value: Any) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        self.menu = value

    @property
    @abstractmethod
    def menu(self) -> Any:
        """Get the underlying menu object.

        Returns:
            Any: The menu object specific to the GUI framework.
        """
        raise NotImplementedError("menu property must be implemented by subclass.")

    @menu.setter
    @abstractmethod
    def menu(self, value: Any) -> None:
        """Set the underlying menu object.

        Args:
            value: The menu object specific to the GUI framework.
        """
        raise NotImplementedError("menu setter must be implemented by subclass.")

    @abstractmethod
    def add_checkbutton(
        self,
        label: str,
        variable: Any,
        command: Optional[Callable] = None,
        index: Union[int, str] = 'end',
        underline: int = -1,
        **kwargs
    ) -> None:
        """Add a checkbutton menu item.

        Args:
            label: The menu item label.
            variable: The variable linked to the checkbutton state.
            command: Optional command to execute when clicked.
            index: The index at which to add the item.
            underline: Index of character to underline.
            **kwargs: Additional menu item properties.
        """
        raise NotImplementedError("add_checkbutton method must be implemented by subclass.")

    @abstractmethod
    def add_item(
        self,
        label: str,
        command: Optional[Callable] = None,
        accelerator: str = '',
        index: Union[int, str] = 'end',
        underline: int = -1,
        **kwargs
    ) -> Any:
        """Add a menu item.

        Args:
            label: The menu item label.
            command: Optional command to execute when clicked.
            accelerator: Keyboard shortcut text.
            index: The index at which to add the item.
            underline: Index of character to underline.
            **kwargs: Additional menu item properties.

        Returns:
            Any: The created menu item reference.
        """
        raise NotImplementedError("add_item method must be implemented by subclass.")

    @abstractmethod
    def add_separator(self) -> None:
        """Add a separator to the menu."""
        raise NotImplementedError("add_separator method must be implemented by subclass.")

    @abstractmethod
    def add_submenu(
        self,
        label: str,
        submenu: 'IGuiMenu',
        **kwargs
    ) -> None:
        """Add a submenu.

        Args:
            label: The submenu label.
            submenu: The submenu to add.
            **kwargs: Additional submenu properties.
        """
        raise NotImplementedError("add_submenu method must be implemented by subclass.")

    @abstractmethod
    def clear(self) -> None:
        """Remove all menu items."""
        raise NotImplementedError("clear method must be implemented by subclass.")

    @abstractmethod
    def config_item(
        self,
        index: Union[int, str],
        **kwargs
    ) -> None:
        """Configure a specific menu item.

        Args:
            index: The index of the menu item to configure.
            **kwargs: Configuration options for the menu item.
        """
        raise NotImplementedError("config_item method must be implemented by subclass.")

    @abstractmethod
    def get_items(self) -> list:
        """Get a list of all menu items.

        Returns:
            list: A list of menu item references.
        """
        raise NotImplementedError("get_items method must be implemented by subclass.")

    @abstractmethod
    def remove_item(
        self,
        index: Union[int, str],
    ) -> bool:
        """Remove a menu item by index.

        Args:
            index: The index of the item to remove.

        Returns:
            bool: True if removal was successful.
        """
        raise NotImplementedError("remove_item method must be implemented by subclass.")


class IApplicationGuiMenu(IGuiMenu):
    """Interface for application-level menus.

    Extends IGuiMenu with application-specific functionality such as
    standard menu items (File, Edit, View, etc.) and menu bar management.
    """

    @abstractmethod
    def get_edit_menu(self) -> IGuiMenu:
        """Create and return a standard Edit menu.

        Returns:
            IGuiMenu: The created Edit menu.
        """
        raise NotImplementedError("get_edit_menu method must be implemented by subclass.")

    @abstractmethod
    def get_file_menu(self) -> IGuiMenu:
        """Create and return a standard File menu.

        Returns:
            IGuiMenu: The created File menu.
        """
        raise NotImplementedError("get_file_menu method must be implemented by subclass.")

    @abstractmethod
    def get_help_menu(self) -> IGuiMenu:
        """Create and return a standard Help menu.

        Returns:
            IGuiMenu: The created Help menu.
        """
        raise NotImplementedError("get_help_menu method must be implemented by subclass.")

    @abstractmethod
    def get_tools_menu(self) -> IGuiMenu:
        """Create and return a standard Tools menu.

        Returns:
            IGuiMenu: The created Tools menu.
            """
        raise NotImplementedError("get_tools_menu method must be implemented by subclass.")

    @abstractmethod
    def get_view_menu(self) -> IGuiMenu:
        """Create and return a standard View menu.

        Returns:
            IGuiMenu: The created View menu.
        """
        raise NotImplementedError("get_view_menu method must be implemented by subclass.")

    def unsafe_get_edit_menu(self) -> IGuiMenu:
        """Get the Edit menu, raising an error if not found.

        Returns:
            IGuiMenu: The Edit menu.
        """
        menu = self.get_edit_menu()
        if menu is None:
            raise RuntimeError("Edit menu not found.")
        return menu

    def unsafe_get_file_menu(self) -> IGuiMenu:
        """Get the File menu, raising an error if not found.

        Returns:
            IGuiMenu: The File menu.
        """
        menu = self.get_file_menu()
        if menu is None:
            raise RuntimeError("File menu not found.")
        return menu

    def unsafe_get_help_menu(self) -> IGuiMenu:
        """Get the Help menu, raising an error if not found.

        Returns:
            IGuiMenu: The Help menu.
        """
        menu = self.get_help_menu()
        if menu is None:
            raise RuntimeError("Help menu not found.")
        return menu

    def unsafe_get_tools_menu(self) -> IGuiMenu:
        """Get the Tools menu, raising an error if not found.

        Returns:
            IGuiMenu: The Tools menu.
        """
        menu = self.get_tools_menu()
        if menu is None:
            raise RuntimeError("Tools menu not found.")
        return menu

    def unsafe_get_view_menu(self) -> IGuiMenu:
        """Get the View menu, raising an error if not found.

        Returns:
            IGuiMenu: The View menu.
        """
        menu = self.get_view_menu()
        if menu is None:
            raise RuntimeError("View menu not found.")
        return menu

    @property
    def edit_menu(self) -> IGuiMenu:
        """Get the Edit menu.

        Returns:
            IGuiMenu: The Edit menu.
        """
        return self.get_edit_menu()

    @property
    def file_menu(self) -> IGuiMenu:
        """Get the File menu.

        Returns:
            IGuiMenu: The File menu.
        """
        return self.get_file_menu()

    @property
    def help_menu(self) -> IGuiMenu:
        """Get the Help menu.

        Returns:
            IGuiMenu: The Help menu.
        """
        return self.get_help_menu()

    @property
    def tools_menu(self) -> IGuiMenu:
        """Get the Tools menu.

        Returns:
            IGuiMenu: The Tools menu.
        """
        return self.get_tools_menu()

    @property
    def view_menu(self) -> IGuiMenu:
        """Get the View menu.

        Returns:
            IGuiMenu: The View menu.
        """
        return self.get_view_menu()
