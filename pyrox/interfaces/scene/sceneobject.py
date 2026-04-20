""" Scene Object.
"""
from abc import abstractmethod
from typing import (
    Any,
)
from pyrox.interfaces import (
    CardinalDirection,
    IDirectional2D,
    IBasePhysicsBody,
    ICoreMixin,
    Connection,
)


class ISceneObject(
        ICoreMixin,
        IDirectional2D,
):
    """Object base class for scene elements.
    """
    _properties: dict
    _scene_object_type: str
    _template_name: str
    _physics_body: IBasePhysicsBody
    _connections: list[Connection]
    _tags: list[str]
    _parent: 'ISceneObject | None'
    _parent_offset_x: float
    _parent_offset_y: float
    _children: dict[str, 'ISceneObject']
    _layer: int
    _sublayer: int
    _group_id: str | None

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update the scene object.

        Args:
            delta_time: Time elapsed since last update in seconds
        """
        ...

    # ------------------------------------------------------------------
    # Properties and serialization
    # ------------------------------------------------------------------

    def compile_properties(self) -> None:
        """Compile the properties of the scene object.

        This method gathers properties from the physics body and any other
        relevant sources to create a complete snapshot of the scene object's
        state for serialization. It should be called before accessing or
        serializing the properties to ensure they are up to date.
        """
        # Scene object properties
        self._properties.update({
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scene_object_type": self._scene_object_type,
            "layer": self._layer,
            "group_id": self._group_id,
        })

        # Physics body properties
        self._properties.update(self.physics_body.get_properties())

    def get_property(self, name: str) -> object:
        """Get a property by name.

        Args:
            name (str): The name of the property.

        Returns:
            object: The value of the property.
        """
        self.compile_properties()
        return self.get_properties().get(name)

    def set_property(self, name: str, value: Any) -> None:
        """Set a single property of the scene object.

        For properties that correspond to a live attribute on the physics body
        or on this object, only the live attribute is updated; the serialisation
        snapshot (``self._properties``) will reflect the change the next time
        :meth:`get_properties` is called.

        For truly custom properties that have no live attribute, the value is
        stored directly in ``self._properties`` so that it survives
        serialisation.

        Args:
            name (str): The property key.
            value (Any): The property value.
        """
        if hasattr(self, name):
            setattr(self, name, value)
        else:
            raise AttributeError(f"SceneObject has no attribute '{name}' to set. Use get_properties/set_properties for custom properties.")

    def get_properties(self) -> dict:
        """Get the properties of the scene object.

        Returns:
            dict: The properties of the scene object.
        """
        self.compile_properties()
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

    @property
    def connections(self) -> list[Connection]:
        return self.get_connections()

    # ------------------------------------------------------------------
    # Tags
    # ------------------------------------------------------------------

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

    @property
    def tags(self) -> list[str]:
        """Tags used for gameplay / logic categorisation."""
        return self.get_tags()

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

    def get_parent_offset(self) -> tuple[float, float]:
        """Get the offset from the parent scene object, if any."""
        return (self._parent_offset_x, self._parent_offset_y)

    def set_parent_offset(self, offset_x: float, offset_y: float) -> None:
        """Set the offset from the parent scene object.

        Args:
            offset_x: The x offset from the parent
            offset_y: The y offset from the parent
        """
        if not self._parent:
            raise ValueError("Cannot set parent offset when there is no parent.")
        self._parent_offset_x = offset_x
        self._parent_offset_y = offset_y

    @property
    def parent_offset(self) -> tuple[float, float]:
        """Get the offset from the parent scene object, if any."""
        return self.get_parent_offset()

    @parent_offset.setter
    def parent_offset(self, offset: tuple[float, float]) -> None:
        """Set the offset from the parent scene object.

        Args:
            offset: Tuple of (offset_x, offset_y) from the parent
        """
        self.set_parent_offset(offset[0], offset[1])

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

    # ------------------------------------------------------------------
    # Layering and rendering order
    # ------------------------------------------------------------------

    def get_layer(self) -> int:
        """Get the rendering layer (z-order) of this object.

        Returns:
            Layer number. Lower values render first (background),
            higher values render last (foreground).
        """
        return self._layer

    def set_layer(self, layer: int) -> None:
        """Set the rendering layer (z-order) of this object.

        Args:
            layer: Layer number. Common values:
                   -100: Floor/background
                   0: Default
                   50: Conveyors/platforms
                   100: Objects/items
                   200: Foreground/UI elements
        """
        self._layer = layer

    def move_layer_up(self) -> None:
        """Move this object one layer up (toward foreground)."""
        self._layer += 1

    def move_layer_down(self) -> None:
        """Move this object one layer down (toward background)."""
        self._layer -= 1

    def bring_to_front(self) -> None:
        """Bring this object to the front (highest layer)."""
        # Scene will need to determine max layer if we want to be relative
        # For now, use a large value
        self._layer = 1000

    def send_to_back(self) -> None:
        """Send this object to the back (lowest layer)."""
        # Use a very low value for back
        self._layer = -1000

    def get_sublayer(self) -> int:
        """Get the sublayer for finer control within the same layer."""
        return self._sublayer

    def set_sublayer(self, sublayer: int) -> None:
        """Set the sublayer for finer control within the same layer."""
        self._sublayer = sublayer

    @property
    def layer(self) -> int:
        """Get the rendering layer (z-order) of this object."""
        return self.get_layer()

    @layer.setter
    def layer(self, layer: int) -> None:
        """Set the rendering layer (z-order) of this object."""
        self.set_layer(layer)

    @property
    def sublayer(self) -> int:
        """Get the sublayer for finer control within the same layer."""
        return self.get_sublayer()

    @sublayer.setter
    def sublayer(self, sublayer: int) -> None:
        """Set the sublayer for finer control within the same layer."""
        self.set_sublayer(sublayer)

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def get_group_id(self) -> str | None:
        """Get the ID of the SceneGroup this object belongs to, or None."""
        return self._group_id

    def set_group_id(self, group_id: str | None) -> None:
        """Set the group ID for this object.

        Args:
            group_id: The owning SceneGroup's scene object ID, or None.
        """
        self._group_id = group_id

    @property
    def group_id(self) -> str | None:
        """Get the ID of the SceneGroup this object belongs to, or None."""
        return self.get_group_id()

    @group_id.setter
    def group_id(self, group_id: str | None) -> None:
        """Set the group ID for this object.

        Args:
            group_id: The owning SceneGroup's scene object ID, or None.
        """
        self.set_group_id(group_id)

    # ---------- Physics body convenience methods ----------

    def get_x(self) -> float:
        """Get the x position of the physics body.

        Returns:
            float | None: The x position, or None if no physics body.
        """
        return self.physics_body.x

    def set_x(self, x: float) -> None:
        """Set the x position of the physics body.

        Args:
            value (float): The x position to set.
        """
        self.physics_body.set_x(x)

    @property
    def x(self) -> float:
        """Get the x position of the physics body.

        Returns:
            float | None: The x position, or None if no physics body.
        """
        return self.get_x()

    @x.setter
    def x(self, value: float) -> None:
        """Set the x position of the physics body.

        Args:
            value (float): The x position to set.
        """
        self.set_x(value)

    def get_y(self) -> float:
        """Get the y position of the physics body.

        Returns:
            float | None: The y position, or None if no physics body.
        """
        return self.physics_body.y

    def set_y(self, y: float) -> None:
        """Set the y position of the physics body.

        Args:
            value (float): The y position to set.
        """
        self.physics_body.set_y(y)

    @property
    def y(self) -> float:
        """Get the y position of the physics body.

        Returns:
            float | None: The y position, or None if no physics body.
        """
        return self.get_y()

    @y.setter
    def y(self, value: float) -> None:
        """Set the y position of the physics body.

        Args:
            value (float): The y position to set.
        """
        self.set_y(value)

    def get_height(self) -> float:
        """Get the height of the physics body.

        Returns:
            float | None: The height, or None if no physics body.
        """
        return self.physics_body.height

    def set_height(self, height: float) -> None:
        """Set the height of the physics body.

        Args:
            value (float): The height to set.
        """
        self.physics_body.set_height(height)

    @property
    def height(self) -> float:
        """Get the height of the physics body.

        Returns:
            float | None: The height, or None if no physics body.
        """
        return self.get_height()

    @height.setter
    def height(self, value: float) -> None:
        """Set the height of the physics body.

        Args:
            value (float): The height to set.
        """
        return self.set_height(value)

    def get_width(self) -> float:
        """Get the width of the physics body.

        Returns:
            float | None: The width, or None if no physics body.
        """
        return self.physics_body.width

    def set_width(self, width: float) -> None:
        """Set the width of the physics body.

        Args:
            value (float): The width to set.
        """
        self.physics_body.set_width(width)

    @property
    def width(self) -> float:
        """Get the width of the physics body.

        Returns:
            float | None: The width, or None if no physics body.
        """
        return self.get_width()

    @width.setter
    def width(self, value: float) -> None:
        """Set the width of the physics body.

        Args:
            value (float): The width to set.
        """
        self.set_width(value)

    def get_yaw(self) -> float:
        """Get the yaw (rotation) of the physics body.

        Returns:
            float | None: The yaw, or None if no physics body.
        """
        return self.physics_body.yaw

    def set_yaw(self, yaw: float) -> None:
        """Set the yaw (rotation) of the physics body.

        Args:
            value (float): The yaw to set.
        """
        self.physics_body.set_yaw(yaw)

    @property
    def yaw(self) -> float:
        """Get the yaw (rotation) of the physics body.

        Returns:
            float | None: The yaw, or None if no physics body.
        """
        return self.get_yaw()

    @yaw.setter
    def yaw(self, value: float) -> None:
        """Set the yaw (rotation) of the physics body.

        Args:
            value (float): The yaw to set.
        """
        self.set_yaw(value)

    def get_direction(self) -> CardinalDirection:
        """Get the cardinal direction of the physics body.

        Returns:
            CardinalDirection | None: The direction, or None if no physics body.
        """
        return self.physics_body.direction

    def set_direction(self, direction: CardinalDirection | int | str | None) -> None:
        """Set the cardinal direction of the physics body.

        Args:
            direction (CardinalDirection): The direction to set.
        """
        self.physics_body.set_direction(direction)


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
