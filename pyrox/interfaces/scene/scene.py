"""
Scene management for field scene_object simulations.
"""
from abc import abstractmethod
from pathlib import Path
from typing import (
    Callable,
    Protocol,
    TypeVar,
)
from pyrox.interfaces import (
    IBasePhysicsBody,
    IPhysicsBody2D,
    IConnectionRegistry,
)
from pyrox.interfaces.scene.sceneobject import ISceneObject, ISceneObjectFactory
from pyrox.interfaces.scene.compositesceneobject import ICompositeSceneObject
from pyrox.interfaces.scene.scenegroup import ISceneGroup


T = TypeVar("T", bound=ISceneObject | ICompositeSceneObject | ISceneGroup)


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
    def scene_objects(self) -> dict[str, ISceneObject | ICompositeSceneObject | ISceneGroup]:
        """Get the scene objects in the scene.

        Returns:
            dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
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

    @property
    def on_scene_updated(self) -> list[Callable]:
        """
        Get the callback for when the scene is updated.

        Returns:
            Callable or None: The callback function or None if not set.
        """
        return self.get_on_scene_updated()

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
    def get_scene_object(self, scene_object_id: str) -> ISceneObject | ICompositeSceneObject | ISceneGroup | None:
        """Get a scene_object by ID."""
        ...

    @abstractmethod
    def get_scene_objects(self) -> dict[str, ISceneObject | ICompositeSceneObject | ISceneGroup]:
        """Get all scene objects in the scene.

        Returns:
            dict[str, ISceneObject]: A dictionary of scene objects by their IDs.
        """
        ...

    @abstractmethod
    def set_scene_objects(
        self,
        scene_objects: dict[str, T]
    ) -> None:
        """Set the scene objects for the scene.

        Args:
            scene_objects (dict[str, ISceneObject]): A dictionary of scene objects by their IDs.
        """
        ...

    @abstractmethod
    def get_scene_object_factory(self) -> ISceneObjectFactory | None:
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
    def add_scene_object(self, scene_object: ISceneObject | ICompositeSceneObject | ISceneGroup) -> None:
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
    def get_connection_registry(self) -> "IConnectionRegistry":
        """Get the connection registry for the scene.

        Returns:
            IConnectionRegistry: The connection registry instance.
        """
        ...

    @abstractmethod
    def set_connection_registry(
        self,
        registry: "IConnectionRegistry"
    ) -> None:
        """Set the connection registry for the scene.

        Args:
            registry (IConnectionRegistry): The connection registry instance.
        """
        ...

    @abstractmethod
    def get_on_scene_updated(self) -> list[Callable]:
        """
        Get the list of callbacks for when the scene is updated.

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
            data: dictionary containing scene data

        Returns:
            Scene instance
        """
        ...

    @abstractmethod
    def save(self, filepath: str | Path) -> None:
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
        filepath: str | Path
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
    Protocol
):
    """ Service interface for running and managing scenes.
    """

    @classmethod
    @abstractmethod
    def get_scene(cls) -> IScene | None:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        ...

    @classmethod
    @abstractmethod
    def set_scene(cls, scene: IScene | None) -> None:
        """Set the scene to be managed.

        Args:
            scene (IScene): The scene instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def load_scene(cls, filepath: str | Path) -> None:
        """Load a scene from a file.

        Args:
            filepath (Union[str, Path]): The path to the scene file.
        """
        ...

    @classmethod
    @abstractmethod
    def save_scene(cls, filepath: str | Path) -> None:
        """Save the current scene to a file.

        Args:
            filepath (Union[str, Path]): The path to save the scene file.
        """
        ...

    @classmethod
    @abstractmethod
    def get_physics_engine(cls) -> object | None:
        """Get the physics engine being used.

        Returns:
            The physics engine instance, or None if physics is disabled.
        """
        ...

    @classmethod
    @abstractmethod
    def set_physics_engine(cls, physics_engine) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def get_environment(cls) -> object | None:
        """Get the environment service being used.

        Returns:
            The environment service instance, or None if physics is disabled.
        """
        ...

    @classmethod
    @abstractmethod
    def set_environment(cls, environment: object) -> None:
        """Set the environment service to be used.

        Args:
            environment: The environment service instance to set.
        """
        ...

    @classmethod
    @abstractmethod
    def set_update_rate(cls, fps: float) -> None:
        """Set the update rate for the scene runner.

        Args:
            fps (float): The desired frames per second.
        """
        ...

    @classmethod
    @abstractmethod
    def get_update_rate(cls) -> float:
        """Get the current update rate for the scene runner.

        Returns:
            float: The current frames per second.
        """
        ...

    @classmethod
    @abstractmethod
    def add_physics_body(cls, body: IBasePhysicsBody | IPhysicsBody2D) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IBasePhysicsBody protocol
        """
        ...

    @classmethod
    @abstractmethod
    def remove_physics_body(cls, body: IBasePhysicsBody) -> None:
        """Remove a physics body from the simulation.

        Args:
            body: Object to remove
        """
        ...

    @classmethod
    @abstractmethod
    def get_physics_stats(cls) -> dict:
        """Get physics engine statistics.

        Returns:
            dictionary with physics stats, or empty dict if physics disabled
        """
        ...


__all__ = ["IScene"]
