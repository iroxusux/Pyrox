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
import uuid

from pyrox.interfaces import (
    IBasePhysicsBody,
    ISceneObject,
)
from pyrox.interfaces.scene.compositesceneobject import ICompositeSceneObject
from pyrox.models.scene.sceneobject import SceneObject
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate
from pyrox.models.physics.factory import PhysicsSceneFactory


class CompositeSceneObject(SceneObject, ICompositeSceneObject):
    """Design-locked composite that owns child components at relative offsets.

    The composite is the sole entry in ``scene._scene_objects``.  Children are
    stored in ``_components`` as ``(obj, offset_x, offset_y)`` tuples.

    World position of a component:
        ``world_x = composite.x + offset_x``
        ``world_y = composite.y + offset_y``

    Events (clicks, updates) are routed through the composite to components.
    """

    _scene_object_type: str = "composite"
    _template_name: str = "CompositeSceneObject"

    def __init__(
        self,
        name: str,
        physics_body: IBasePhysicsBody,
        description: str = "",
        id: str | None = None,
        group_id: str | None = None,
        properties: dict | None = None,
        parent: SceneObject | None = None,
        layer: int = 0,
        tags: list[str] | None = None,
        components: list[dict] | dict | None = None,
        direction=None,
    ):
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            id=id or f'{self._scene_object_type}_{uuid.uuid4()}',
            group_id=group_id,
            properties=properties,
            parent=parent,
            layer=layer,
            tags=tags,
        )

        # _components must be initialised before set_direction is called, because
        # set_direction → rotate_components iterates self._components.
        if isinstance(components, list):
            # Convert list of dicts to internal dict format
            self._components: dict[str, ISceneObject] = {}
            for comp in components:
                comp_name = comp["name"]
                obj_data = comp["object"]
                obj = SceneObject.from_dict(obj_data)
                self._components[comp_name] = obj
        elif isinstance(components, dict):
            # Assume already in internal dict format
            self._components = components
        else:
            self._components: dict[str, ISceneObject] = {}

        if direction is not None:
            self.set_direction(direction)

        # Tracking for velocity-based position updates (e.g. physics body)
        self._component_world_position_cache = {}

    # ------------------------------------------------------------------
    # Event routing
    # ------------------------------------------------------------------

    def contains_point(self, x: float, y: float) -> bool:
        """True if the point is within the composite bounds OR any component."""
        if super().contains_point(x, y):
            return True
        for obj in self._components.values():
            wx = self.x + obj._parent_offset_x
            wy = self.y + obj._parent_offset_y
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
        for obj in self._components.values():
            ox, oy = obj.parent_offset
            obj.x = self.x + ox
            obj.y = self.y + oy
            obj.update(dt)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        base = super().to_dict()
        components_data = []
        for name, obj in self._components.items():
            components_data.append({
                "name": name,
                "object": obj.to_dict(),
            })
        base["components"] = components_data
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "CompositeSceneObject":
        """Reconstruct a CompositeSceneObject from a serialized dictionary."""

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
            id=data.get("id", None),
            group_id=data.get("group_id", None),
            properties=data.get("properties", {}),
            layer=data.get("layer", 0),
            tags=data.get("tags", []),
            components=data.get("components", None),
        )


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=CompositeSceneObject._template_name,
        scene_object_class=CompositeSceneObject,
        description="Design-locked composite that owns child components at relative offsets.",
        category="Groups",
    ),
)
