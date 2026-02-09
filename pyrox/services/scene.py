from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union
import json
from pathlib import Path
from pyrox.interfaces import (
    IApplication,
    IPhysicsBody2D,
    IScene,
    ISceneObject,
    ISceneRunnerService,
)

from pyrox.services import GuiManager, log
from pyrox.services.file import get_open_file, get_save_file
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService


class HasSceneMixin:
    def __init__(
        self,
        scene: Optional[IScene] = None,
    ):
        self._scene = scene

    def get_scene(self) -> Optional[IScene]:
        return self._scene

    def set_scene(self, scene: Optional[IScene]) -> None:
        self._scene = scene

    @property
    def scene(self) -> Optional[IScene]: return self.get_scene()


class SceneEventType(Enum):
    """Types of scene-related events."""

    SCENE_LOADED = auto()  # A scene was loaded
    SCENE_UNLOADED = auto()  # A scene was unloaded
    SCENE_STARTED = auto()  # Scene runner started
    SCENE_STOPPED = auto()  # Scene runner stopped
    SCENE_MODIFIED = auto()  # Scene was modified
    OBJECT_ADDED = auto()  # Object added to scene
    OBJECT_REMOVED = auto()  # Object removed from scene
    OBJECT_SELECTED = auto()  # Object selected in GUI
    OBJECT_DESELECTED = auto()  # Object deselected in GUI


@dataclass
class SceneEvent:
    """Event data for scene-related events."""

    event_type: SceneEventType
    scene: Optional[Any] = None  # The scene object, if applicable
    data: Optional[Dict[str, Any]] = field(default_factory=dict)  # Additional event data


class SceneEventBus:
    """Static event bus for scene-related events.

    This provides a centralized pub/sub system for scene events, enabling
    loose coupling between components that need to react to scene state changes.

    Usage:
        # Subscribe to events
        def on_scene_loaded(event: SceneEvent):
            print(f"Scene loaded: {event.scene}")

        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED, on_scene_loaded)

        # Publish events
        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_LOADED,
            scene=my_scene
        ))

        # Unsubscribe
        SceneEventBus.unsubscribe(SceneEventType.SCENE_LOADED, on_scene_loaded)
    """

    _subscribers: Dict[SceneEventType, List[Callable[[SceneEvent], None]]] = {}

    @classmethod
    def subscribe(
        cls,
        event_type: SceneEventType,
        callback: Callable[[SceneEvent], None]
    ) -> None:
        """Subscribe to a scene event type.

        Args:
            event_type: The type of event to subscribe to
            callback: Function to call when the event occurs.
                     Should accept a SceneEvent parameter.
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []

        if callback not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(callback)
            log(cls).debug(f"Subscribed {callback.__name__} to {event_type.name}")

    @classmethod
    def unsubscribe(
        cls,
        event_type: SceneEventType,
        callback: Callable[[SceneEvent], None]
    ) -> None:
        """Unsubscribe from a scene event type.

        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in cls._subscribers:
            if callback in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(callback)
                log(cls).debug(f"Unsubscribed {callback.__name__} from {event_type.name}")

    @classmethod
    def publish(cls, event: SceneEvent) -> None:
        """Publish a scene event to all subscribers.

        Args:
            event: The event to publish
        """
        subscribers = cls._subscribers.get(event.event_type, [])

        log(cls).debug(f"Publishing {event.event_type.name} to {len(subscribers)} subscribers")

        # Call each subscriber, removing any that raise exceptions
        dead_callbacks = []
        for callback in subscribers.copy():
            try:
                callback(event)
            except Exception as e:
                log(cls).error(f"Error in event subscriber {callback.__name__}: {e}")
                dead_callbacks.append(callback)

        # Remove dead callbacks
        for callback in dead_callbacks:
            cls.unsubscribe(event.event_type, callback)

    @classmethod
    def clear(cls) -> None:
        """Clear all subscriptions. Useful for testing."""
        cls._subscribers.clear()
        log(cls).debug("Cleared all event subscriptions")

    @classmethod
    def get_subscriber_count(cls, event_type: SceneEventType) -> int:
        """Get the number of subscribers for an event type.

        Args:
            event_type: The event type to query

        Returns:
            Number of subscribers
        """
        return len(cls._subscribers.get(event_type, []))


