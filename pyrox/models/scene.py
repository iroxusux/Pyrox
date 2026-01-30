"""
Scene management for field scene_object simulations.
"""
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, Union
from pyrox.interfaces import IScene, ISceneObject, ISceneObjectFactory
from pyrox.models import CoreMixin, Spatial2D
from pyrox.models.protocols.physics import PhysicsBody2D, Material
from pyrox.interfaces.protocols.physics import BodyType, ColliderType, CollisionLayer


class SceneObject(
        ISceneObject,
        CoreMixin,
        Spatial2D,
):
    """Base class for scene objects.
    """

    def __init__(
        self,
        id: str,
        name: str,
        scene_object_type: str,
        description: str = "",
        properties: Optional[Dict] = None,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
    ):
        CoreMixin.__init__(
            self,
            id=id,
            name=name,
            description=description
        )
        Spatial2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw
        )
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

    def update(self, dt: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        pass


class PhysicsSceneObject(
        SceneObject,
        PhysicsBody2D,
):
    """Scene object with physics simulation capabilities.

    Combines SceneObject with PhysicsMixin to create objects that can be
    simulated in a physics engine with collision detection, forces, and
    material properties.
    """

    def __init__(
        self,
        id: str,
        name: str,
        scene_object_type: str,
        description: str = "",
        properties: Optional[Dict] = None,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        roll: float = 0.0,
        pitch: float = 0.0,
        yaw: float = 0.0,
        # Physics parameters
        body_type: BodyType = BodyType.DYNAMIC,
        mass: float = 1.0,
        material: Material | None = None,
        collider_type: ColliderType = ColliderType.RECTANGLE,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: list[CollisionLayer] | None = None,
        is_trigger: bool = False,
    ):
        """Initialize physics scene object.

        Args:
            id: Unique identifier
            name: Object name
            scene_object_type: Type classification
            description: Object description
            properties: Additional properties dictionary
            x, y: Position coordinates
            width, height: Size dimensions
            roll, pitch, yaw: Rotation angles
            body_type: Physics body type (static, dynamic, kinematic)
            mass: Mass in kilograms
            material: Material properties (creates default if None)
            collider_type: Collision shape type
            collision_layer: Which layer this object is on
            collision_mask: Which layers this object collides with
            is_trigger: Whether this is a trigger (no physics response)
        """
        # Initiialize SceneObject first
        SceneObject.__init__(
            self,
            id=id,
            name=name,
            scene_object_type=scene_object_type,
            description=description,
            properties=properties,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw
        )

        # Initialize PhysicsMixin
        PhysicsBody2D.__init__(
            self,
            x=x,
            y=y,
            width=width,
            height=height,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            body_type=body_type,
            mass=mass,
            material=material,
            collider_type=collider_type,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            is_trigger=is_trigger,
        )

        # Store additional scene object attributes
        self._scene_object_type = scene_object_type
        self._properties: Dict[str, Any] = properties if properties is not None else dict()

    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "scene_object_type": self._scene_object_type,
            "description": self.description,
            "properties": self._properties,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            # Physics properties
            "body_type": self.body_type.name,
            "mass": self.mass,
            "collider_type": self.collider.collider_type.name,
            "collision_layer": self.collision_layer.name,
            "is_trigger": self.is_trigger,
            # Material properties
            "density": self.density,
            "restitution": self.restitution,
            "friction": self.friction,
            "drag": self.drag,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PhysicsSceneObject":
        """Create physics scene object from dictionary."""
        # Parse enum values
        body_type = BodyType[data.get("body_type", "DYNAMIC")]
        collider_type = ColliderType[data.get("collider_type", "RECTANGLE")]
        collision_layer = CollisionLayer[data.get("collision_layer", "DEFAULT")]

        # Create material
        material = Material(
            density=data.get("density", 1.0),
            restitution=data.get("restitution", 0.3),
            friction=data.get("friction", 0.5),
            drag=data.get("drag", 0.1),
        )

        return cls(
            id=data["id"],
            name=data["name"],
            scene_object_type=data["scene_object_type"],
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            width=data.get("width", 10.0),
            height=data.get("height", 10.0),
            roll=data.get("roll", 0.0),
            pitch=data.get("pitch", 0.0),
            yaw=data.get("yaw", 0.0),
            body_type=body_type,
            mass=data.get("mass", 1.0),
            material=material,
            collider_type=collider_type,
            collision_layer=collision_layer,
            is_trigger=data.get("is_trigger", False),
        )

    def _compile_properties(self) -> None:
        """Compile properties for physics simulation."""
        self._properties.update({
            # Scene object properties
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scene_object_type": self._scene_object_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            # Kinematic properties
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "acceleration_x": self.acceleration_x,
            "acceleration_y": self.acceleration_y,
            # Physics properties
            "body_type": self.body_type.name,
            "mass": self.mass,
            "collider_type": self.collider.collider_type.name,
            "collision_layer": self.collision_layer.name,
            "is_trigger": self.is_trigger,
            "density": self.density,
            "restitution": self.restitution,
            "friction": self.friction,
            "drag": self.drag,
        })

    def get_properties(self) -> Dict:
        self._compile_properties()
        return super().get_properties()


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
