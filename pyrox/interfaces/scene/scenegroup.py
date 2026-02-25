"""
Interface for user-assembled scene object groups (Type 1 grouping).

A SceneGroup coordinates multiple independently scene-registered objects.
All members remain top-level scene objects but are linked through the group,
which acts as an anchor / bounding container, propagating translations.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import (
    Dict,
    List,
    Optional,
    Protocol,
    runtime_checkable,
)

from pyrox.interfaces.scene.sceneobject import ISceneObject


@runtime_checkable
class ISceneGroup(ISceneObject, Protocol):
    """Coordinator for a user-assembled collection of scene objects.

    Members are independently registered in the parent Scene.
    The group itself is also a scene object (bounding anchor).
    Groups can be disbanded at any time, returning members to standalone status.
    """

    # ---------- Member management ----------

    @abstractmethod
    def add_member(self, obj: ISceneObject) -> None:
        """Add an existing scene object to this group.

        Args:
            obj: The scene object to add as a member.
        """
        ...

    @abstractmethod
    def remove_member(self, obj_id: str) -> None:
        """Remove a member from the group by ID.

        The object is not removed from the scene - it simply becomes ungrouped.

        Args:
            obj_id: The ID of the member to remove.
        """
        ...

    @abstractmethod
    def get_members(self) -> Dict[str, ISceneObject]:
        """Get all members of this group.

        Returns:
            Dict mapping member ID to scene object.
        """
        ...

    @abstractmethod
    def get_member(self, obj_id: str) -> Optional[ISceneObject]:
        """Get a specific member by ID.

        Args:
            obj_id: The ID of the member.

        Returns:
            The scene object, or None if not a member.
        """
        ...

    @abstractmethod
    def has_member(self, obj_id: str) -> bool:
        """Check whether an object is a member of this group.

        Args:
            obj_id: The ID to check.

        Returns:
            True if the object is a member, False otherwise.
        """
        ...

    # ---------- Spatial operations ----------

    @abstractmethod
    def move_delta(self, dx: float, dy: float) -> None:
        """Translate the group and all members by (dx, dy).

        Args:
            dx: Horizontal displacement.
            dy: Vertical displacement.
        """
        ...

    @abstractmethod
    def recompute_bounds(self) -> None:
        """Recompute the group's bounding box from its current members.

        Should be called whenever a member is added, removed, or moved.
        """
        ...

    # ---------- Lifecycle ----------

    @abstractmethod
    def disband(self) -> List[ISceneObject]:
        """Disband the group, clearing group membership from all members.

        After this call the group should be removed from the scene by the caller.
        Members remain in the scene as standalone objects.

        Returns:
            List of all former member objects.
        """
        ...

    @abstractmethod
    def duplicate(self) -> "ISceneGroup":
        """Create a deep copy of the group with fresh IDs for all members.

        Returns:
            A new ISceneGroup containing deep-copied members.
        """
        ...

    # ---------- Member IDs (for serialization) ----------

    @abstractmethod
    def get_member_ids(self) -> List[str]:
        """Get the IDs of all current members.

        Returns:
            List of member IDs.
        """
        ...


@runtime_checkable
class IGroupable(Protocol):
    """Mixin protocol for scene objects that can belong to a group."""

    @abstractmethod
    def get_group_id(self) -> Optional[str]:
        """Get the ID of the group this object belongs to, or None.

        Returns:
            Group ID string, or None if not grouped.
        """
        ...

    @abstractmethod
    def set_group_id(self, group_id: Optional[str]) -> None:
        """Set the group ID for this object.

        Args:
            group_id: The group's scene object ID, or None to ungroup.
        """
        ...


__all__ = ["ISceneGroup", "IGroupable"]