class SceneRunnerService(
    ISceneRunnerService,
):
    """Static class, run scenes with a supplied GUI Application context.

    Integrates physics simulation with scene updates, providing a complete
    runtime environment with fixed timestep physics and frame-rate independent
    rendering.
    """
    # State
    _running: bool = False
    _enable_physics: bool = False
    _update_interval_ms: int = 16
    _current_time = datetime.now().timestamp()

    # Objects and services
    _scene: Optional[IScene] = None
    _environment: Optional[EnvironmentService] = None
    _physics_engine: Optional[PhysicsEngineService] = None

    # Events
    _event_id: Optional[int | str] = None

    def __init__(self):
        raise ValueError("SceneRunnerService is a static class and cannot be initialized directly!")

    @classmethod
    def initialize(
        cls,
        app: IApplication,
        scene: Optional[IScene] = None,
        physics_engine: Optional[PhysicsEngineService] = None,
        environment: Optional[EnvironmentService] = None,
        enable_physics: bool = False,
        update_interval: int = 16  # ~60 FPS (16ms)
    ):
        """Initialize the service.

        Args:
            app: The Application context to use
            scene: The scene to run
            physics_engine: Optional physics engine (creates default if None and enable_physics=True)
            environment: Optional environment service (creates default if None and enable_physics=True)
            enable_physics: Whether to enable physics simulation
        """
        # Set application context
        cls._app = app
        cls._enable_physics = enable_physics

        # Physics integration
        if enable_physics:
            cls.set_environment(environment or EnvironmentService())
            cls.set_physics_engine(physics_engine or PhysicsEngineService(
                environment=cls._environment
            ))
        else:
            cls.set_environment(None)
            cls.set_physics_engine(None)

        # Set initial scene, bind to events and register physics bodies
        cls.set_scene(scene)
        cls._bind_to_scene_events()
        cls._register_physics_bodies()

        # Update timing
        cls._update_interval_ms = update_interval
        cls._current_time = datetime.now().timestamp()

        # Initialize events and callbacks
        cls._event_id = None

    @classmethod
    def get_scene(cls) -> Optional[IScene]:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        return cls._scene

    @classmethod
    def set_scene(
        cls,
        scene: Optional[IScene]
    ) -> None:
        """Set the scene to be managed.

        Args:
            scene: The new scene instance.
        """
        cls._scene = scene
        if scene:
            cls._register_physics_bodies()
            cls._bind_to_scene_events()
            event_type = SceneEventType.SCENE_LOADED
        else:
            event_type = SceneEventType.SCENE_UNLOADED

        SceneEventBus.publish(SceneEvent(
            event_type=event_type,
            scene=scene
        ))

    @classmethod
    def new_scene(cls) -> None:
        """Create and set a new empty scene.
        """
        from pyrox.models.scene import Scene
        scene = Scene()
        cls.set_scene(scene)

    @classmethod
    def load_scene(
        cls,
        filepath: Optional[str | Path] = None
    ) -> None:
        if not filepath:
            filepath = get_open_file(
                title="Load Scene",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filepath:
                log(cls).info("Scene load cancelled")
                return

        if not Path(filepath).is_file():
            log(cls).error(f"Scene file not found: {filepath}")
            return

        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            from pyrox.models.scene import Scene
            data = json.load(f)
            scene = Scene.from_dict(data)
            cls.set_scene(scene)

    @classmethod
    def save_scene(
        cls,
        filepath: Optional[str | Path] = None
    ) -> None:
        if not cls._scene:
            log(cls).warning("No scene to save")
            return

        if not filepath:
            filepath = get_save_file(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if not filepath:
                log(cls).info("Scene save cancelled")
                return

        filepath = Path(filepath)
        data = cls._scene.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def get_physics_engine(cls) -> PhysicsEngineService | None:
        """Get the physics engine being used.

        Returns:
            Physics engine instance, or None if physics is disabled.
        """
        return cls._physics_engine

    @classmethod
    def set_physics_engine(cls, physics_engine: PhysicsEngineService | None) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance.
        """
        cls._physics_engine = physics_engine

    @classmethod
    def get_environment(cls) -> EnvironmentService | None:
        """Get the environment service being used.

        Returns:
            Environment service instance, or None if physics is disabled.
        """
        return cls._environment

    @classmethod
    def set_environment(cls, environment: EnvironmentService | None) -> None:  # type: ignore
        """Set the environment service to be used.

        Args:
            environment: The environment service instance.
        """
        cls._environment = environment

    @classmethod
    def _bind_to_scene_events(cls) -> None:
        """Bind to scene events for object addition/removal.
        """
        if not cls._scene:
            return

        if cls.add_physics_body not in cls._scene.on_scene_object_added:
            cls._scene.on_scene_object_added.append(cls.add_physics_body)
        if cls.remove_physics_body not in cls._scene.on_scene_object_removed:
            cls._scene.on_scene_object_removed.append(cls.remove_physics_body)

    @classmethod
    def _register_physics_bodies(cls) -> None:
        """Register all physics-enabled scene objects with the physics engine.
        """
        if not cls._scene:
            return

        if not cls._physics_engine:
            log(cls).warning('Unable to register physics bodies!\nPhysics engine is not initialized!')
            return

        if not cls._enable_physics:
            log(cls).info('Physics is disabled, skipping physics body registration.')
            return

        scene_objects = cls._scene.get_scene_objects()
        for scene_object in scene_objects.values():
            # Check if object implements physics body protocol
            if isinstance(scene_object.physics_body, IPhysicsBody2D):
                cls._physics_engine.register_body(scene_object.physics_body)
            else:
                raise TypeError("Scene object physics body does not implement IPhysicsBody2D protocol")

    @classmethod
    def run(cls) -> int:
        """Run the scene within the application context."""
        if cls._running:
            return 1  # Already running

        cls._running = True
        cls._current_time = datetime.now().timestamp()

        # Schedule periodic updates
        cls._event_id = GuiManager.unsafe_get_backend().schedule_event(
            cls._update_interval_ms,
            lambda: cls._run_scene()
        )
        return 0

    @classmethod
    def stop(cls, stop_code: int = 0) -> None:
        """Stop the scene runner."""
        # Stop running
        cls._running = False

        # Cancel scheduled updates
        if cls._event_id:
            GuiManager.unsafe_get_backend().cancel_scheduled_event(cls._event_id)

        # Reset state
        cls._event_id = None
        log(cls).info(f"Scene runner stopped with code {stop_code}")

    @classmethod
    def _run_scene(cls) -> None:
        """Internal method to update the scene each frame."""
        if not cls._running:
            return

        if not cls._scene:
            log(cls).warning("No scene loaded, stopping scene runner.")
            cls.stop()
            return

        # Calculate time delta
        new_time = datetime.now().timestamp()
        time_delta = new_time - cls._current_time
        cls._current_time = new_time

        # Clamp time delta to prevent spiral of death
        time_delta = min(time_delta, 0.1)  # Max 100ms

        # Update physics (if enabled)
        if cls._enable_physics and cls._physics_engine:
            cls._physics_engine.step(time_delta)

        # Update scene
        cls._scene.update(time_delta)

        # Schedule scene update on the main thread
        cls._event_id = GuiManager.unsafe_get_backend().schedule_event(
            cls._update_interval_ms,
            lambda: cls._run_scene()
        )

    @classmethod
    def get_update_rate(cls) -> float:
        """Get the current update rate in frames per second.

        Returns:
            Current frames per second
        """
        return 1000.0 / cls._update_interval_ms

    @classmethod
    def set_update_rate(cls, fps: float) -> None:
        """Set the update rate in frames per second.

        Args:
            fps: Target frames per second (1-240)
        """
        if not 1 <= fps <= 240:
            raise ValueError("FPS must be between 1 and 240")
        cls._update_interval_ms = int(1000 / fps)

    @classmethod
    def add_physics_body(cls, body: Union[IPhysicsBody2D, ISceneObject]) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IPhysicsBody protocol
        """
        if isinstance(body, ISceneObject):
            if not isinstance(body.physics_body, IPhysicsBody2D):
                raise TypeError("SceneObject does not have a valid physics body")
            body = body.physics_body

        if cls._physics_engine:
            cls._physics_engine.register_body(body)

    @classmethod
    def remove_physics_body(cls, body) -> None:
        """Remove a physics body from the simulation.

        Args:
            body: Object to remove
        """
        if cls._physics_engine:
            cls._physics_engine.unregister_body(body)

    @classmethod
    def get_physics_stats(cls) -> dict:
        """Get physics engine statistics.

        Returns:
            Dictionary with physics stats, or empty dict if physics disabled
        """
        if cls._physics_engine:
            return cls._physics_engine.get_stats()
        return {}
