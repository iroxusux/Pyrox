"""
Scene management for field scene_object simulations.
"""
from abc import abstractmethod
from typing import (
    Protocol,
    runtime_checkable,
)
from pyrox.interfaces import (
    INameable,
    IConnectable,
    IDescribable,
    IBasePhysicsBody,
)


@runtime_checkable
class ISceneObject(
        IConnectable,
        INameable,
        IDescribable,
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

    # ---------- Layer methods ----------

    @abstractmethod
    def get_layer(self) -> int:
        """Get the layer of the scene object.

        Returns:
            int: The layer of the scene object.
        """
        ...

    @abstractmethod
    def set_layer(self, layer: int) -> None:
        """Set the layer of the scene object.

        Args:
            layer (int): The layer to set for the scene object.
        """
        ...

    @abstractmethod
    def move_layer_up(self) -> None:
        """Move the scene object up one layer."""
        ...

    @abstractmethod
    def move_layer_down(self) -> None:
        """Move the scene object down one layer."""
        ...

    @abstractmethod
    def bring_to_front(self) -> None:
        """Bring the scene object to the front layer."""
        ...

    @abstractmethod
    def send_to_back(self) -> None:
        """Send the scene object to the back layer."""
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

    # ---------- Group Methods ----------

    @abstractmethod
    def get_group_id(self) -> str | None:
        """Get the group this scene object belongs to, if any.

        Returns:
            str | None: The ID of the group, or None if not in a group.
        """
        ...

    @abstractmethod
    def set_group_id(self, group_id: str | None) -> None:
        """Set the group this scene object belongs to.

        Args:
            group_id (str | None): The ID of the group to set, or None to ungroup.
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


__all__ = ["ISceneObject", "ISceneObjectFactory"]
