"""
Scene management for field scene_object simulations.
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, Union
from pyrox.interfaces import IScene, ISceneObject, ISceneObjectFactory


class SceneObject(ISceneObject):
    """Base class for scene objects.
    """

    def __init__(
        self,
        id: str,
        name: str,
        scene_object_type: str,
        description: str = "",
        properties: Optional[Dict] = None
    ):
        self._id = id
        self._name = name
        self._description = description
        self._scene_object_type = scene_object_type
        self._properties: Dict[str, Any] = properties if properties is not None else dict()

    def get_id(self) -> str:
        """Get the unique identifier of the scene object.

        Returns:
            str: The unique identifier.
        """
        return self._id

    def set_id(self, id: str) -> None:
        """Set the unique identifier of the scene object.

        Args:
            id (str): The unique identifier.
        """
        self._id = id

    def get_name(self) -> str:
        """Get the name of the scene object.

        Returns:
            str: The name of the scene object.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """Set the name of the scene object.

        Args:
            name (str): The name of the scene object.
        """
        if not name or name.startswith(" "):
            raise ValueError("Scene object name cannot be empty or start with a space.")
        self._name = name

    def get_description(self) -> str:
        """Get the description of the scene object.

        Returns:
            str: The description of the scene object.
        """
        return self._description

    def set_description(self, description: str) -> None:
        """Set the description of the scene object.

        Args:
            description (str): The description of the scene object.
        """
        self._description = description

    def get_properties(self) -> Dict:
        """Get the properties of the scene object.

        Returns:
            Dict: The properties of the scene object.
        """
        return self._properties

    def set_properties(self, properties: Dict) -> None:
        """Set the properties of the scene object.

        Args:
            properties (Dict): The properties to set.
        """
        if not isinstance(properties, dict):
            raise ValueError("Properties must be a dictionary")
        self._properties = properties

    def get_scene_object_type(self) -> str:
        """Get the type of the scene object.

        Returns:
            str: The type of the scene object.
        """
        return self._scene_object_type

    def set_scene_object_type(self, scene_object_type: str) -> None:
        """Set the type of the scene object.

        Args:
            scene_object_type (str): The type of the scene object.
        """
        self._scene_object_type = scene_object_type

    def get_position(self) -> tuple[float, float, float]:
        """Get the position of the scene object as (x, y, z)."""
        return self.x, self.y, self.z

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set the position of the scene object."""
        self.x = x
        self.y = y
        self.z = z

    def get_x(self) -> float:
        """Get the X position of the scene object."""
        return self.properties.get("x", 0.0)

    def set_x(self, x: float) -> None:
        """Set the X position of the scene object."""
        self.properties['x'] = x

    def get_y(self) -> float:
        """Get the Y position of the scene object."""
        return self.properties.get("y", 0.0)

    def set_y(self, y: float) -> None:
        """Set the Y position of the scene object."""
        self.properties['y'] = y

    def get_z(self) -> float:
        """Get the Z position of the scene object."""
        return self.properties.get("z", 0.0)

    def set_z(self, z: float) -> None:
        """Set the Z position of the scene object."""
        self.properties['z'] = z

    def get_rotation(self) -> tuple[float, float, float]:
        """Get the rotation of the scene object as (pitch, yaw, roll)."""
        return self.pitch, self.yaw, self.roll

    def set_rotation(self, pitch: float, yaw: float, roll: float) -> None:
        """Set the rotation of the scene object."""
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll

    def get_pitch(self) -> float:
        """Get the pitch rotation of the scene object."""
        return self.properties.get("pitch", 0.0)

    def set_pitch(self, pitch: float) -> None:
        """Set the pitch rotation of the scene object."""
        self.properties['pitch'] = pitch

    def get_yaw(self) -> float:
        """Get the yaw rotation of the scene object."""
        return self.properties.get("yaw", 0.0)

    def set_yaw(self, yaw: float) -> None:
        """Set the yaw rotation of the scene object."""
        self.properties['yaw'] = yaw

    def get_roll(self) -> float:
        """Get the roll rotation of the scene object."""
        return self.properties.get("roll", 0.0)

    def set_roll(self, roll: float) -> None:
        """Set the roll rotation of the scene object."""
        self.properties['roll'] = roll

    def get_height(self) -> float:
        """Get the height of the scene object."""
        return self.properties.get("height", 0.0)

    def set_height(self, height: float) -> None:
        """Set the height of the scene object."""
        self.properties['height'] = height

    def get_width(self) -> float:
        """Get the width of the scene object."""
        return self.properties.get("width", 0.0)

    def set_width(self, width: float) -> None:
        """Set the width of the scene object."""
        self.properties['width'] = width

    def get_depth(self) -> float:
        """Get the depth of the scene object."""
        return self.properties.get("depth", 0.0)

    def set_depth(self, depth: float) -> None:
        """Set the depth of the scene object."""
        self.properties['depth'] = depth

    def get_size(self) -> tuple[float, float, float]:
        return self.get_width(), self.get_height(), self.get_depth()

    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        return {
            "id": self._id,
            "name": self._name,
            "scene_object_type": self._scene_object_type,
            "description": self._description,
            "properties": self._properties,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SceneObject":
        """Create scene object from dictionary."""
        scene_object = cls(
            id=data["id"],
            name=data["name"],
            scene_object_type=data["scene_object_type"],
            description=data.get("description", ""),
            properties=data.get("properties", {})
        )
        return scene_object

    def update(self, delta_time: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        pass


class SceneObjectFactory(ISceneObjectFactory):
    """
    Factory for registering and creating scene_object instances.

    Allows custom scene_object types to be registered and instantiated
    from serialized data.
    """

    def __init__(self):
        """Initialize the scene_object factory."""
        self._registry: Dict[str, Type[ISceneObject]] = {}

    def register(
        self,
        scene_object_type: str,
        scene_object_class: Type[ISceneObject]
    ) -> None:
        if scene_object_type in self._registry:
            raise ValueError(f"scene_object type '{scene_object_type}' is already registered")

        self._registry[scene_object_type] = scene_object_class

    def unregister(
        self,
        scene_object_type: str
    ) -> None:
        self._registry.pop(scene_object_type, None)

    def get_registered_types(self) -> list[str]:
        return list(self._registry.keys())

    def create_scene_object(self, data: dict) -> ISceneObject:
        scene_object_type = data.get("scene_object_type")

        if scene_object_type not in self._registry:
            raise ValueError(
                f"scene_object type '{scene_object_type}' is not registered. "
                f"Available types: {self.get_registered_types()}"
            )

        scene_object_class = self._registry[scene_object_type]
        return scene_object_class.from_dict(data)


class Scene(IScene):
    """Class representing a scene containing scene_objects and tags.
    """

    def __init__(
        self,
        name: str = "Untitled Scene",
        description: str = "",
        scene_object_factory=None
    ):
        self._name = name
        self._description = description
        self._scene_objects: Dict[str, ISceneObject] = {}
        self._scene_object_factory = scene_object_factory

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

    def remove_scene_object(
        self,
        scene_object_id: str
    ) -> None:
        """Remove a scene object from the scene.

        Args:
            scene_object_id: ID of the scene object to remove
        """
        if scene_object_id in self._scene_objects:
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

    def get_scene_object_factory(self):
        """Get the object factory for loading scenes."""
        return self._scene_object_factory

    def set_scene_object_factory(
        self,
        factory: ISceneObjectFactory
    ) -> None:
        """Set the object factory for loading scenes.

        Args:
            factory: The scene object factory to set.
        """
        self._scene_object_factory = factory

    def update(self, delta_time: float) -> None:
        """
        Update all scene objects in the scene.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        for scene_object in self._scene_objects.values():
            scene_object.update(delta_time)

    def to_dict(self) -> dict:
        """Convert scene to dictionary for JSON serialization."""
        return {
            "name": self._name,
            "description": self._description,
            "scene_objects": [
                scene_object.to_dict() for scene_object in self._scene_objects.values()
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        factory: ISceneObjectFactory
    ) -> IScene:
        """Create scene from dictionary."""
        scene = cls(
            name=data.get("name", "Untitled Scene"),
            description=data.get("description", ""),
            scene_object_factory=factory
        )

        # Load scene objects
        for scene_object_data in data.get("scene_objects", []):
            if factory is None:
                raise ValueError("scene_object_factory is required to load scene objects")
            scene_object = factory.create_scene_object(scene_object_data)
            scene.add_scene_object(scene_object)

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
        factory: ISceneObjectFactory
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
        if factory is None:
            raise ValueError("scene_object_factory is required to load scene")

        filepath = Path(filepath)

        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data, factory=factory)
