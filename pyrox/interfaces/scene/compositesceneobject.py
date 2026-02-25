"""
Interface for design-locked composite scene objects (Type 2 grouping).

A CompositeSceneObject is the sole scene-registered object.  Its children
(components) are owned internally and are stored with relative offsets from
the composite's origin.  Components cannot be extracted or ungrouped —
the composition is intentional by design (e.g. a control panel with buttons).
"""
from __future__ import annotations

from abc import abstractmethod
from typing import (
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

from pyrox.interfaces.scene.sceneobject import ISceneObject


@runtime_checkable
class ICompositeSceneObject(ISceneObject, Protocol):
    """A design-locked scene object that owns child components at fixed offsets.

    The composite itself is the only object registered in the Scene.
    Each component is positioned relative to the composite's origin:

        world_x = composite.x + component_offset_x
        world_y = composite.y + component_offset_y

    Components are not independently selectable or movable by the user.
    Events (clicks, updates) are dispatched to the appropriate component
    by the composite.
    """

    # ---------- Component management ----------

    @abstractmethod
    def add_component(
        self,
        name: str,
        obj: ISceneObject,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        """Register a child component at a relative offset.

        Args:
            name:     Logical name used to retrieve this component later.
            obj:      The scene object acting as the component.
            offset_x: Horizontal offset from the composite's origin.
            offset_y: Vertical offset from the composite's origin.
        """
        ...

    @abstractmethod
    def remove_component(self, name: str) -> None:
        """Remove a component by name.

        Args:
            name: The logical name of the component to remove.
        """
        ...

    @abstractmethod
    def get_component(self, name: str) -> Optional[ISceneObject]:
        """Retrieve a component by its logical name.

        Args:
            name: The logical name of the component.

        Returns:
            The component scene object, or None if not found.
        """
        ...

    @abstractmethod
    def get_components(self) -> Dict[str, Tuple[ISceneObject, float, float]]:
        """Get all components with their offsets.

        Returns:
            Dict mapping component name to (scene_object, offset_x, offset_y).
        """
        ...

    @abstractmethod
    def get_component_world_position(self, name: str) -> Optional[Tuple[float, float]]:
        """Get the world-space position of a component.

        Computed as (composite.x + offset_x, composite.y + offset_y).

        Args:
            name: The logical name of the component.

        Returns:
            (world_x, world_y), or None if component not found.
        """
        ...

    @abstractmethod
    def get_component_at_point(self, x: float, y: float) -> Optional[ISceneObject]:
        """Find the topmost component that contains the given world-space point.

        Args:
            x: World-space X coordinate.
            y: World-space Y coordinate.

        Returns:
            The matching component, or None if no component is at that point.
        """
        ...

    # ---------- Component listing ----------

    @abstractmethod
    def get_component_names(self) -> List[str]:
        """Get the logical names of all registered components.

        Returns:
            List of component names.
        """
        ...

    @abstractmethod
    def has_component(self, name: str) -> bool:
        """Check whether a component with the given name exists.

        Args:
            name: The logical name to check.

        Returns:
            True if the component exists, False otherwise.
        """
        ...


__all__ = ["ICompositeSceneObject"]
