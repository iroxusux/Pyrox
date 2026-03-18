""" Scene management for field scene_object simulations.
"""
from typing import (
    Any,
    Callable,
)
import uuid
from pyrox.interfaces import (
    IBasePhysicsBody,
    ISceneObject,
    Connection,
)
from pyrox.models.protocols import CoreMixin
from pyrox.models.physics.factory import PhysicsSceneFactory
from pyrox.models.scene.animation import SceneAnimator


class SceneObject(
        ISceneObject,
        CoreMixin
):
    """Base class for scene objects.
    """

    def __init__(
        self,
        name: str,
        scene_object_type: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        template_name: str = "",
        id: str | None = None,
        group_id: str | None = None,
        properties: dict | None = None,
        parent: 'SceneObject | None' = None,
        layer: int = 0,
        sprite_path: str | None = None,
        bg_color: str = "#4a9eff",
        tags: list[str] | None = None,
    ):
        CoreMixin.__init__(self, name=name, description=description, id=id or f'scene_object_{uuid.uuid4()}')
        self._scene_object_type = scene_object_type
        self._template_name: str = template_name
        self._properties: dict[str, Any] = properties if properties is not None else dict()
        self._physics_body = physics_body
        self._group_id: str | None = group_id

        # Parent-child hierarchy
        self._parent: 'SceneObject | None' = parent
        self._children: dict[str, 'SceneObject'] = {}

        # Rendering layer (z-order)
        # Lower values render first (background), higher values render last (foreground)
        # Common layers: -100 (floor), 0 (default), 50 (conveyors), 100 (objects), 200 (UI)
        self._layer: int = layer

        # Visual properties
        # sprite_path / bg_color can also be supplied via the properties dict
        # (e.g. when loading from JSON).  The explicit constructor args take
        # priority; if absent, fall back to whatever the properties dict says.
        _props = properties or {}
        self._sprite_path: str | None = sprite_path if sprite_path is not None else _props.get("sprite_path")
        self._bg_color: str = bg_color if bg_color != "#4a9eff" else _props.get("bg_color", _props.get("color", "#4a9eff"))

        # Animation
        self._animator: SceneAnimator = SceneAnimator()

        # Event handlers for interactive elements
        self._on_click_handlers: list[Callable] = []
        self._on_hover_handlers: list[Callable] = []
        self._clickable: bool = False  # Whether this object responds to clicks

        # Tags for gameplay / logic categorisation
        self._tags: list[str] = list(tags) if tags else []

        # Connection records (managed by Scene / ConnectionRegistry)
        self._connections: list[Connection] = []
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
    # Visual properties
    # ------------------------------------------------------------------

    @property
    def sprite_path(self) -> str | None:
        """Filesystem path to a sprite image, or ``None`` to use a plain colour fill."""
        return self._sprite_path

    @sprite_path.setter
    def sprite_path(self, path: str | None) -> None:
        self._sprite_path = path

    @property
    def bg_color(self) -> str:
        """Background / fill colour used when no sprite is set (CSS hex string)."""
        return self._bg_color

    @bg_color.setter
    def bg_color(self, color: str) -> None:
        self._bg_color = color

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------

    @property
    def animator(self) -> SceneAnimator:
        """The :class:`~pyrox.models.scene.animation.SceneAnimator` for this object."""
        return self._animator

    # ------------------------------------------------------------------
    # Properties and serialization
    # ------------------------------------------------------------------

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

    def get_properties(self) -> dict:
        """Get the properties of the scene object.

        Returns:
            Dict: The properties of the scene object.
        """
        self._compile_properties()
        return self._properties

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
        if hasattr(self.physics_body, name):
            setattr(self.physics_body, name, value)
        elif hasattr(self, name):
            setattr(self, name, value)
        else:
            self._properties[name] = value

    def set_properties(self, properties: dict) -> None:
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

    def get_template_name(self) -> str:
        """Get the SceneObjectFactory template name for this object."""
        return self._template_name

    def set_template_name(self, template_name: str) -> None:
        """Set the SceneObjectFactory template name for this object."""
        self._template_name = template_name

    @property
    def template_name(self) -> str:
        """SceneObjectFactory template name used to reconstruct this object."""
        return self._template_name

    def to_dict(self) -> dict:
        """Convert scene object to dictionary for JSON serialization."""
        # Use physics body's to_dict if available, otherwise construct manually
        body = self.physics_body.to_dict()

        return {
            "name": self.name,
            "scene_object_type": self._scene_object_type,
            "template_name": self._template_name,
            "id": self.id,
            "group_id": self._group_id,
            "description": self._description,
            "tags": self._tags,
            "properties": self.properties,
            "layer": self._layer,
            "body": body,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ISceneObject:
        """Create scene object from dictionary.

        When called on the base :class:`SceneObject` class and a
        ``template_name`` is present in *data*, dispatches to the registered
        subclass via :class:`~pyrox.models.scene.factory.SceneObjectFactory`.
        Falls back to constructing a plain :class:`SceneObject` when no
        matching template is found (backward-compatible with generic objects).
        """
        # Dispatch via SceneObjectFactory — only when called on the base class
        # to avoid infinite recursion when a subclass inherits this method.
        if cls is SceneObject:
            # Local import avoids a circular dependency between sceneobject and factory.
            from pyrox.models.scene.factory import SceneObjectFactory  # noqa: PLC0415
            # Primary key: template_name.  Fallback: scene_object_type for files
            # saved before the template_name field was populated (backward compat).
            template_name: str = (
                data.get("template_name", "")
                or data.get("scene_object_type", "")
            )
            if template_name:
                template = SceneObjectFactory.get_template(template_name)
                if template is not None and template.scene_object_class is not SceneObject:
                    return template.scene_object_class.from_dict(data)

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
            template_name=data.get("template_name", ""),
            id=data.get("id", None),
            group_id=data.get("group_id", None),
            physics_body=body,
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            layer=data.get("layer", 0),
            tags=data.get("tags", []),
        )
        # Restore visual properties explicitly so they survive _compile_properties
        props = data.get("properties", {})
        obj._sprite_path = props.get("sprite_path")
        obj._bg_color = props.get("bg_color", props.get("color", "#4a9eff"))
        return obj

    def update(self, dt: float) -> None:
        """Tick the object — advances any active animation.

        Args:
            dt: Elapsed time in seconds since the last call.
        """
        self._animator.update(dt, self)

    def get_physics_body(self) -> IBasePhysicsBody:
        return self._physics_body

    def set_physics_body(self, physics_body: IBasePhysicsBody) -> None:
        self._physics_body = physics_body

    # Parent-child relationship methods

    def get_parent(self) -> 'SceneObject | None':
        """Get the parent scene object."""
        return self._parent

    def set_parent(self, parent: 'SceneObject | None') -> None:
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

    def get_children(self) -> dict[str, 'SceneObject']:
        """Get all child scene objects.

        Returns:
            Dictionary of child scene objects by ID
        """
        return self._children

    def get_child(self, child_id: str) -> 'SceneObject | None':
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

    def get_group_id(self) -> str | None:
        """Get the ID of the SceneGroup this object belongs to, or None."""
        return self._group_id

    def set_group_id(self, group_id: str | None) -> None:
        """Set the group ID for this object.

        Args:
            group_id: The owning SceneGroup's scene object ID, or None.
        """
        self._group_id = group_id

    def _compile_properties(self) -> None:
        """Build the serialisation snapshot from live attributes.

        ``self._properties`` is a *lazy snapshot*: it is only populated here
        (and in the ``else`` branch of :meth:`set_property` for custom
        properties that have no corresponding live attribute).  Consumer code
        should always obtain properties through :meth:`get_properties`, which
        calls this method before returning the dict.

        **Subclass contract**: overrides MUST call
        ``super()._compile_properties()`` before adding their own keys so that
        all base-class fields are present in the snapshot.  See
        :class:`~pyrox.models.scene.assets.topdown.piston.PistonSceneObject`
        for a reference implementation.
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

        # Visual properties
        self._properties.update({
            "sprite_path": self._sprite_path,
            "bg_color": self._bg_color,
            "color": self._bg_color,  # backward-compat alias
        })

        # Physics body properties
        self._properties.update(self.physics_body.get_properties())
