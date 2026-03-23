""" Scene Object.
"""
from abc import abstractmethod
from typing import (
    Any,
)
from pyrox.interfaces import (
    IBasePhysicsBody,
    ICoreMixin,
    Connection,
)


class ISceneObject(
        ICoreMixin,
):
    """Object base class for scene elements.
    """

    # ------------------------------------------------------------------
    # Properties and serialization
    # ------------------------------------------------------------------

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

    def get_properties(self) -> dict:
        """Get the properties of the scene object.

        Returns:
            dict: The properties of the scene object.
        """
        return self._properties

    def set_properties(self, properties: dict) -> None:
        """Set the properties of the scene object.

        Args:
            properties (dict): The properties of the scene object.
        """
        if not isinstance(properties, dict):
            raise ValueError("Properties must be a dictionary.")
        self._properties = properties

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

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> "ISceneObject":
        """Create scene object from dictionary."""
        ...

    # ------------------------------------------------------------------
    # Scene object type and template name
    # ------------------------------------------------------------------

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

    def get_template_name(self) -> str:
        """Get the template name of the scene object, if any.

        Returns:
            str: The template name of the scene object.
        """
        return self._template_name

    def set_template_name(self, template_name: str) -> None:
        """Set the template name of the scene object.

        Args:
            template_name (str): The template name to set for the scene object.
        """
        self._template_name = template_name

    @property
    def template_name(self) -> str:
        """Get the template name of the scene object, if any.

        Returns:
            str: The template name of the scene object.
        """
        return self.get_template_name()

    @template_name.setter
    def template_name(self, template_name: str) -> None:
        """Set the template name of the scene object.

        Args:
            template_name (str): The template name to set for the scene object.
        """
        self.set_template_name(template_name)

    # ------------------------------------------------------------------
    # Physics body
    # ------------------------------------------------------------------

    def get_physics_body(self) -> IBasePhysicsBody:
        """Get the physics body associated with this scene object.

        Returns:
            Optional[BasePhysicsBody]: The physics body, or None if not set.
        """
        return self._physics_body

    def set_physics_body(
        self,
        physics_body: IBasePhysicsBody
    ) -> None:
        """Set the physics body associated with this scene object.

        Args:
            physics_body (Optional[BasePhysicsBody]): The physics body to set, or None.
        """
        self._physics_body = physics_body

    @property
    def physics_body(self) -> IBasePhysicsBody:
        """Get the physics body associated with this scene object.

        Returns:
            Optional[BasePhysicsBody]: The physics body, or None if not set.
        """
        return self.get_physics_body()

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    @property
    def connections(self) -> list[Connection]:
        return self._connections

    def get_connections(self) -> list[Connection]:
        return self._connections

    def set_connections(self, connections: list[Connection]) -> None:
        self._connections = list(connections)

    def get_inputs(self) -> dict[str, Any]:
        """Delegate to the physics body's input endpoints."""
        return self._physics_body.get_inputs()

    def get_outputs(self) -> dict[str, Any]:
        """Delegate to the physics body's output endpoints."""
        return self._physics_body.get_outputs()

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

    @property
    def tags(self) -> list[str]:
        """Tags used for gameplay / logic categorisation."""
        return self._tags

    def get_tags(self) -> list[str]:
        return self._tags

    def set_tags(self, tags: list[str]) -> None:
        self._tags = list(tags)

    def has_tag(self, tag: str) -> bool:
        return tag in self._tags

    def add_tag(self, tag: str) -> None:
        if tag not in self._tags:
            self._tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        if tag in self._tags:
            self._tags.remove(tag)

    # ------------------------------------------------------------------
    # Parent-child relationships
    # ------------------------------------------------------------------

    def get_parent(self) -> 'ISceneObject | None':
        """Get the parent scene object."""
        return self._parent

    def set_parent(self, parent: 'ISceneObject | None') -> None:
        """Set the parent scene object.

        Args:
            parent: The parent scene object, or None to remove parent
        """
        # Remove from old parent's children
        if self._parent and self.id in self._parent.children:
            del self._parent.children[self.id]

        self._parent = parent

        # Add to new parent's children
        if parent:
            parent.children[self.id] = self

    @property
    def parent(self) -> 'ISceneObject | None':
        """Get the parent scene object."""
        return self.get_parent()

    @parent.setter
    def parent(self, parent: 'ISceneObject | None') -> None:
        """Set the parent scene object.

        Args:
            parent: The parent scene object, or None to remove parent
        """
        self.set_parent(parent)

    def add_child(self, child: 'ISceneObject') -> None:
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
        if child_id in self.children:
            self.children[child_id].set_parent(None)

    def get_children(self) -> dict[str, 'ISceneObject']:
        """Get all child scene objects.

        Returns:
            Dictionary of child scene objects by ID
        """
        return self._children

    def set_children(self, children: dict[str, 'ISceneObject']) -> None:
        """Set the child scene objects.

        Args:
            children: Dictionary of child scene objects by ID
        """
        # Clear existing children
        for child in self._children.values():
            child.set_parent(None)

        self._children = children

        # Set parent for new children
        for child in self._children.values():
            child.set_parent(self)

    def get_child(self, child_id: str) -> 'ISceneObject | None':
        """Get a specific child by ID.

        Args:
            child_id: The ID of the child to retrieve

        Returns:
            The child scene object, or None if not found
        """
        return self.children.get(child_id)

    @property
    def children(self) -> dict[str, 'ISceneObject']:
        """Get all child scene objects.

        Returns:
            Dictionary of child scene objects by ID
        """
        return self.get_children()

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
