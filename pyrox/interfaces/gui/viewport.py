"""Viewport interface definitions.
"""
from abc import ABC, abstractmethod
from pyrox.interfaces.protocols.spatial import IArea2D, IZoomable


class IViewport(
    IArea2D,
    IZoomable,
    ABC
):
    """Interface for a viewport in the GUI."""

    @abstractmethod
    def get_delta(
        self,
        other: 'IViewport',
    ) -> tuple[float, float, float]:
        """Calculate the delta between this viewport and another.

        Args:
            other (IViewport): The other viewport to compare with.
        Returns:
            tuple[float, float, float]: The (dx, dy, zoom) delta values.
        """
        pass

    @abstractmethod
    def reset(
        self
    ) -> None:
        """Reset the viewport to its default state."""
        pass

    @abstractmethod
    def update(
        self,
        other: 'IViewport'
    ) -> None:
        """Update the viewport's position.
        Args:
            other (IViewport): The viewport to copy values from.
        """
        pass
