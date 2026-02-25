""" Scene class for maintaining a collection of scene objects.
"""
import json
from pathlib import Path
from typing import (
    Any,
    Callable,
)
from pyrox.interfaces import (
    IConnectionRegistry,
    IScene,
    ISceneObject,
    ICompositeSceneObject,
    ISceneGroup,
)
from pyrox.models.connection import ConnectionRegistry
from pyrox.models.scene.sceneobject import SceneObject


class Scene(IScene):
    """Class representing a scene containing scene_objects and tags.
    """

    def __init__(
        self,
        name: str = "Untitled Scene",
        description: str = "",
    ):
        self._name = name
        self._description = description
        self._scene_objects: dict[str, ISceneObject] = {}
        self._on_scene_object_added: list[Callable] = []
        self._on_scene_object_removed: list[Callable] = []
        self._on_scene_updated: list[Callable] = []

        # Connection registry
        self._connection_registry = ConnectionRegistry()

    def get_name(self) -> str:
        """Get the name of the scene."""
        return self._name

    def set_name(self, name: str) -> None:
        """Set the name of the scene."""
        if not name:
            raise ValueError("Scene name cannot be empty")
        self._name = name

    def get_description(self) -> str:
        """Get the description of the scene."""
        return self._description

    def set_description(self, description: str) -> None:
        """Set the description of the scene."""
        self._description = description

    def add_scene_object(
        self,
        scene_object: ISceneObject | ICompositeSceneObject | ISceneGroup
    ) -> None:
        """Add a scene object to the scene.

        Args:
            scene_object: Scene object to add

        Raises:
            ValueError: If scene object ID already exists
        """
        if scene_object.id in self._scene_objects:
            raise ValueError(f"Scene object with ID '{scene_object.id}' already exists in scene")

        self._scene_objects[scene_object.id] = scene_object
        self._connection_registry.register_object(
            scene_object.id,
            scene_object
        )
        [callback(scene_object) for callback in self._on_scene_object_added]

    def remove_scene_object(
        self,
        scene_object_id: str
    ) -> None:
        """Remove a scene object from the scene.

        Args:
            scene_object_id: ID of the scene object to remove
        """
        if scene_object_id in self._scene_objects:
            # Before the object is removed, call the callbacks
            obj = self._scene_objects[scene_object_id]
            [callback(obj) for callback in self._on_scene_object_removed]
            self._connection_registry.unregister_object(scene_object_id)
            # Remove the object
            del self._scene_objects[scene_object_id]

    def get_scene_object(
        self,
        scene_object_id: str
    ) -> ISceneObject | ICompositeSceneObject | ISceneGroup | None:
        """Get a scene object by ID."""
        return self._scene_objects.get(scene_object_id)

    def get_scene_objects(self) -> dict[str, ISceneObject | ICompositeSceneObject | ISceneGroup]:
        """Get all scene objects in the scene.

        Returns:
            dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
        """
        return self._scene_objects

    def set_scene_objects(self, scene_objects: dict[str, ISceneObject | ICompositeSceneObject | ISceneGroup]) -> None:
        """Set the scene objects for the scene.

        Args:
            scene_objects (dict[str, ISceneObject]): A dictionary of scene objects by their IDs.
        """
        if not isinstance(scene_objects, dict):
            raise ValueError("scene_objects must be a dictionary")
        self._scene_objects = scene_objects

    def get_on_scene_object_added(self) -> list[Callable]:
        return self._on_scene_object_added

    def get_on_scene_object_removed(self) -> list[Callable]:
        return self._on_scene_object_removed

    def get_connection_registry(self) -> IConnectionRegistry:
        """Get the connection registry for the scene.

        Returns:
            IConnectionRegistry: The connection registry instance.
        """
        return self._connection_registry

    def set_connection_registry(self, registry: IConnectionRegistry) -> None:
        """Set the connection registry for the scene.

        Args:
            registry (IConnectionRegistry): The connection registry instance.
        """
        self._connection_registry = registry

    def get_on_scene_updated(self) -> list[Callable[..., Any]]:
        return self._on_scene_updated

    def update(self, delta_time: float) -> None:
        """
        Update all scene objects in the scene.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        for scene_object in self._scene_objects.values():
            scene_object.update(delta_time)
        # Call on-scene-updated callbacks
        for callback in self._on_scene_updated.copy():
            try:
                callback(self, delta_time)
            except Exception as e:
                print(f"Error in on_scene_updated callback: {e}")
                self._on_scene_updated.remove(callback)

    def to_dict(self) -> dict:
        """Convert scene to dictionary for JSON serialization."""
        return {
            "name": self._name,
            "description": self._description,
            "scene_objects": [
                scene_object.to_dict() for scene_object in self._scene_objects.values()
            ],
            "connections": self._connection_registry.serialize()["connections"],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> IScene:
        """Create scene from dictionary.

        Uses a 2-pass strategy:
        * Pass 1 — create all plain SceneObjects, CompositeSceneObjects, and
          SceneGroup *shells* (without member links).
        * Pass 2 — link SceneGroup shells to their previously-created members.
        """
        # Import here to avoid circular imports at module level.
        from pyrox.models.scene.scenegroup import SceneGroup, SCENE_OBJECT_TYPE_GROUP
        from pyrox.models.scene.compositesceneobject import (
            CompositeSceneObject,
            SCENE_OBJECT_TYPE_COMPOSITE,
        )

        scene = cls(
            name=data.get("name", "Untitled Scene"),
            description=data.get("description", ""),
        )

        # ------ Pass 1: instantiate every scene object ------
        groups: list[SceneGroup] = []
        for scene_object_data in data.get("scene_objects", []):
            sot = scene_object_data.get("scene_object_type", "")

            if sot == SCENE_OBJECT_TYPE_GROUP:
                obj = SceneGroup.from_dict(scene_object_data)
                groups.append(obj)
            elif sot == SCENE_OBJECT_TYPE_COMPOSITE or scene_object_data.get("components"):
                obj = CompositeSceneObject.from_dict(scene_object_data)
            else:
                obj = SceneObject.from_dict(scene_object_data)

            scene.add_scene_object(obj)
            scene._connection_registry.register_object(obj.id, obj)

        # ------ Pass 2: link group members ------
        for group in groups:
            pending_ids: list[str] = getattr(group, "_pending_member_ids", [])
            for member_id in pending_ids:
                member = scene.get_scene_object(member_id)
                if member is not None:
                    group.add_member(member)
            # Clear the temporary attribute
            if hasattr(group, "_pending_member_ids"):
                object.__setattr__(group, "_pending_member_ids", [])

        # ------ Connections ------
        for conn_data in data.get("connections", []):
            scene._connection_registry.connect(
                source_id=conn_data["source"],
                output_name=conn_data["output"],
                target_id=conn_data["target"],
                input_name=conn_data["input"],
            )

        return scene

    # ------------------------------------------------------------------
    # Group convenience helpers
    # ------------------------------------------------------------------

    def group_objects(
        self,
        object_ids: list[str],
        name: str = "Group",
        layer: int = 0,
    ) -> "ISceneGroup":
        """Wrap existing scene objects into a new SceneGroup.

        All objects identified by *object_ids* must already be registered in
        this scene.  A new SceneGroup anchor is added to the scene and its
        bounding box is computed from the members.

        Args:
            object_ids: IDs of the scene objects to group.
            name:       Name for the new SceneGroup.
            layer:      Rendering layer for the group anchor.

        Returns:
            The newly created SceneGroup.

        Raises:
            ValueError: If any ID is not found in this scene.
        """
        from pyrox.models.scene.scenegroup import SceneGroup

        members: list[ISceneObject] = []
        for oid in object_ids:
            obj = self.get_scene_object(oid)
            if obj is None:
                raise ValueError(
                    f"Scene object '{oid}' not found in scene '{self.name}'."
                )
            members.append(obj)

        if not members:
            raise ValueError("Cannot create a group with no members.")

        # Build an anchor physics body from the first member's body type,
        # but strip the ID so a fresh one is auto-generated.
        from pyrox.models.physics.factory import PhysicsSceneFactory

        body_dict = members[0].physics_body.to_dict()
        body_dict.pop("id", None)   # falsy id → auto-generates a new ID
        body_dict["name"] = name

        template_name = body_dict.get("template_name", "")
        body_template = PhysicsSceneFactory.get_template(template_name)
        if not body_template:
            raise RuntimeError(
                f"Physics body template '{template_name}' not registered; "
                "cannot create SceneGroup anchor."
            )
        anchor_body = body_template.body_class.from_dict(body_dict)

        group = SceneGroup(
            name=name,
            physics_body=anchor_body,
            layer=layer,
        )
        for obj in members:
            group.add_member(obj)

        self.add_scene_object(group)
        return group

    def ungroup(self, group_id: str) -> list[ISceneObject]:
        """Disband a SceneGroup, returning members to standalone status.

        The group anchor is removed from the scene; members remain.

        Args:
            group_id: Scene object ID of the SceneGroup to disband.

        Returns:
            list of former member objects.

        Raises:
            ValueError: If the ID does not correspond to a SceneGroup.
        """
        from pyrox.models.scene.scenegroup import SceneGroup

        obj = self.get_scene_object(group_id)
        if obj is None:
            raise ValueError(
                f"Scene object '{group_id}' not found in scene '{self.name}'."
            )
        if not isinstance(obj, SceneGroup):
            raise ValueError(
                f"Scene object '{group_id}' is not a SceneGroup."
            )
        members = obj.disband()
        self.remove_scene_object(group_id)
        return members

    def save(self, filepath: str | Path) -> None:
        """
        Save scene to JSON file.

        Args:
            filepath: Path to save the scene
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(
        cls,
        filepath: str | Path,
    ) -> IScene:
        """
        Load scene from JSON file.

        Args:
            filepath: Path to load the scene from
            factory: Factory for creating scene objects

        Returns:
            Scene: Loaded scene instance

        Raises:
            ValueError: If scene_object_factory is not provided
        """
        filepath = Path(filepath)

        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)
