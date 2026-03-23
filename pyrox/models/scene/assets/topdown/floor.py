"""Top-down floor scene object.
"""
from __future__ import annotations

from typing import cast

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.floor import FloorBody
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate
from pyrox.models.scene.sceneobject import SceneObject

SCENE_OBJECT_TYPE = "floor"
SCENE_OBJECT_TEMPLATE_NAME = "Top-Down Floor"
SCENE_OBJECT_DEF_COLOR = "#202020"


class FloorSceneObject(SceneObject):
    """Top-down floor scene object.
    """

    def __init__(
        self,
        name: str,
        physics_body: FloorBody,
        description: str = "",
        floor_color: str = SCENE_OBJECT_DEF_COLOR,
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
            bg_color=_props.get("floor_color", floor_color),
            layer=layer,
            properties=_props,
            id=id,
            group_id=group_id,
            tags=tags,
        )

        # Keep a typed reference for sensor-specific attribute access.
        self._floor_body: FloorBody = physics_body

    # ------------------------------------------------------------------
    # Convenience factory
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        name: str,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        collision_layer: CollisionLayer = CollisionLayer.TERRAIN,
        floor_color: str = SCENE_OBJECT_DEF_COLOR,
        layer: int = 0,
        body: dict | None = None,
        **kwargs,
    ) -> "FloorSceneObject":
        """Create a :class:`SensorSceneObject` without manually building a physics body.

        Args:
            name:            Identifier for this sensor.
            x:               Scene X position.
            y:               Scene Y position.
            width:           Width of the detection zone.
            height:          Height of the detection zone.
            collision_layer: Collision layer for the sensor body.
            sensor_color:    CSS hex colour used when rendering the zone.
            layer:           Render layer (z-order).
            body:            Optional serialised body dict (used when loading
                             from JSON via the factory).

        Returns:
            A fully-initialised :class:`SensorSceneObject`.
        """
        if body:
            physics_body = cast(FloorBody, FloorBody.from_dict(body))
        else:
            physics_body = FloorBody(
                name=f"{name}_body",
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                collision_layer=collision_layer,
            )
        return cls(
            name=name,
            physics_body=physics_body,
            floor_color=floor_color,
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
        super()._compile_properties()
        self._properties["floor_color"] = self._bg_color

    @classmethod
    def from_dict(cls, data: dict) -> "FloorSceneObject":
        """Restore a :class:`SensorSceneObject` from a serialised dictionary."""
        body_data = data.get("body", {})
        physics_body = cast(FloorBody, FloorBody.from_dict(body_data))
        props = data.get("properties", {})
        return cls(
            name=data["name"],
            physics_body=physics_body,
            description=data.get("description", ""),
            floor_color=props.get("floor_color", SCENE_OBJECT_DEF_COLOR),
            layer=data.get("layer", 0),
            properties=props,
            id=data.get("id"),
            group_id=data.get("group_id"),
            tags=data.get("tags", []),
        )


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SCENE_OBJECT_TEMPLATE_NAME,
        scene_object_class=FloorSceneObject,
        description="Floor scene object (top-down view)",
        factory_func=FloorSceneObject.create,
        default_kwargs={
            "name": SCENE_OBJECT_TEMPLATE_NAME,
            "width": 800.0,
            "height": 800.0,
            "floor_color": SCENE_OBJECT_DEF_COLOR,
            "layer": 0,
        },
        category="Floor",
    )
)
