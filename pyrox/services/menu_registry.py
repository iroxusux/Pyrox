"""Menu Registry Service for tracking and managing application menu items.

This service provides centralized management of menu items, enabling loose coupling
between services, tasks, and GUI components through a registry pattern.
"""
from typing import Callable, Dict, Optional, Any
from dataclasses import dataclass, field
from pyrox.services.logging import log


@dataclass
class MenuItemDescriptor:
    """Descriptor for a registered menu item."""

    menu_id: str  # Unique identifier for the menu item
    menu_path: str  # e.g., "File/Save Scene" or "View/Scene Viewer/Properties Panel"
    menu_widget: Any  # The actual menu widget (tk.Menu)
    menu_index: int  # Index within the menu
    owner: str  # Task or component that owns this item
    command: Optional[Callable] = None  # The command callback
    enabled: bool = True  # Current enabled state
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata


class MenuRegistry:
    """Static registry for managing menu items across the application.

    This provides a centralized location to:
    - Register menu items with unique IDs
    - Enable/disable menu items by ID or owner
    - Update menu item commands dynamically
    - Query menu item state

    Usage:
        # During task injection
        MenuRegistry.register_item(
            menu_id="scene.save",
            menu_path="File/Save Scene",
            menu_widget=file_menu.menu,
            menu_index=0,
            owner="SceneviewerApplicationTask"
        )

        # From a service
        MenuRegistry.enable_item("scene.save")

        # From a GUI component
        MenuRegistry.set_command("scene.save", my_callback)

        # Bulk operations by owner
        MenuRegistry.enable_items_by_owner("SceneviewerApplicationTask")
    """

    _registry: Dict[str, MenuItemDescriptor] = {}
    _owner_index: Dict[str, list[str]] = {}  # owner -> list of menu_ids

    @classmethod
    def register_item(
        cls,
        menu_id: str,
        menu_path: str,
        menu_widget: Any,
        menu_index: int,
        owner: str,
        command: Optional[Callable] = None,
        **metadata
    ) -> None:
        """Register a menu item in the registry.

        Args:
            menu_id: Unique identifier for the menu item
            menu_path: Human-readable path (e.g., "File/Save Scene")
            menu_widget: The tkinter Menu widget
            menu_index: Index of the item in the menu
            owner: The component that owns this menu item
            command: Optional command callback
            **metadata: Additional metadata to store
        """
        descriptor = MenuItemDescriptor(
            menu_id=menu_id,
            menu_path=menu_path,
            menu_widget=menu_widget,
            menu_index=menu_index,
            owner=owner,
            command=command,
            enabled=True,
            metadata=metadata
        )

        cls._registry[menu_id] = descriptor

        # Update owner index
        if owner not in cls._owner_index:
            cls._owner_index[owner] = []
        cls._owner_index[owner].append(menu_id)

        log(cls).debug(f"Registered menu item: {menu_id} at {menu_path}")

    @classmethod
    def unregister_item(cls, menu_id: str) -> None:
        """Remove a menu item from the registry.

        Args:
            menu_id: The ID of the menu item to remove
        """
        if menu_id in cls._registry:
            descriptor = cls._registry[menu_id]

            # Remove from owner index
            if descriptor.owner in cls._owner_index:
                cls._owner_index[descriptor.owner].remove(menu_id)
                if not cls._owner_index[descriptor.owner]:
                    del cls._owner_index[descriptor.owner]

            del cls._registry[menu_id]
            log(cls).debug(f"Unregistered menu item: {menu_id}")

    @classmethod
    def get_item(cls, menu_id: str) -> Optional[MenuItemDescriptor]:
        """Get a menu item descriptor by ID.

        Args:
            menu_id: The ID of the menu item

        Returns:
            MenuItemDescriptor if found, None otherwise
        """
        return cls._registry.get(menu_id)

    @classmethod
    def enable_item(cls, menu_id: str) -> bool:
        """Enable a menu item.

        Args:
            menu_id: The ID of the menu item to enable

        Returns:
            True if successful, False if menu item not found
        """
        descriptor = cls.get_item(menu_id)
        if descriptor:
            try:
                # Check if it's a separator
                item_type = descriptor.menu_widget.type(descriptor.menu_index)
                if item_type != 'separator':
                    descriptor.menu_widget.entryconfig(descriptor.menu_index, state='normal')
                    descriptor.enabled = True
                    log(cls).debug(f"Enabled menu item: {menu_id}")
                    return True
            except Exception as e:
                log(cls).warning(f"Failed to enable menu item {menu_id}: {e}")
        return False

    @classmethod
    def disable_item(cls, menu_id: str) -> bool:
        """Disable a menu item.

        Args:
            menu_id: The ID of the menu item to disable

        Returns:
            True if successful, False if menu item not found
        """
        descriptor = cls.get_item(menu_id)
        if descriptor:
            try:
                # Check if it's a separator
                item_type = descriptor.menu_widget.type(descriptor.menu_index)
                if item_type != 'separator':
                    descriptor.menu_widget.entryconfig(descriptor.menu_index, state='disabled')
                    descriptor.enabled = False
                    log(cls).debug(f"Disabled menu item: {menu_id}")
                    return True
            except Exception as e:
                log(cls).warning(f"Failed to disable menu item {menu_id}: {e}")
        return False

    @classmethod
    def set_command(cls, menu_id: str, command: Callable | None) -> bool:
        """Set or update the command callback for a menu item.

        Args:
            menu_id: The ID of the menu item
            command: The new command callback

        Returns:
            True if successful, False if menu item not found
        """
        descriptor = cls.get_item(menu_id)
        if descriptor:
            try:
                descriptor.menu_widget.entryconfig(descriptor.menu_index, command=command)
                descriptor.command = command
                log(cls).debug(f"Updated command for menu item: {menu_id}")
                return True
            except Exception as e:
                log(cls).warning(f"Failed to set command for menu item {menu_id}: {e}")
        return False

    @classmethod
    def enable_items_by_owner(cls, owner: str) -> int:
        """Enable all menu items owned by a specific component.

        Args:
            owner: The owner identifier

        Returns:
            Number of items enabled
        """
        count = 0
        menu_ids = cls._owner_index.get(owner, [])
        for menu_id in menu_ids:
            if cls.enable_item(menu_id):
                count += 1
        log(cls).debug(f"Enabled {count} menu items for owner: {owner}")
        return count

    @classmethod
    def disable_items_by_owner(cls, owner: str) -> int:
        """Disable all menu items owned by a specific component.

        Args:
            owner: The owner identifier

        Returns:
            Number of items disabled
        """
        count = 0
        menu_ids = cls._owner_index.get(owner, [])
        for menu_id in menu_ids:
            if cls.disable_item(menu_id):
                count += 1
        log(cls).debug(f"Disabled {count} menu items for owner: {owner}")
        return count

    @classmethod
    def get_items_by_owner(cls, owner: str) -> list[MenuItemDescriptor]:
        """Get all menu items owned by a specific component.

        Args:
            owner: The owner identifier

        Returns:
            List of menu item descriptors
        """
        menu_ids = cls._owner_index.get(owner, [])
        return [cls._registry[mid] for mid in menu_ids if mid in cls._registry]

    @classmethod
    def clear(cls) -> None:
        """Clear the entire registry. Useful for testing."""
        cls._registry.clear()
        cls._owner_index.clear()
        log(cls).debug("Cleared menu registry")

    @classmethod
    def get_all_items(cls) -> Dict[str, MenuItemDescriptor]:
        """Get all registered menu items.

        Returns:
            Dictionary of menu_id -> MenuItemDescriptor
        """
        return cls._registry.copy()
