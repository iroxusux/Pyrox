"""Gui Widget Interface Module.
"""
from abc import abstractmethod
from typing import Generic, TypeVar
from .component import IGuiComponent


T = TypeVar('T')


class IGuiWidget(
    Generic[T],
    IGuiComponent[T],
):
    """Interface for GUI widgets.

    Extends IGuiComponent with widget-specific functionality such as
    enabling/disabling and focus management.
    """

    @abstractmethod
    def disable(self) -> None:
        """Disable the widget."""
        raise NotImplementedError("disable method must be implemented by subclass.")

    @abstractmethod
    def enable(self) -> None:
        """Enable the widget."""
        raise NotImplementedError("enable method must be implemented by subclass.")

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
    def pack_forget(self) -> None:
        """Forget the widget's packing configuration."""
        raise NotImplementedError("pack_forget method must be implemented by subclass.")

    @abstractmethod
    def update_idletasks(self) -> None:
        """Update the widget's idle tasks."""
        raise NotImplementedError("update_idletasks method must be implemented by subclass.")
