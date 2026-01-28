"""
Scene management for field scene_object simulations.
"""
from abc import abstractmethod
from pathlib import Path
from typing import Dict, Optional, Type, Union
from pyrox.interfaces import ISpatial2D


class ISceneObject(ISpatial2D):
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

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "ISceneObject":
        """Create scene object from dictionary."""
        ...

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        ...


class ISceneObjectFactory:
    """
    Factory for registering and creating scene object instances.

    Allows custom scene object types to be registered and instantiated
    from serialized data.
    """

    @abstractmethod
    def register(
        self,
        scene_object_type: str,
        scene_object_class: Type[ISceneObject]
    ) -> None:
        """
        Register a scene_object type.

        Args:
            scene_object_type: String identifier for the scene_object type
            scene_object_class: scene_object class to register

        Raises:
            ValueError: If scene_object_type is already registered
        """
        ...

    @abstractmethod
    def unregister(
        self,
        scene_object_type: str
    ) -> None:
        """
        Unregister a scene_object type.

        Args:
            scene_object_type: String identifier for the scene_object type
        """
        ...

    @abstractmethod
    def get_registered_types(self) -> list[str]:
        """Get list of all registered scene object types."""
        ...

    @abstractmethod
    def create_scene_object(self, data: dict) -> ISceneObject:
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
    def remove_scene_object(self, scene_object_id: str) -> None:
        """
        Remove a scene_object from the scene.

        Args:
            scene_object_id: ID of scene_object to remove
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
        factory: ISceneObjectFactory
    ) -> "IScene":
        """
        Create scene from dictionary.

        Args:
            data: Dictionary containing scene data
            factory: Scene object factory for creating scene objects

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
        filepath: Union[str, Path],
        factory: ISceneObjectFactory
    ) -> "IScene":
        """
        Load scene from JSON file.

        Args:
            filepath: Path to the scene JSON file
            factory: Scene object factory for creating scene objects
        Returns:
            Scene instance
        """
        ...


__all__ = ["IScene", "ISceneObject", "ISceneObjectFactory"]
