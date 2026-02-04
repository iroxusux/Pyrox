"""
Scene management for field scene_object simulations.
"""
from abc import abstractmethod
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Optional,
    Protocol,
    runtime_checkable,
    Union
)
from pyrox.interfaces import (
    IHasId,
    INameable,
    IRunnable,
    IBasePhysicsBody,
    IPhysicsBody2D,
)


@runtime_checkable
class ISceneObject(
        IHasId,
        INameable,
        Protocol
):
    """Object base class for scene elements.
    """

    @property
    def properties(self) -> dict:
        """Get the properties of the scene object.

        Returns:
            dict: The properties of the scene object.
        """
        return self.get_properties()

    @properties.setter
    def properties(self, properties: dict) -> None:
        """Set the properties of the scene object.

        Args:
            properties (dict): The properties of the scene object.
        """
        self.set_properties(properties)

    @property
    def scene_object_type(self) -> str:
        """Get the type of the scene object.

        Returns:
            str: The type of the scene object.
        """
        return self.get_scene_object_type()

    @scene_object_type.setter
    def scene_object_type(self, scene_object_type: str) -> None:
        """Set the type of the scene object.

        Args:
            scene_object_type (str): The type of the scene object.
        """
        self.set_scene_object_type(scene_object_type)

    @property
    def physics_body(self) -> IBasePhysicsBody:
        """Get the physics body associated with this scene object.

        Returns:
            Optional[BasePhysicsBody]: The physics body, or None if not set.
        """
        return self.get_physics_body()

    def get_property(self, name: str) -> object:
        """Get a property by name.

        Args:
            name (str): The name of the property.

        Returns:
            object: The value of the property.
        """
        return self.get_properties().get(name)

    def set_property(self, name: str, value: object) -> None:
        """Set a property by name.

        Args:
            name (str): The name of the property.
            value (object): The value to set the property to.
        """
        props = self.get_properties()
        props[name] = value
        self.set_properties(props)

    @abstractmethod
    def get_properties(self) -> dict:
        """Get the properties of the scene object.

        Returns:
            dict: The properties of the scene object.
        """
        ...

    @abstractmethod
    def set_properties(self, properties: dict) -> None:
        """Set the properties of the scene object.

        Args:
            properties (dict): The properties of the scene object.
        """
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        ...

    @abstractmethod
    def get_scene_object_type(self) -> str:
        """Get the type of the scene object.

        Returns:
            str: The type of the scene object.
        """
        ...

    @abstractmethod
    def set_scene_object_type(self, scene_object_type: str) -> None:
        """Set the type of the scene object.

        Args:
            scene_object_type (str): The type of the scene object.
        """
        ...

    @abstractmethod
    def get_physics_body(self) -> IBasePhysicsBody:
        """Get the physics body associated with this scene object.

        Returns:
            Optional[BasePhysicsBody]: The physics body, or None if not set.
        """
        ...

    @abstractmethod
    def set_physics_body(
        self,
        physics_body: IBasePhysicsBody
    ) -> None:
        """Set the physics body associated with this scene object.

        Args:
            physics_body (Optional[BasePhysicsBody]): The physics body to set, or None.
        """
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "ISceneObject":
        """Create scene object from dictionary."""
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        ...

    # ---------- Physics body convenience methods ----------

    @property
    def x(self) -> float:
        """Get the x position of the physics body.

        Returns:
            float | None: The x position, or None if no physics body.
        """
        return self.physics_body.x

    @x.setter
    def x(self, value: float) -> None:
        """Set the x position of the physics body.

        Args:
            value (float): The x position to set.
        """
        self.physics_body.set_x(value)

    @property
    def y(self) -> float:
        """Get the y position of the physics body.

        Returns:
            float | None: The y position, or None if no physics body.
        """
        return self.physics_body.y

    @y.setter
    def y(self, value: float) -> None:
        """Set the y position of the physics body.

        Args:
            value (float): The y position to set.
        """
        self.physics_body.set_y(value)

    @property
    def height(self) -> float:
        """Get the height of the physics body.

        Returns:
            float | None: The height, or None if no physics body.
        """
        return self.physics_body.height

    @height.setter
    def height(self, value: float) -> None:
        """Set the height of the physics body.

        Args:
            value (float): The height to set.
        """
        self.physics_body.set_height(value)

    @property
    def width(self) -> float:
        """Get the width of the physics body.

        Returns:
            float | None: The width, or None if no physics body.
        """
        return self.physics_body.width

    @width.setter
    def width(self, value: float) -> None:
        """Set the width of the physics body.

        Args:
            value (float): The width to set.
        """
        self.physics_body.set_width(value)


