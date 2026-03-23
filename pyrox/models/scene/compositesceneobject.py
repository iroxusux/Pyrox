"""
CompositeSceneObject: design-locked composite scene object (Type 2 grouping).

The composite is the only object registered in the scene.  Its child
components are owned slots, positioned with relative offsets from the
composite's origin.  Components are not individually selectable by the user —
events are dispatched by the composite to the appropriate child.

Example::

    panel = CompositeSceneObject(name="Control Panel", physics_body=body)
    panel.add_component("e_stop",   estop_obj,   offset_x=10,  offset_y=20)
    panel.add_component("run_btn",  run_btn_obj, offset_x=10,  offset_y=60)
    scene.add_scene_object(panel)
"""

from typing import (
    Dict,
    List,
    Optional,
    Tuple,
)
import uuid

from pyrox.interfaces import (
    IBasePhysicsBody,
    ISceneObject,
)
from pyrox.interfaces.scene.compositesceneobject import ICompositeSceneObject
from pyrox.models.scene.sceneobject import SceneObject

SCENE_OBJECT_TYPE_COMPOSITE = "composite"


class CompositeSceneObject(SceneObject, ICompositeSceneObject):
    """Design-locked composite that owns child components at relative offsets.

    The composite is the sole entry in ``scene._scene_objects``.  Children are
    stored in ``_components`` as ``(obj, offset_x, offset_y)`` tuples.

    World position of a component:
        ``world_x = composite.x + offset_x``
        ``world_y = composite.y + offset_y``

    Events (clicks, updates) are routed through the composite to components.
    """

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        scene_object_type: str = SCENE_OBJECT_TYPE_COMPOSITE,
        template_name: str = SCENE_OBJECT_TYPE_COMPOSITE,
        id: str | None = None,
        group_id: str | None = None,
        properties: Optional[Dict] = None,
        parent: Optional[SceneObject] = None,
        layer: int = 0,
        tags: list[str] | None = None,
        components: list[dict] | dict | None = None,
    ):
        super().__init__(
            name=name,
            scene_object_type=scene_object_type,
            template_name=template_name,
            physics_body=physics_body,
            description=description,
            id=id or f'{SCENE_OBJECT_TYPE_COMPOSITE}_{uuid.uuid4()}',
            group_id=group_id,
            properties=properties,
            parent=parent,
            layer=layer,
            tags=tags,
        )

        if isinstance(components, list):
            # Convert list of dicts to internal dict format
            self._components = {}
            for comp in components:
                name = comp["name"]
                offset_x = comp.get("offset_x", 0.0)
                offset_y = comp.get("offset_y", 0.0)
                obj_data = comp["object"]
                obj = SceneObject.from_dict(obj_data)
                self._components[name] = (obj, offset_x, offset_y)

        elif isinstance(components, dict):
            # Assume already in internal dict format
            self._components = components
        else:
            self._components = {}

    # ------------------------------------------------------------------
    # ICompositeSceneObject — component management
    # ------------------------------------------------------------------

    def add_component(
        self,
        name: str,
        obj: ISceneObject,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        """Register a child component at a relative offset."""
        if name in self._components:
            raise ValueError(
                f"A component named '{name}' already exists in '{self.name}'."
            )
        self._components[name] = (obj, offset_x, offset_y)

    def remove_component(self, name: str) -> None:
        """Remove a component by logical name."""
        if name in self._components:
            del self._components[name]

    def get_component(self, name: str) -> Optional[ISceneObject]:
        entry = self._components.get(name)
        return entry[0] if entry else None

    def get_components(self) -> Dict[str, Tuple[ISceneObject, float, float]]:
        return dict(self._components)

    def get_component_names(self) -> List[str]:
        return list(self._components.keys())

    def has_component(self, name: str) -> bool:
        return name in self._components

    @property
    def is_animating(self) -> bool:
        """False by default.  Override in subclasses that mutate component
        offsets directly in their ``update()`` method (i.e. do not use the
        SceneAnimator system) so the renderer re-renders their components
        every frame rather than relying on ``animator.is_playing``."""
        return False

    def get_component_world_position(
        self, name: str
    ) -> Optional[Tuple[float, float]]:
        """Return the world-space position of the named component."""
        entry = self._components.get(name)
        if not entry:
            return None
        _, offset_x, offset_y = entry
        return (self.x + offset_x, self.y + offset_y)

    def get_component_at_point(
        self, x: float, y: float
    ) -> Optional[ISceneObject]:
        """Find the topmost component whose bounds contain the given point.

        Components are checked in descending layer order (foreground first).
        """
        # Sort by component layer descending for foreground-first hit-testing
        candidates = sorted(
            self._components.values(),
            key=lambda entry: entry[0].get_layer(),
            reverse=True,
        )
        for obj, offset_x, offset_y in candidates:
            wx = self.x + offset_x
            wy = self.y + offset_y
            if wx <= x <= wx + obj.width and wy <= y <= wy + obj.height:
                return obj
        return None

    # ------------------------------------------------------------------
    # Event routing
    # ------------------------------------------------------------------

    def contains_point(self, x: float, y: float) -> bool:
        """True if the point is within the composite bounds OR any component."""
        if super().contains_point(x, y):
            return True
        for obj, offset_x, offset_y in self._components.values():
            wx = self.x + offset_x
            wy = self.y + offset_y
            if wx <= x <= wx + obj.width and wy <= y <= wy + obj.height:
                return True
        return False

    def trigger_click(self, x: float, y: float) -> None:
        """Route click to the appropriate component, then to self if no match."""
        # Prefer component hit-testing first
        component = self.get_component_at_point(x, y)
        if component is not None and hasattr(component, "trigger_click"):
            component.trigger_click(x, y)  # type: ignore[union-attr]
        else:
            super().trigger_click(x, y)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Update the composite and all its components.

        Each component's physics body position is synchronised to its world
        position (composite origin + component offset) before the component
        is ticked, so the collision/spatial systems always see correct bounds.
        """
        super().update(dt)
        for obj, offset_x, offset_y in self._components.values():
            obj.x = self.x + offset_x
            obj.y = self.y + offset_y
            obj.update(dt)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        base = super().to_dict()
        components_data = []
        for name, (obj, offset_x, offset_y) in self._components.items():
            components_data.append({
                "name": name,
                "offset_x": offset_x,
                "offset_y": offset_y,
                "object": obj.to_dict(),
            })
        base["components"] = components_data
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "CompositeSceneObject":
        """Reconstruct a CompositeSceneObject from a serialized dictionary."""
        from pyrox.models.physics.factory import PhysicsSceneFactory

        body_data: dict = data.get("body", {})
        body_template = PhysicsSceneFactory.get_template(
            body_data.get("template_name", "")
        )
        if not body_template:
            raise ValueError(
                f"Physics body template '{body_data.get('template_name', '')}' "
                f"not registered."
            )
        body = body_template.body_class.from_dict(body_data)

        return cls(
            name=data["name"],
            physics_body=body,
            description=data.get("description", ""),
            scene_object_type=data.get("scene_object_type", SCENE_OBJECT_TYPE_COMPOSITE),
            template_name=data.get("template_name", SCENE_OBJECT_TYPE_COMPOSITE),
            id=data.get("id", None),
            group_id=data.get("group_id", None),
            properties=data.get("properties", {}),
            layer=data.get("layer", 0),
            tags=data.get("tags", []),
            components=data.get("components", None),
        )


# ---------------------------------------------------------------------------
# Factory registration — done once at import time so SceneObject.from_dict
# can dispatch to CompositeSceneObject when it sees template_name /
# scene_object_type equal to SCENE_OBJECT_TYPE_COMPOSITE ("composite").
# ---------------------------------------------------------------------------
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate  # noqa: E402

SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TYPE_COMPOSITE,
        scene_object_class=CompositeSceneObject,
        description="Design-locked composite that owns child components at relative offsets.",
        category="Groups",
    ),
)
