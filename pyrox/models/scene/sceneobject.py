""" Scene management for field scene_object simulations.
"""
from typing import (
    Any,
    Callable,
)
import uuid
from pyrox.interfaces import (
    CardinalDirection,
    IBasePhysicsBody,
    ISceneObject,
    Connection,
)
from pyrox.models.protocols import CoreMixin
from pyrox.models.physics.factory import PhysicsSceneFactory
from pyrox.models.scene.animation import SceneAnimator


class SceneObject(
        ISceneObject,
        CoreMixin,
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
        parent_offset_x: float = 0.0,
        parent_offset_y: float = 0.0,
        layer: int = 0,
        direction: CardinalDirection | None = None,
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

        if direction:
            self._direction = CardinalDirection.try_parse(direction)
        elif properties:
            self._direction = CardinalDirection.try_parse(properties.get("direction", 'NORTH'))
        else:
            self._direction = CardinalDirection.NORTH  # Default direction

        # Parent-child hierarchy
        self._parent: 'ISceneObject | None' = parent
        self._parent_offset_x = parent_offset_x
        self._parent_offset_y = parent_offset_y

        self._children: dict[str, 'ISceneObject'] = {}

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

    def compile_properties(self) -> None:
        """Public method to trigger properties compilation.

        This is called by consumer code before serializing or accessing the
        properties dict to ensure that the snapshot is up to date with the
        current state of the object.
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
            "parent_offset_x": self._parent_offset_x,
            "parent_offset_y": self._parent_offset_y,
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
            parent_offset_x=data.get("parent_offset_x", 0.0),
            parent_offset_y=data.get("parent_offset_y", 0.0),
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