class ISceneObjectFactory:
    """
    Factory for registering and creating scene object instances.

    Allows custom scene object types to be registered and instantiated
    from serialized data.
    """

    @classmethod
    @abstractmethod
    def create_scene_object(cls, data: dict) -> ISceneObject:
        """
        Create a scene_object instance from serialized data.

        Args:
            data: Dictionary containing scene_object data

        Returns:
            scene_object instance

        Raises:
            ValueError: If scene_object_type is not registered
        """
        ...


class IScene:
    """
    Scene Interface for managing scene objects within a scene.
    """

    def __repr__(self) -> str:
        return (
            f"Scene(name='{self.name}', "
            f"description='{self.description}', "
            f"scene_objects={len(self.scene_objects)}, "
            f"object_factory={self.get_scene_object_factory()})"
        )

    @property
    def name(self) -> str:
        """Get the name of the scene.

        Returns:
            str: The name of the scene.
        """
        return self.get_name()

    @name.setter
    def name(self, name: str) -> None:
        """Set the name of the scene.

        Args:
            name (str): The name of the scene.
        """
        self.set_name(name)

    @property
    def description(self) -> str:
        """Get the description of the scene.

        Returns:
            str: The description of the scene.
        """
        return self.get_description()

    @description.setter
    def description(self, description: str) -> None:
        """Set the description of the scene.

        Args:
            description (str): The description of the scene.
        """
        self.set_description(description)

    @property
    def scene_objects(self) -> Dict[str, ISceneObject]:
        """Get the scene objects in the scene.

        Returns:
            Dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
        """
        return self.get_scene_objects()

    @property
    def on_scene_object_added(self) -> list[Callable]:
        """
        Get the callback for when a scene_object is added.

        Returns:
            Callable or None: The callback function or None if not set.
        """
        return self.get_on_scene_object_added()

    @property
    def on_scene_object_removed(self) -> list[Callable]:
        """
        Get the callback for when a scene_object is removed.

        Returns:
            Callable or None: The callback function or None if not set.
        """
        return self.get_on_scene_object_removed()

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of the scene."""
        ...

    @abstractmethod
    def set_name(self, name: str) -> None:
        """Set the name of the scene.

        Args:
            name (str): The name of the scene.
        """
        ...

    @abstractmethod
    def get_description(self) -> str:
        """Get the description of the scene."""
        ...

    @abstractmethod
    def set_description(self, description: str) -> None:
        """Set the description of the scene.

        Args:
            description (str): The description of the scene.
        """
        ...

    @abstractmethod
    def get_scene_object(self, scene_object_id: str) -> Optional[ISceneObject]:
        """Get a scene_object by ID."""
        ...

    @abstractmethod
    def get_scene_objects(self) -> Dict[str, ISceneObject]:
        """Get all scene objects in the scene.

        Returns:
            Dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
        """
        ...

    @abstractmethod
    def set_scene_objects(
        self,
        scene_objects: Dict[str, ISceneObject]
    ) -> None:
        """Set the scene objects for the scene.

        Args:
            scene_objects (Dict[str, ISceneObject]): A dictionary of scene objects by their IDs.
        """
        ...

    @abstractmethod
    def get_scene_object_factory(self) -> Optional[ISceneObjectFactory]:
        """Get the object factory for loading scenes."""
        ...

    @abstractmethod
    def set_scene_object_factory(self, factory: ISceneObjectFactory) -> None:
        """Set the object factory for loading scenes.

        Args:
            factory: The scene object factory to set.
        """
        ...

    @abstractmethod
    def add_scene_object(self, scene_object: ISceneObject) -> None:
        """
        Add a scene_object to the scene.

        Args:
            scene_object: scene_object instance to add

        Raises:
            ValueError: If scene_object ID already exists
        """
        ...

    @abstractmethod
    def get_on_scene_object_added(self) -> list[Callable]:
        """
        Get the list of callbacks for when a scene_object is added.

        Returns:
            list[Callable]: The list of callback functions.
        """
        ...

    @abstractmethod
    def remove_scene_object(self, scene_object_id: str) -> None:
        """
        Remove a scene_object from the scene.

        Args:
            scene_object_id: ID of scene_object to remove
        """
        ...

    @abstractmethod
    def get_on_scene_object_removed(self) -> list[Callable]:
        """
        Get the list of callbacks for when a scene_object is removed.

        Returns:
            list[Callable]: The list of callback functions.
        """
        ...

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """
        Update all scene_objects in the scene.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert scene to dictionary for JSON serialization."""
        ...

    @classmethod
    @abstractmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "IScene":
        """
        Create scene from dictionary.

        Args:
            data: Dictionary containing scene data

        Returns:
            Scene instance
        """
        ...

    @abstractmethod
    def save(self, filepath: Union[str, Path]) -> None:
        """
        Save scene to JSON file.

        Args:
            filepath: Path to save the scene JSON file
        """
        ...

    @classmethod
    @abstractmethod
    def load(
        cls,
        filepath: Union[str, Path]
    ) -> "IScene":
        """
        Load scene from JSON file.

        Args:
            filepath: Path to the scene JSON file
        Returns:
            Scene instance
        """
        ...


class ISceneRunnerService(
    IRunnable,
    Protocol
):
    """ Service interface for running and managing scenes.
    """

    @abstractmethod
    def get_scene(self) -> IScene:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        ...

    @abstractmethod
    def set_scene(self, scene: IScene) -> None:
        """Set the scene to be managed.

        Args:
            scene (IScene): The scene instance to set.
        """
        ...

    @abstractmethod
    def load_scene(self, filepath: Union[str, Path]) -> None:
        """Load a scene from a file.

        Args:
            filepath (Union[str, Path]): The path to the scene file.
        """
        ...

    @abstractmethod
    def save_scene(self, filepath: Union[str, Path]) -> None:
        """Save the current scene to a file.

        Args:
            filepath (Union[str, Path]): The path to save the scene file.
        """
        ...

    @abstractmethod
    def get_physics_engine(self) -> Optional[object]:
        """Get the physics engine being used.

        Returns:
            The physics engine instance, or None if physics is disabled.
        """
        ...

    @abstractmethod
    def set_physics_engine(self, physics_engine) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance to set.
        """
        ...

    @abstractmethod
    def get_environment(self) -> Optional[object]:
        """Get the environment service being used.

        Returns:
            The environment service instance, or None if physics is disabled.
        """
        ...

    @abstractmethod
    def set_environment(self, environment: object) -> None:
        """Set the environment service to be used.

        Args:
            environment: The environment service instance to set.
        """
        ...

    @abstractmethod
    def set_update_rate(self, fps: float) -> None:
        """Set the update rate for the scene runner.

        Args:
            fps (float): The desired frames per second.
        """
        ...

    @abstractmethod
    def get_update_rate(self) -> float:
        """Get the current update rate for the scene runner.

        Returns:
            float: The current frames per second.
        """
        ...

    @abstractmethod
    def add_physics_body(self, body: Union[IBasePhysicsBody, IPhysicsBody2D]) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IBasePhysicsBody protocol
        """
        ...

    @abstractmethod
    def remove_physics_body(self, body: IBasePhysicsBody) -> None:
        """Remove a physics body from the simulation.

        Args:
            body: Object to remove
        """
        ...

    @abstractmethod
    def get_physics_stats(self) -> dict:
        """Get physics engine statistics.

        Returns:
            Dictionary with physics stats, or empty dict if physics disabled
        """
        ...

    def get_on_tick_callbacks(self) -> list[Callable]:
        """Get the list of on-tick callback functions.

        Returns:
            List of callback functions called on each tick
        """
        ...

    def get_on_scene_load_callbacks(self) -> list[Callable]:
        """Get the list of on-scene-load callback functions.

        Returns:
            List of callback functions called on scene load
        """
        ...

    @property
    def on_tick_callbacks(self) -> list[Callable]:
        """Get the list of on-tick callback functions.

        Returns:
            List of callback functions called on each tick
        """
        return self.get_on_tick_callbacks()

    @property
    def on_scene_load_callbacks(self) -> list[Callable]:
        """Get the list of on-scene-load callback functions.

        Returns:
            List of callback functions called on scene load
        """
        return self.get_on_scene_load_callbacks()

    @property
    def scene(self) -> IScene:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        return self.get_scene()

    @property
    def physics_engine(self) -> Optional[object]:
        """Get the physics engine being used.

        Returns:
            The physics engine instance, or None if physics is disabled.
        """
        return self.get_physics_engine()

    @property
    def environment(self) -> Optional[object]:
        """Get the environment service being used.

        Returns:
            The environment service instance, or None if physics is disabled.
        """
        return self.get_environment()


__all__ = ["IScene", "ISceneObject", "ISceneObjectFactory"]
