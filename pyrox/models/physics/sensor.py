"""Proximity sensor physics body implementation.

Provides a trigger-based proximity sensor that detects when objects
enter or exit its detection zone without physically interacting with them.
"""
from typing import List, Callable, Set, Any
from pyrox.interfaces.protocols.physics import (
    BodyType,
    ColliderType,
    CollisionLayer,
    IPhysicsBody2D,
)
from pyrox.models.physics.base import BasePhysicsBody
from pyrox.models.protocols.physics import Material
from .factory import PhysicsSceneTemplate, PhysicsSceneFactory


class ProximitySensorBody(BasePhysicsBody):
    """Proximity sensor that detects objects entering/exiting without collision.

    A proximity sensor is a STATIC trigger body that doesn't physically
    interact with objects, but tracks when they enter or exit its zone.
    Perfect for conveyor belt checkpoints, doorways, or trigger zones.

    The sensor fires events when its state changes:
    - Activated: When first object enters (empty -> occupied)
    - Deactivated: When last object exits (occupied -> empty)

    Attributes:
        is_active: Whether the sensor currently detects any objects
        detected_objects: Set of objects currently in the sensor zone
        detection_count: Number of objects currently detected
    """

    def __init__(
        self,
        name: str = "ProximitySensor",
        template_name: str = "Proximity Sensor",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 10.0,
        height: float = 10.0,
        collision_layer: CollisionLayer = CollisionLayer.DEFAULT,
        collision_mask: List[CollisionLayer] | None = None,
        *args,
        **kwargs
    ):
        """Initialize proximity sensor.

        Args:
            name: Name of the sensor
            x: X position
            y: Y position
            width: Width of detection zone (keep small for conveyors)
            height: Height of detection zone
            collision_layer: Collision layer for the sensor
            collision_mask: Which layers can be detected
        """
        # Default collision mask includes common dynamic objects
        if collision_mask is None:
            collision_mask = [
                CollisionLayer.DEFAULT,
                CollisionLayer.PLAYER,
                CollisionLayer.ENEMY,
            ]

        # Sensors are always STATIC triggers with no mass
        super().__init__(
            name=name,
            template_name=template_name,
            tags=["sensor", "proximity"],
            body_type=BodyType.STATIC,
            is_trigger=True,
            mass=0.0,
            x=x,
            y=y,
            width=width,
            height=height,
            collision_layer=collision_layer,
            collision_mask=collision_mask,
            collider_type=ColliderType.RECTANGLE,
            material=Material(
                density=0.0,
                restitution=0.0,
                friction=0.0,
                drag=0.0
            )
        )

        # Tracking
        self._detected_objects: Set[IPhysicsBody2D] = set()
        self._is_active: bool = False

        # State change callbacks
        self._on_activate_callbacks: List[Callable[['ProximitySensorBody'], None]] = []
        self._on_deactivate_callbacks: List[Callable[['ProximitySensorBody'], None]] = []

        # Object detection callbacks
        self._on_object_enter_callbacks: List[Callable[['ProximitySensorBody', IPhysicsBody2D], None]] = []
        self._on_object_exit_callbacks: List[Callable[['ProximitySensorBody', IPhysicsBody2D], None]] = []

    @property
    def is_active(self) -> bool:
        """Check if sensor is currently detecting any objects.

        Returns:
            True if at least one object is in the detection zone
        """
        return self._is_active

    @property
    def detected_objects(self) -> Set[IPhysicsBody2D]:
        """Get set of currently detected objects.

        Returns:
            Set of physics bodies in the detection zone
        """
        return self._detected_objects.copy()

    @property
    def detection_count(self) -> int:
        """Get number of objects currently detected.

        Returns:
            Count of objects in the detection zone
        """
        return len(self._detected_objects)

    @property
    def on_activate_callbacks(self) -> List[Callable[['ProximitySensorBody'], None]]:
        """Get list of callbacks fired when sensor activates (empty -> occupied).

        Returns:
            List of callback functions
        """
        return self._on_activate_callbacks

    @property
    def on_deactivate_callbacks(self) -> List[Callable[['ProximitySensorBody'], None]]:
        """Get list of callbacks fired when sensor deactivates (occupied -> empty).

        Returns:
            List of callback functions
        """
        return self._on_deactivate_callbacks

    @property
    def on_object_enter_callbacks(self) -> List[Callable[['ProximitySensorBody', IPhysicsBody2D], None]]:
        """Get list of callbacks fired when an object enters the zone.

        Returns:
            List of callback functions
        """
        return self._on_object_enter_callbacks

    @property
    def on_object_exit_callbacks(self) -> List[Callable[['ProximitySensorBody', IPhysicsBody2D], None]]:
        """Get list of callbacks fired when an object exits the zone.

        Returns:
            List of callback functions
        """
        return self._on_object_exit_callbacks

    def on_collision_enter(self, other: IPhysicsBody2D) -> None:
        """Called when an object enters the sensor zone.

        Args:
            other: The physics body entering the detection zone
        """
        # Add to detected objects
        if other not in self._detected_objects:
            self._detected_objects.add(other)

            # Fire object enter callbacks
            for callback in self._on_object_enter_callbacks:
                try:
                    callback(self, other)
                except Exception as e:
                    print(f"Error in sensor object_enter callback: {e}")

            # Check if this activates the sensor
            if not self._is_active:
                self._activate()

    def on_collision_exit(self, other: IPhysicsBody2D) -> None:
        """Called when an object exits the sensor zone.

        Args:
            other: The physics body exiting the detection zone
        """
        # Remove from detected objects
        if other in self._detected_objects:
            self._detected_objects.remove(other)

            # Fire object exit callbacks
            for callback in self._on_object_exit_callbacks:
                try:
                    callback(self, other)
                except Exception as e:
                    print(f"Error in sensor object_exit callback: {e}")

            # Check if this deactivates the sensor
            if self._is_active and len(self._detected_objects) == 0:
                self._deactivate()

    def _activate(self) -> None:
        """Activate the sensor (first object entered).

        Fires all on_activate callbacks.
        """
        if not self._is_active:
            self._is_active = True

            # Fire activate callbacks
            for callback in self._on_activate_callbacks:
                try:
                    callback(self)
                except Exception as e:
                    print(f"Error in sensor activate callback: {e}")

    def _deactivate(self) -> None:
        """Deactivate the sensor (last object exited).

        Fires all on_deactivate callbacks.
        """
        if self._is_active:
            self._is_active = False

            # Fire deactivate callbacks
            for callback in self._on_deactivate_callbacks:
                try:
                    callback(self)
                except Exception as e:
                    print(f"Error in sensor deactivate callback: {e}")

    def clear_detected_objects(self) -> None:
        """Clear all detected objects and deactivate sensor.

        Useful for resetting sensor state.
        """
        self._detected_objects.clear()
        if self._is_active:
            self._deactivate()

    def is_detecting(self, body: IPhysicsBody2D) -> bool:
        """Check if a specific body is currently detected.

        Args:
            body: Physics body to check for

        Returns:
            True if the body is in the detection zone
        """
        return body in self._detected_objects

    @classmethod
    def create_small_sensor(
        cls,
        name: str = "SmallSensor",
        x: float = 0.0,
        y: float = 0.0,
    ) -> 'ProximitySensorBody':
        """Factory method to create a small sensor for conveyor belts.

        Args:
            name: Name of the sensor
            x: X position
            y: Y position

        Returns:
            Small proximity sensor (5x5 units)
        """
        return cls(
            name=name,
            x=x,
            y=y,
            width=5.0,
            height=5.0
        )

    @classmethod
    def create_checkpoint_sensor(
        cls,
        name: str = "Checkpoint",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 20.0,
    ) -> 'ProximitySensorBody':
        """Factory method to create a checkpoint sensor spanning a path.

        Args:
            name: Name of the sensor
            x: X position
            y: Y position
            width: Width of the checkpoint (spans path)

        Returns:
            Thin checkpoint sensor for detecting passage
        """
        return cls(
            name=name,
            x=x,
            y=y,
            width=width,
            height=5.0
        )

    def get_outputs(self) -> dict[str, Any]:
        """Get available output connections.

        Returns:
            Dictionary of output names to callback lists
        """
        return {
            "on_activate_callbacks": self.on_activate_callbacks,
            "on_deactivate_callbacks": self.on_deactivate_callbacks,
            "on_object_enter_callbacks": self.on_object_enter_callbacks,
            "on_object_exit_callbacks": self.on_object_exit_callbacks,
        }


PhysicsSceneFactory.register_template(
    template_name="Proximity Sensor",
    template=PhysicsSceneTemplate(
        name="Proximity Sensor",
        body_class=ProximitySensorBody,
        default_kwargs={
            "width": 10.0,
            "height": 10.0,
            "collision_layer": CollisionLayer.SENSOR,
            "collision_mask": [
                    CollisionLayer.DEFAULT,
                    CollisionLayer.PLAYER,
                    CollisionLayer.ENEMY,
            ],
        }
    )
)
