""" Scene management for field scene_object simulations.
"""
from typing import (
    Any,
    Callable,
    Dict,
    Optional,
)
from pyrox.interfaces import (
    Connection,
    IBasePhysicsBody,
    INameable,
    IDescribable,
    ISceneObject,
)
from pyrox.models.physics.factory import PhysicsSceneFactory


class SceneObject(
        ISceneObject,
        INameable,
        IDescribable,
):
    """Base class for scene objects.
    """

    def __getattribute__(self, name: str) -> Any:
        # Override to allow dynamic properties from physics body
        try:
            return super().__getattribute__(name)
        except AttributeError:
            physics_body = super().__getattribute__("_physics_body")
            if hasattr(physics_body, name):
                return getattr(physics_body, name)
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __init__(
        self,
        name: str,
        scene_object_type: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        properties: Optional[Dict] = None,
        parent: Optional['SceneObject'] = None,
        layer: int = 0,
    ):
        self._description = description
        self._scene_object_type = scene_object_type
        self._properties: Dict[str, Any] = properties if properties is not None else dict()
        self._physics_body = physics_body

        if name:
            self._physics_body.name = name

        # Parent-child hierarchy
        self._parent: Optional['SceneObject'] = parent
        self._children: Dict[str, 'SceneObject'] = {}

        # Rendering layer (z-order)
        # Lower values render first (background), higher values render last (foreground)
        # Common layers: -100 (floor), 0 (default), 50 (conveyors), 100 (objects), 200 (UI)
        self._layer: int = layer

        # Event handlers for interactive elements
        self._on_click_handlers: list[Callable] = []
        self._on_hover_handlers: list[Callable] = []
        self._clickable: bool = False  # Whether this object responds to clicks

        # Group membership — ID of the SceneGroup this object belongs to, or None
        self._group_id: Optional[str] = None

    # INamable methods
    def get_name(self) -> str:
        return self._physics_body.name

    def set_name(self, name: str) -> None:
        self._physics_body.name = name

    # IDescribable methods
    def get_description(self) -> str:
        return self._description

    def set_description(self, description: str) -> None:
        self._description = description

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
        # We have to check physics body first to avoid setting a new property on the scene object when it actually belongs to the physics body
        if hasattr(self.physics_body, name):
            setattr(self.physics_body, name, value)
        elif hasattr(self, name):
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
        # Use physics body's to_dict if available, otherwise construct manually
        body = self.physics_body.to_dict()

        return {
            "name": self.name,
            "scene_object_type": self._scene_object_type,
            "id": self.id,
            "description": self._description,
            "properties": self.properties,
            "layer": self._layer,
            "group_id": self._group_id,
            "body": body,
            "material": body.get("material", {}) if isinstance(body, dict) else {},
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
            properties=data.get("properties", {}),
            layer=data.get("layer", 0)
        )
        obj._group_id = data.get("group_id", None)
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

    # Layer/z-order methods

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

    # ------------------------------------------------------------------
    # IGroupable — group membership
    # ------------------------------------------------------------------

    def get_group_id(self) -> Optional[str]:
        """Get the ID of the SceneGroup this object belongs to, or None."""
        return self._group_id

    def set_group_id(self, group_id: Optional[str]) -> None:
        """Set the group ID for this object.

        Args:
            group_id: The owning SceneGroup's scene object ID, or None.
        """
        self._group_id = group_id

    def _compile_properties(self) -> None:
        """Compile properties for physics simulation."""

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
