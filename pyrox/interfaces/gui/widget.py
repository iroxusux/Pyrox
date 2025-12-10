"""Gui Widget Interface Module.
"""
from abc import abstractmethod
from typing import Any, Optional
from .component import IGuiComponent


class IGuiWidget(IGuiComponent):
    """Interface for GUI widgets.

    Extends IGuiComponent with widget-specific functionality such as
    enabling/disabling and focus management.
    """

    @property
    @abstractmethod
    def parent(self) -> Optional['IGuiWidget']:
        """Get the parent widget.

        Returns:
            IGuiWidget: The parent widget.
        """
        raise NotImplementedError("parent property must be implemented by subclass.")

    @parent.setter
    @abstractmethod
    def parent(self, value: Optional['IGuiWidget']) -> None:
        """Set the parent widget.

        Args:
            parent (IGuiWidget): The parent widget.
        """
        raise NotImplementedError("parent setter must be implemented by subclass.")

    @property
    def root(self) -> Any:
        """Get the underlying gui object.

        Returns:
            Any: The gui object specific to the GUI framework.
        """
        return self.widget

    @root.setter
    def root(self, value: Any) -> None:
        """Set the underlying gui object.

        Args:
            value: The gui object specific to the GUI framework.
        """
        self.widget = value

    @property
    @abstractmethod
    def widget(self) -> Any:
        """Get the underlying widget object.

        Returns:
            Any: The widget object specific to the GUI framework.
        """
        raise NotImplementedError("widget property must be implemented by subclass.")

    @widget.setter
    @abstractmethod
    def widget(self, value: Any) -> None:
        """Set the underlying widget object.

        Args:
            value: The widget object specific to the GUI framework.
        """
        raise NotImplementedError("widget setter must be implemented by subclass.")

    @abstractmethod
    def disable(self) -> None:
        """Disable the widget."""
        raise NotImplementedError("disable method must be implemented by subclass.")

    @abstractmethod
    def enable(self) -> None:
        """Enable the widget."""
        raise NotImplementedError("enable method must be implemented by subclass.")

    @abstractmethod
    def focus(self) -> None:
        """Set focus to the widget."""
        raise NotImplementedError("focus method must be implemented by subclass.")

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the widget.

        Returns:
            str: The name of the widget.
        """
        raise NotImplementedError("get_name method must be implemented by subclass.")

    @abstractmethod
    def get_parent(self) -> Optional['IGuiWidget']:
        """Get the parent widget.

        Returns:
            IGuiWidget: The parent widget.
        """
        raise NotImplementedError("get_parent method must be implemented by subclass.")

    @abstractmethod
    def pack(self, **kwargs) -> None:
        """Pack the widget into its parent container.

        Args:
            **kwargs: Packing options.
        """
        raise NotImplementedError("pack method must be implemented by subclass.")

    @abstractmethod
    def pack_propagate(self, propagate: bool) -> None:
        """Set whether the widget should propagate its size to its parent.

        Args:
            propagate (bool): True to enable propagation, False to disable.
        """
        raise NotImplementedError("pack_propogate method must be implemented by subclass.")

    @abstractmethod
    def set_parent(self, parent: Optional['IGuiWidget']) -> None:
        """Set the parent widget.

        Args:
            parent (IGuiWidget): The parent widget.
        """
        raise NotImplementedError("set_parent method must be implemented by subclass.")

    @abstractmethod
    def update_idletasks(self) -> None:
        """Update the widget's idle tasks."""
        raise NotImplementedError("update_idletasks method must be implemented by subclass.")
