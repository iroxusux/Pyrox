"""
SceneGroup: user-assembled group of scene objects (Type 1 grouping).

All members remain independently registered in the scene.  The group itself
is also registered as a scene object and acts as a bounding anchor.
"""
from __future__ import annotations

import copy
from typing import (
    Dict,
    List,
    Optional,
)

from pyrox.interfaces import (
    IBasePhysicsBody,
    ISceneObject,
)
from pyrox.interfaces.scene.scenegroup import ISceneGroup
from pyrox.models.scene.sceneobject import SceneObject

SCENE_OBJECT_TYPE_GROUP = "group"


class SceneGroup(SceneObject, ISceneGroup):
    """User-assembled group of independently registered scene objects.

    The group is registered in the scene alongside its members.  Moving the
    group propagates the delta to every member.  The group's own physics body
    acts as a bounding box that is recomputed whenever members change.

    Usage::

        group = SceneGroup(name="Conveyor Assembly", physics_body=body)
        group.add_member(conveyor)
        group.add_member(prox_1)
        group.add_member(prox_2)
        scene.add_scene_object(group)

        # Move everything together
        group.move_delta(100, 0)

        # Later — disband
        members = group.disband()
        scene.remove_scene_object(group.id)
    """

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        properties: Optional[Dict] = None,
        parent: Optional[SceneObject] = None,
        layer: int = 0,
    ):
        super().__init__(
            name=name,
            scene_object_type=SCENE_OBJECT_TYPE_GROUP,
            physics_body=physics_body,
            description=description,
            properties=properties,
            parent=parent,
            layer=layer,
        )
        # Members keyed by their scene object ID
        self._members: Dict[str, ISceneObject] = {}

    # ------------------------------------------------------------------
    # ISceneGroup — member management
    # ------------------------------------------------------------------

    def add_member(self, obj: ISceneObject) -> None:
        """Add an existing scene object to this group."""
        if obj.id == self.id:
            raise ValueError("A group cannot be a member of itself.")
        self._members[obj.id] = obj
        # Tag the object with this group's ID (if it supports it)
        if hasattr(obj, "set_group_id"):
            obj.set_group_id(self.id)  # type: ignore[union-attr]
        self.recompute_bounds()

    def remove_member(self, obj_id: str) -> None:
        """Remove a member by ID (object stays in scene)."""
        if obj_id in self._members:
            obj = self._members.pop(obj_id)
            if hasattr(obj, "set_group_id"):
                obj.set_group_id(None)  # type: ignore[union-attr]
            self.recompute_bounds()

    def get_members(self) -> Dict[str, ISceneObject]:
        return dict(self._members)

    def get_member(self, obj_id: str) -> Optional[ISceneObject]:
        return self._members.get(obj_id)

    def has_member(self, obj_id: str) -> bool:
        return obj_id in self._members

    def get_member_ids(self) -> List[str]:
        return list(self._members.keys())

    # ------------------------------------------------------------------
    # ISceneGroup — spatial operations
    # ------------------------------------------------------------------

    def move_delta(self, dx: float, dy: float) -> None:
        """Translate all members and the group anchor by (dx, dy)."""
        # Move each member
        for obj in self._members.values():
            obj.physics_body.set_x(obj.x + dx)
            obj.physics_body.set_y(obj.y + dy)
        # Move the anchor itself
        self.physics_body.set_x(self.x + dx)
        self.physics_body.set_y(self.y + dy)

    def recompute_bounds(self) -> None:
        """Recompute this group's bounding box from its current members."""
        if not self._members:
            return

        objects = list(self._members.values())
        min_x = min(o.x for o in objects)
        min_y = min(o.y for o in objects)
        max_x = max(o.x + o.width for o in objects)
        max_y = max(o.y + o.height for o in objects)

        self.physics_body.set_x(min_x)
        self.physics_body.set_y(min_y)
        self.physics_body.set_width(max_x - min_x)
        self.physics_body.set_height(max_y - min_y)

    # ------------------------------------------------------------------
    # ISceneGroup — lifecycle
    # ------------------------------------------------------------------

    def disband(self) -> List[ISceneObject]:
        """Disband the group and return all members as standalone objects."""
        members = list(self._members.values())
        for obj in members:
            if hasattr(obj, "set_group_id"):
                obj.set_group_id(None)  # type: ignore[union-attr]
        self._members.clear()
        return members

    def duplicate(self) -> "SceneGroup":
        """Deep-copy all members with fresh IDs and return a new SceneGroup."""
        # Import here to avoid circular dependency at module level
        from pyrox.models.physics.factory import PhysicsSceneFactory

        new_body_data = self.physics_body.to_dict()
        body_template = PhysicsSceneFactory.get_template(
            new_body_data.get("template_name", "")
        )
        if body_template:
            new_body = body_template.body_class.from_dict(new_body_data)
        else:
            new_body = copy.deepcopy(self.physics_body)

        new_group = SceneGroup(
            name=f"{self.name} (Copy)",
            physics_body=new_body,
            description=self._description,
            properties=copy.deepcopy(self._properties),
            layer=self._layer,
        )

        for obj in self._members.values():
            new_member = copy.deepcopy(obj)
            # Reset the ID so it is regenerated (relies on physics body UUID)
            new_group.add_member(new_member)

        return new_group

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["member_ids"] = self.get_member_ids()
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "SceneGroup":
        """Create a SceneGroup shell from dict.

        Members are linked in a second pass by Scene.from_dict, since the
        member objects must be created first.
        """
        from pyrox.models.physics.factory import PhysicsSceneFactory

        body_data: dict = data.get("body", {})
        body_template = PhysicsSceneFactory.get_template(
            body_data.get("template_name", "")
        )
        if not body_template:
            raise ValueError(
                f"Physics body template '{body_data.get('template_name', '')}' "
                f"not registered."
            )
        body = body_template.body_class.from_dict(body_data)

        group = cls(
            name=data["name"],
            physics_body=body,
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            layer=data.get("layer", 0),
        )
        # member_ids are stored temporarily for the 2-pass load in Scene.from_dict
        object.__setattr__(group, "_pending_member_ids", data.get("member_ids", []))
        return group

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Update all members."""
        for obj in self._members.values():
            obj.update(dt)
