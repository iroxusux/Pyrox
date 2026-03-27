"""Top-down proximity sensor scene object.

Wraps a :class:`~pyrox.models.physics.sensor.ProximitySensorBody` and exposes
signal callback lists directly on the SceneObject so the connection registry
can wire to *this* object without ever touching the physics body.  The physics
body stays focused on collision detection; signal dispatch travels through the
SceneObject layer.

Example::

    sensor = SensorSceneObject.create(
        name="Part Present",
        x=100.0,
        y=100.0,
        width=10.0,
        height=10.0,
    )
    scene.add_scene_object(sensor)

    # Wire sensor → piston via the connection registry:
    registry.connect(
        source_id=sensor.id,
        output_name="on_activate_callbacks",
        target_id=piston.id,
        input_name="activate",
    )
"""
from __future__ import annotations

from typing import Any, Callable, cast

from pyrox.interfaces import CollisionLayer
from pyrox.models.physics.sensor import ProximitySensorBody
from pyrox.models.scene.factory import SceneObjectFactory, SceneObjectTemplate
from pyrox.models.scene.sceneobject import SceneObject


class SensorSceneObject(SceneObject):
    """Top-down proximity sensor scene object.

    Owns four signal callback lists so the connection registry can wire
    directly to this SceneObject without knowledge of the underlying physics
    body.  When the physics body fires its native events the SceneObject
    bridges them to its own lists.

    Signals (outputs):
        on_activate_callbacks:     Fired when the sensor transitions from
                                   empty → occupied (first object enters).
        on_deactivate_callbacks:   Fired when the sensor transitions from
                                   occupied → empty (last object exits).
        on_object_enter_callbacks: Fired each time any individual object
                                   enters the detection zone.
        on_object_exit_callbacks:  Fired each time any individual object
                                   exits the detection zone.

    Inputs:
        activate:   Force-fire the activate signal (useful for testing).
        deactivate: Force-fire the deactivate signal.
        clear:      Reset detected objects and deactivate the sensor body.
    """

    _scene_object_type: str = "sensor"
    _template_name: str = "Top-Down Proximity Sensor"

    def __init__(
        self,
        name: str,
        physics_body: ProximitySensorBody,
        description: str = "",
        sensor_color: str = "#00ffff",
        layer: int = 0,
        properties: dict | None = None,
        id: str | None = None,
        group_id: str | None = None,
        tags: list[str] | None = None,
        **kwargs,
    ) -> None:
        # Own callback lists — the connection registry attaches to these.
        self._on_activate_callbacks: list[Callable] = []
        self._on_deactivate_callbacks: list[Callable] = []
        self._on_object_enter_callbacks: list[Callable] = []
        self._on_object_exit_callbacks: list[Callable] = []

        _props = properties or {}
        super().__init__(
            name=name,
            physics_body=physics_body,
            description=description,
            bg_color=_props.get("sensor_color", sensor_color),
            layer=layer,
            properties=_props,
            id=id,
            group_id=group_id,
            tags=tags,
        )

        # Keep a typed reference for sensor-specific attribute access.
        self._sensor_body: ProximitySensorBody = physics_body

        # Bridge physics body events → this SceneObject's callback lists.
        physics_body.on_activate_callbacks.append(self._bridge_activate)
        physics_body.on_deactivate_callbacks.append(self._bridge_deactivate)
        physics_body.on_object_enter_callbacks.append(self._bridge_object_enter)
        physics_body.on_object_exit_callbacks.append(self._bridge_object_exit)

    # ------------------------------------------------------------------
    # Bridge methods — forward physics body events to SceneObject lists
    # ------------------------------------------------------------------

    def _bridge_activate(self, state: bool) -> None:
        for cb in list(self._on_activate_callbacks):
            cb(state)

    def _bridge_deactivate(self, state: bool) -> None:
        for cb in list(self._on_deactivate_callbacks):
            cb(state)

    def _bridge_object_enter(self, sensor: ProximitySensorBody, obj: Any) -> None:
        for cb in list(self._on_object_enter_callbacks):
            cb(self, obj)

    def _bridge_object_exit(self, sensor: ProximitySensorBody, obj: Any) -> None:
        for cb in list(self._on_object_exit_callbacks):
            cb(self, obj)

    # ------------------------------------------------------------------
    # Output properties — exposed for getattr in the connection registry
    # ------------------------------------------------------------------

    @property
    def on_activate_callbacks(self) -> list[Callable]:
        """Callback list fired when the sensor transitions empty → occupied."""
        return self._on_activate_callbacks

    @property
    def on_deactivate_callbacks(self) -> list[Callable]:
        """Callback list fired when the sensor transitions occupied → empty."""
        return self._on_deactivate_callbacks

    @property
    def on_object_enter_callbacks(self) -> list[Callable]:
        """Callback list fired each time an object enters the detection zone."""
        return self._on_object_enter_callbacks

    @property
    def on_object_exit_callbacks(self) -> list[Callable]:
        """Callback list fired each time an object exits the detection zone."""
        return self._on_object_exit_callbacks

    # ------------------------------------------------------------------
    # Input methods — exposed for getattr in the connection registry
    # ------------------------------------------------------------------

    def activate(self, *_) -> None:
        """Force-fire the activate signal (empty → occupied transition)."""
        self._bridge_activate(True)

    def deactivate(self, *_) -> None:
        """Force-fire the deactivate signal (occupied → empty transition)."""
        self._bridge_deactivate(False)

    def clear(self) -> None:
        """Clear all detected objects and deactivate the physics sensor."""
        self._sensor_body.clear_detected_objects()

    # ------------------------------------------------------------------
    # ISceneObject — connection endpoints
    # ------------------------------------------------------------------

    def get_outputs(self) -> dict[str, Any]:
        """Return output signal endpoints for the connection registry."""
        return {
            "on_activate_callbacks": self.on_activate_callbacks,
            "on_deactivate_callbacks": self.on_deactivate_callbacks,
            "on_object_enter_callbacks": self.on_object_enter_callbacks,
            "on_object_exit_callbacks": self.on_object_exit_callbacks,
        }

    def get_inputs(self) -> dict[str, Callable[..., None]]:
        """Return input method endpoints for the connection registry."""
        return {
            "activate": self.activate,
            "deactivate": self.deactivate,
            "clear": self.clear,
        }

    # ------------------------------------------------------------------
    # Status / introspection
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """``True`` when the sensor is currently detecting at least one object."""
        return self._sensor_body.is_active

    @property
    def detection_count(self) -> int:
        """Number of objects currently inside the detection zone."""
        return self._sensor_body.detection_count

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
        collision_layer: CollisionLayer = CollisionLayer.SENSOR,
        sensor_color: str = "#00ffff",
        layer: int = 0,
        body: dict | None = None,
        **kwargs,
    ) -> "SensorSceneObject":
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
            physics_body = cast(ProximitySensorBody, ProximitySensorBody.from_dict(body))
        else:
            physics_body = ProximitySensorBody(
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
            sensor_color=sensor_color,
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
        self._properties["sensor_color"] = self._bg_color

    @classmethod
    def from_dict(cls, data: dict) -> "SensorSceneObject":
        """Restore a :class:`SensorSceneObject` from a serialised dictionary."""
        body_data = data.get("body", {})
        physics_body = cast(ProximitySensorBody, ProximitySensorBody.from_dict(body_data))
        props = data.get("properties", {})
        return cls(
            name=data["name"],
            physics_body=physics_body,
            description=data.get("description", ""),
            sensor_color=props.get("sensor_color", "#00ffff"),
            layer=data.get("layer", 0),
            properties=props,
            id=data.get("id"),
            group_id=data.get("group_id"),
            tags=data.get("tags", []),
        )


SceneObjectFactory.register_template(
    SceneObjectTemplate(
        name=SensorSceneObject._template_name,
        scene_object_class=SensorSceneObject,
        description="Proximity sensor that fires signals when objects enter or exit the detection zone (top-down view)",
        factory_func=SensorSceneObject.create,
        default_kwargs={
            "name": SensorSceneObject._template_name,
            "width": 10.0,
            "height": 10.0,
            "sensor_color": "#00ffff",
            "layer": 0,
        },
        category="Sensors",
    )
)
