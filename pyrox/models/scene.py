"""
Scene management for field scene_object simulations.
"""
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Union
from pyrox.interfaces import (
    IBasePhysicsBody,
    IScene,
    ISceneObject,
    ISceneObjectFactory
)
from pyrox.services import log
from pyrox.models.protocols import (
    HasId,
    Nameable,
    Describable,
)

from pyrox.models.physics.factory import PhysicsSceneFactory


class SceneObject(
        ISceneObject,
        HasId,
        Nameable,
        Describable,
):
    """Base class for scene objects.
    """

    def __init__(
        self,
        id: str,
        name: str,
        scene_object_type: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        properties: Optional[Dict] = None,
    ):
        HasId.__init__(self, id)
        Nameable.__init__(self, name)
        Describable.__init__(self, description)
        self._scene_object_type = scene_object_type
        self._properties: Dict[str, Any] = properties if properties is not None else dict()
        self._physics_body = physics_body

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

    def get_property(self, name: str) -> Any:
        """Get a single property of the scene object.

        Args:
            name (str): The property name.

        Returns:
            Any: The property value, or None if not found.
        """
        if hasattr(self, name):
            self._properties[name] = getattr(self, name)
        return self._properties.get(name)

    def get_properties(self) -> Dict:
        """Get the properties of the scene object.

        Returns:
            Dict: The properties of the scene object.
        """
        self._compile_properties()
        return self._properties

    def set_property(self, name: str, value: Any) -> None:
        """Set a single property of the scene object.

        Args:
            key (str): The property key.
            value (Any): The property value.
        """
        # Check to see if the property exists as an attribute of this object
        if hasattr(self, name):
            setattr(self, name, value)
        self._properties[name] = value

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

    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        material = {
            "density": self.physics_body.material.density,
            "restitution": self.physics_body.material.restitution,
            "friction": self.physics_body.material.friction,
            "drag": self.physics_body.material.drag,
        }
        body = {
            "name": self.name,
            "tags": self.physics_body.tags,
            "body_type": self.physics_body.body_type.name,
            "enabled": self.physics_body.enabled,
            "sleeping": self.physics_body.sleeping,
            "mass": self.physics_body.mass,
            "moment_of_inertia": self.physics_body.moment_of_inertia,
            "velocity_x": self.physics_body.velocity_x,
            "velocity_y": self.physics_body.velocity_y,
            "acceleration_x": self.physics_body.acceleration_x,
            "acceleration_y": self.physics_body.acceleration_y,
            "angular_velocity": self.physics_body.angular_velocity,
            "collider_type": self.physics_body.collider.collider_type.name,
            "collision_layer": self.physics_body.collider.collision_layer.name,
            "collision_mask": [m.name for m in self.physics_body.collider.collision_mask],
            "is_trigger": self.physics_body.collider.is_trigger,
            "x": self.physics_body.x,
            "y": self.physics_body.y,
            "width": self.physics_body.width,
            "height": self.physics_body.height,
            "roll": self.physics_body.roll,
            "pitch": self.physics_body.pitch,
            "yaw": self.physics_body.yaw,
            "material": material,
        }

        return {
            "id": self.id,
            "name": self.name,
            "scene_object_type": self._scene_object_type,
            "description": self._description,
            "properties": self.properties,
            "body": body,
            "material": material,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SceneObject":
        """Create scene object from dictionary."""
        body_template = PhysicsSceneFactory.get_template(data.get("name", ""))
        if not body_template:
            raise ValueError(
                f"physics body template type '{data.get('name', '')}' is not registered. "
                f"Available types: {PhysicsSceneFactory.get_all_templates().keys()}"
            )
        body = body_template.body_class.from_dict(data)
        if not body:
            raise ValueError("Failed to create physics body from dictionary")

        obj = cls(
            id=data["id"],
            name=data["name"],
            scene_object_type=data["scene_object_type"],
            physics_body=body,
            description=data.get("description", ""),
            properties=data.get("properties", {})
        )

        return obj

    def update(self, dt: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        pass

    def get_physics_body(self) -> IBasePhysicsBody:
        return self._physics_body

    def set_physics_body(self, physics_body: IBasePhysicsBody) -> None:
        self._physics_body = physics_body

    def _compile_properties(self) -> None:
        """Compile properties for physics simulation."""
        self._properties.update({
            # Scene object properties
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scene_object_type": self._scene_object_type,
            # Physics body properties
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "roll": self.physics_body.roll,
            "pitch": self.physics_body.pitch,
            "yaw": self.physics_body.yaw,
            "velocity_x": self.physics_body.velocity_x,
            "velocity_y": self.physics_body.velocity_y,
            "acceleration_x": self.physics_body.acceleration_x,
            "acceleration_y": self.physics_body.acceleration_y,
            "body_type": self.physics_body.body_type.name,
            "mass": self.physics_body.mass,
            # Collider properties
            "collider_type": self.physics_body.collider.collider_type.name,
            "collision_layer": self.physics_body.collider.collision_layer.name,
            "is_trigger": self.physics_body.collider.is_trigger,
            # Material properties
            "density": self.physics_body.material.density,
            "restitution": self.physics_body.material.restitution,
            "friction": self.physics_body.material.friction,
            "drag": self.physics_body.material.drag,
        })


class SceneObjectFactory(ISceneObjectFactory):
    """
    Factory for registering and creating scene_object instances.

    Allows custom scene_object types to be registered and instantiated
    from serialized data.
    """
    _registry: Dict[str, Type[ISceneObject]] = {}

    def __init__(self):
        """Initialize the scene_object factory."""
        raise ValueError("SceneObjectFactory cannot be instantiated directly. Use class methods only.")

    @classmethod
    def register(
        cls,
        scene_object_type: str,
        scene_object_class: Type[ISceneObject]
    ) -> None:
        if scene_object_type in SceneObjectFactory._registry:
            log(SceneObjectFactory).warning(
                f"scene_object type '{scene_object_type}' is already registered. Overwriting."
            )

        SceneObjectFactory._registry[scene_object_type] = scene_object_class

    @classmethod
    def unregister(
        cls,
        scene_object_type: str
    ) -> None:
        SceneObjectFactory._registry.pop(scene_object_type, None)

    @classmethod
    def get_registered_types(cls) -> list[str]:
        return list(SceneObjectFactory._registry.keys())

    @classmethod
    def create_scene_object(
        cls,
        data: dict
    ) -> ISceneObject:
        scene_object_type = data.get("name")

        if scene_object_type not in SceneObjectFactory._registry:
            raise ValueError(
                f"scene_object type '{scene_object_type}' is not registered. "
                f"Available types: {SceneObjectFactory.get_registered_types()}"
            )

        scene_object_class = SceneObjectFactory._registry[scene_object_type]
        return scene_object_class.from_dict(data)


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
    ) -> IScene:
        """Create scene from dictionary."""
        scene = cls(
            name=data.get("name", "Untitled Scene"),
            description=data.get("description", ""),
        )

        # Load scene objects
        for scene_object_data in data.get("scene_objects", []):
            scene_object = SceneObjectFactory.create_scene_object(scene_object_data)
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


def register_scene_object_from_physics_factory() -> None:
    """Register all physics body templates as scene object types."""
    for template in PhysicsSceneFactory.get_all_templates().values():

        raise RuntimeError("This is where we are failing!")
        # we are registering each physics body class as a scene object class, however, this is registering the physics body itself, not a scene object which wraps it.
        # TODO: Fix this by creating a workflow to wrap the physics body in a scene object when registering.

        SceneObjectFactory.register(
            scene_object_type=template.name,
            scene_object_class=template.body_class
        )


# Register base SceneObject type
SceneObjectFactory.register(
    scene_object_type="SceneObject",
    scene_object_class=SceneObject
)

# Register all physics body templates as scene object types
register_scene_object_from_physics_factory()
