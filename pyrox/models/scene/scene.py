""" Scene class for maintaining a collection of scene objects.
"""
import json
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    Union
)
from pyrox.interfaces import (
    IConnectionRegistry,
    IScene,
    ISceneObject,
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
        self._scene_objects: Dict[str, ISceneObject] = {}
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
        scene_object: ISceneObject
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
    ) -> Optional[ISceneObject]:
        """Get a scene object by ID."""
        return self._scene_objects.get(scene_object_id)

    def get_scene_objects(self) -> Dict[str, ISceneObject]:
        """Get all scene objects in the scene.

        Returns:
            Dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
        """
        return self._scene_objects

    def set_scene_objects(self, scene_objects: Dict[str, ISceneObject]) -> None:
        """Set the scene objects for the scene.

        Args:
            scene_objects (Dict[str, ISceneObject]): A dictionary of scene objects by their IDs.
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
        """Create scene from dictionary."""
        scene = cls(
            name=data.get("name", "Untitled Scene"),
            description=data.get("description", ""),
        )

        # Load scene objects
        for scene_object_data in data.get("scene_objects", []):
            scene_object = SceneObject.from_dict(scene_object_data)
            scene.add_scene_object(scene_object)
            scene._connection_registry.register_object(
                scene_object.id, scene_object
            )

        # Load connections
        for conn_data in data.get("connections", []):
            scene._connection_registry.connect(
                source_id=conn_data["source"],
                output_name=conn_data["output"],
                target_id=conn_data["target"],
                input_name=conn_data["input"],
            )

        return scene

    def save(self, filepath: Union[str, Path]) -> None:
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
        filepath: Union[str, Path],
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
