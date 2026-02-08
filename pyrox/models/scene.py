""" Scene management for field scene_object simulations.
"""
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from pyrox.interfaces import (
    IBasePhysicsBody,
    IConnectionRegistry,
    IScene,
    ISceneObject,
)

from pyrox.interfaces.protocols.connection import Connection

from pyrox.models.protocols import (
    Nameable,
    Describable,
)
from pyrox.models.connection import ConnectionRegistry

from pyrox.models.physics.factory import PhysicsSceneFactory


class SceneObject(
        ISceneObject,
        Nameable,
        Describable,
):
    """Base class for scene objects.
    """

    def __init__(
        self,
        name: str,
        scene_object_type: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        properties: Optional[Dict] = None,
        parent: Optional['SceneObject'] = None,
    ):
        Nameable.__init__(self, name)
        Describable.__init__(self, description)
        self._scene_object_type = scene_object_type
        self._properties: Dict[str, Any] = properties if properties is not None else dict()
        self._physics_body = physics_body

        # Parent-child hierarchy
        self._parent: Optional['SceneObject'] = parent
        self._children: Dict[str, 'SceneObject'] = {}

        # Event handlers for interactive elements
        self._on_click_handlers: list[Callable] = []
        self._on_hover_handlers: list[Callable] = []
        self._clickable: bool = False  # Whether this object responds to clicks

    # Properties and serialization methods
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
            "name": self.physics_body.name,
            "id": self.physics_body.id,
            "template_name": self.physics_body.template_name,
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
            "name": self.name,
            "scene_object_type": self._scene_object_type,
            "id": self.id,
            "description": self._description,
            "properties": self.properties,
            "body": body,
            "material": material,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SceneObject":
        """Create scene object from dictionary."""
        body_data: dict = data.get("body", {})
        body_template = PhysicsSceneFactory.get_template(body_data.get("template_name", ""))
        if not body_template:
            raise ValueError(
                f"physics body template type '{data.get('template_name', '')}' is not registered. "
                f"Available types: {PhysicsSceneFactory.get_all_templates().keys()}"
            )
        body = body_template.body_class.from_dict(data.get("body", {}))
        if not body:
            raise ValueError("Failed to create physics body from dictionary")

        obj = cls(
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

    # Parent-child relationship methods

    def get_parent(self) -> Optional['SceneObject']:
        """Get the parent scene object."""
        return self._parent

    def set_parent(self, parent: Optional['SceneObject']) -> None:
        """Set the parent scene object.

        Args:
            parent: The parent scene object, or None to remove parent
        """
        # Remove from old parent's children
        if self._parent and self.id in self._parent._children:
            del self._parent._children[self.id]

        self._parent = parent

        # Add to new parent's children
        if parent:
            parent._children[self.id] = self

    def add_child(self, child: 'SceneObject') -> None:
        """Add a child scene object.

        Args:
            child: The child scene object to add
        """
        child.set_parent(self)

    def remove_child(self, child_id: str) -> None:
        """Remove a child scene object.

        Args:
            child_id: The ID of the child to remove
        """
        if child_id in self._children:
            self._children[child_id].set_parent(None)

    def get_children(self) -> Dict[str, 'SceneObject']:
        """Get all child scene objects.

        Returns:
            Dictionary of child scene objects by ID
        """
        return self._children

    def get_child(self, child_id: str) -> Optional['SceneObject']:
        """Get a specific child by ID.

        Args:
            child_id: The ID of the child to retrieve

        Returns:
            The child scene object, or None if not found
        """
        return self._children.get(child_id)

    # Click event methods

    def set_clickable(self, clickable: bool) -> None:
        """Set whether this object responds to clicks.

        Args:
            clickable: True to enable click handling, False to disable
        """
        self._clickable = clickable

    def is_clickable(self) -> bool:
        """Check if this object responds to clicks.

        Returns:
            True if clickable, False otherwise
        """
        return self._clickable

    def add_on_click_handler(self, handler: Callable) -> None:
        """Add a click event handler.

        Args:
            handler: Callable that takes (scene_object, x, y) as arguments
        """
        if handler not in self._on_click_handlers:
            self._on_click_handlers.append(handler)

    def remove_on_click_handler(self, handler: Callable) -> None:
        """Remove a click event handler.

        Args:
            handler: The handler to remove
        """
        if handler in self._on_click_handlers:
            self._on_click_handlers.remove(handler)

    def trigger_click(self, x: float, y: float) -> None:
        """Trigger click event at the specified coordinates.

        Args:
            x: X coordinate of the click in scene space
            y: Y coordinate of the click in scene space
        """
        if self._clickable:
            for handler in self._on_click_handlers:
                handler(self, x, y)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is within this object's bounds.

        Args:
            x: X coordinate in scene space
            y: Y coordinate in scene space

        Returns:
            True if point is inside bounds, False otherwise
        """
        return (
            self.x <= x <= self.x + self.width and
            self.y <= y <= self.y + self.height
        )

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

    # IConnectable interface

    def get_connections(self) -> list[Connection]:
        return self.physics_body.get_connections()

    def set_connections(self, connections: list[Connection]) -> None:
        self.physics_body.set_connections(connections)

    def get_outputs(self) -> dict[str, Any]:
        return self.physics_body.get_outputs()

    def get_inputs(self) -> dict[str, Any]:
        return self.physics_body.get_inputs()

    # IHasId interface
    def get_id(self) -> str:
        return self.physics_body.id

    def set_id(self, id: str) -> None:
        raise NotImplementedError("ID cannot be changed after creation")


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
