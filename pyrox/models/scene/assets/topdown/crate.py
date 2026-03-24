"""Top-down crate scene object.

Wraps a :class:`~pyrox.models.physics.crate.CrateBody` so that a movable
crate can be placed directly into a 2-D top-down scene.

Example::

    crate = CrateSceneObject.create(
        name="Wooden Crate",
        x=200.0,
        y=150.0,
        width=20.0,
        height=20.0,
        crate_type="wooden",
    )
    scene.add_scene_object(crate)
"""
from __future__ import annotations

from typing import cast

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.crate import CrateBody
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate
from pyrox.models.scene.sceneobject import SceneObject

SCENE_OBJECT_TYPE = "crate"
SCENE_OBJECT_TEMPLATE_NAME = "Top-Down Crate"
SCENE_OBJECT_DEF_COLOR = "#8B6914"

_CRATE_COLORS: dict[str, str] = {
    "wooden":    "#8B6914",
    "metal":     "#7A8A99",
    "cardboard": "#C4A265",
    "plastic":   "#4A90D9",
}


class CrateSceneObject(SceneObject):
    """Top-down crate scene object.

    A simple dynamic body that can be pushed by conveyors, pistons, and
    other physics objects.  The visual colour defaults to a sensible value
    for the selected ``crate_type`` but can be overridden via
    ``crate_color``.
    """

    def __init__(
        self,
        name: str,
        physics_body: CrateBody,
        description: str = "",
        crate_color: str = SCENE_OBJECT_DEF_COLOR,
        layer: int = 0,
        properties: dict | None = None,
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
        **kwargs,
    ) -> None:
        _props = properties or {}
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            scene_object_type=SCENE_OBJECT_TYPE,
            template_name=SCENE_OBJECT_TEMPLATE_NAME,
            bg_color=_props.get("crate_color", crate_color),
            layer=layer,
            properties=_props,
            id=id,
            group_id=group_id,
            tags=tags,
        )

        # Keep a typed reference for crate-specific attribute access.
        self._crate_body: CrateBody = physics_body

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @property
    def crate_type(self) -> str:
        """Type of crate (e.g. ``"wooden"``, ``"metal"``, ``"cardboard"``)."""
        return self._crate_body.crate_type

    @property
    def mass(self) -> float:
        """Mass of the crate in kilograms."""
        return self._crate_body.mass

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 20.0,
        height: float = 20.0,
        mass: float = 10.0,
        crate_type: str = "wooden",
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        crate_color: str | None = None,
        layer: int = 0,
        body: dict | None = None,
        **kwargs,
    ) -> "CrateSceneObject":
        """Create a :class:`CrateSceneObject` without manually building a physics body.

        Args:
            name:            Identifier for this crate.
            x:               Scene X position.
            y:               Scene Y position.
            width:           Width of the crate.
            height:          Height of the crate.
            mass:            Mass in kilograms.
            crate_type:      One of ``"wooden"``, ``"metal"``, ``"cardboard"``,
                             ``"plastic"``.
            collision_layer: Collision layer for the crate body.
            crate_color:     CSS hex colour override.  Defaults to a
                             sensible colour for the selected type.
            layer:           Render layer (z-order).
            body:            Optional serialised body dict (used when loading
                             from JSON via the factory).

        Returns:
            A fully-initialised :class:`CrateSceneObject`.
        """
        if body:
            physics_body = cast(CrateBody, CrateBody.from_dict(body))
        else:
            physics_body = CrateBody(
                name=f"{name}_body",
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                mass=float(mass),
                crate_type=crate_type,
                collision_layer=collision_layer,
            )

        resolved_color = crate_color or _CRATE_COLORS.get(crate_type, SCENE_OBJECT_DEF_COLOR)
        return cls(
            name=name,
            physics_body=physics_body,
            crate_color=resolved_color,
            layer=layer,
            id=kwargs.get("id"),
            description=kwargs.get("description", ""),
            group_id=kwargs.get("group_id"),
            tags=kwargs.get("tags"),
            properties=kwargs.get("properties"),
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _compile_properties(self) -> None:
        super().compile_properties()
        self._properties["crate_color"] = self._bg_color
        self._properties["crate_type"] = self._crate_body.crate_type

    @classmethod
    def from_dict(cls, data: dict) -> "CrateSceneObject":
        """Restore a :class:`CrateSceneObject` from a serialised dictionary."""
        body_data = data.get("body", {})
        physics_body = cast(CrateBody, CrateBody.from_dict(body_data))
        props = data.get("properties", {})
        crate_type = props.get("crate_type", "wooden")
        return cls(
            name=data["name"],
            physics_body=physics_body,
            description=data.get("description", ""),
            crate_color=props.get("crate_color", _CRATE_COLORS.get(crate_type, SCENE_OBJECT_DEF_COLOR)),
            layer=data.get("layer", 0),
            properties=props,
            id=data.get("id"),
            group_id=data.get("group_id"),
            tags=data.get("tags", []),
        )


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME,
        scene_object_class=CrateSceneObject,
        description="Dynamic crate that can be pushed by conveyors, pistons and other physics objects (top-down view)",
        factory_func=CrateSceneObject.create,
        default_kwargs={
            "name": SCENE_OBJECT_TEMPLATE_NAME,
            "width": 20.0,
            "height": 20.0,
            "mass": 10.0,
            "crate_type": "wooden",
            "layer": 0,
        },
        category="Objects",
    )
)
