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
    def parent(self) -> Optional['IGuiWidget']:
        """Get the parent widget.

        Returns:
            IGuiWidget: The parent widget.
        """
        return self.get_parent()

    @parent.setter
    def parent(self, value: Optional['IGuiWidget']) -> None:
        """Set the parent widget.

        Args:
            parent (IGuiWidget): The parent widget.
        """
        return self.set_parent(value)

    @property
    def widget(self) -> Any:
        """Get the underlying widget object.

        Returns:
            Any: The widget object specific to the GUI framework.
        """
        return self.get_widget()

    @widget.setter
    def widget(self, value: Any) -> None:
        """Set the underlying widget object.

        Args:
            value: The widget object specific to the GUI framework.
        """
        return self.set_widget(value)

    def get_root(self) -> Any:
        return self.get_widget()

    def set_root(self, root: Any) -> None:
        self.set_widget(root)

    @abstractmethod
    def get_widget(self) -> Any:
        """Get the underlying widget object.

        Returns:
            Any: The widget object specific to the GUI framework.
        """
        raise NotImplementedError("get_widget method must be implemented by subclass.")

    @abstractmethod
    def set_widget(self, value: Any) -> None:
        """Set the underlying widget object.

        Args:
            value: The widget object specific to the GUI framework.
        """
        raise NotImplementedError("set_widget method must be implemented by subclass.")

    @abstractmethod
    def get_parent(self) -> Optional['IGuiWidget']:
        """Get the parent widget.

        Returns:
            IGuiWidget: The parent widget.
        """
        raise NotImplementedError("get_parent method must be implemented by subclass.")

    @abstractmethod
    def set_parent(self, parent: Optional['IGuiWidget']) -> None:
        """Set the parent widget.

        Args:
            parent (IGuiWidget): The parent widget.
        """
        raise NotImplementedError("set_parent method must be implemented by subclass.")

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
    def update_idletasks(self) -> None:
        """Update the widget's idle tasks."""
        raise NotImplementedError("update_idletasks method must be implemented by subclass.")
