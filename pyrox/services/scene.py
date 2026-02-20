from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import importlib
from typing import Any, Callable, Dict, List, Optional, Union
import json
from pathlib import Path
from pyrox.interfaces import (
    IApplication,
    IPhysicsBody2D,
    IScene,
    ISceneBridge,
    ISceneObject,
    ISceneRunnerService,
)

from pyrox.services import GuiManager, log, physics
from pyrox.services import environment as env
from pyrox.services.file import get_open_file, get_save_file


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
    SCENE_SAVED = auto()    # Scene was saved to disk
    OBJECT_ADDED = auto()  # Object added to scene
    OBJECT_REMOVED = auto()  # Object removed from scene
    OBJECT_SELECTED = auto()  # Object selected in GUI
    OBJECT_DESELECTED = auto()  # Object deselected in GUI


@dataclass
class SceneEvent:
    """Event data for scene-related events."""

    event_type: SceneEventType
    scene: Optional[IScene] = None  # The scene object, if applicable
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


class SceneBridgeService:
    """Static service that owns and manages the active SceneBridge.

    Subscribes to :class:`SceneEventBus` and reacts to scene lifecycle events:

    * **SCENE_LOADED** — creates a new bridge for the incoming scene and
      attempts to restore binding configuration from a sidecar
      ``<scene>.bridge.json`` file if one exists.
    * **SCENE_UNLOADED** — stops and discards the bridge.
    * **SCENE_SAVED** — serialises the current bridge configuration to a
      ``<scene>.bridge.json`` sidecar file alongside the scene file.

    This keeps all bridge lifecycle logic out of the GUI.  GUI components
    retrieve the active bridge via :meth:`get_bridge` and display it through
    :class:`~pyrox.models.gui.scenebridge.SceneBridgeDialog`, but they no
    longer own or create the bridge.

    Sidecar convention::

        my_scene.json          ← scene data
        my_scene.bridge.json   ← bridge binding configuration (auto-managed)

    Typical application startup::

        SceneBridgeService.initialize()   # subscribe to event bus
        SceneRunnerService.initialize(app)
        SceneRunnerService.load_scene("my_scene.json")  # bridge auto-created
    """

    _bridge: Optional[ISceneBridge] = None  # SceneBridge instance
    _initialized: bool = False

    # Registry of named source factories populated before a scene loads.
    # Each entry is a Callable[[], Any] that produces the source instance.
    # All registered factories are called when a new bridge is created so
    # that the bound layer is pre-populated automatically.
    _source_factories: dict[str, Any] = {}  # name → Callable[[], Any]

    def __init__(self) -> None:
        raise TypeError("SceneBridgeService is a static class and cannot be instantiated")

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    @classmethod
    def initialize(cls) -> None:
        """Subscribe to SceneEventBus.  Safe to call multiple times."""
        if cls._initialized:
            return
        SceneEventBus.subscribe(SceneEventType.SCENE_LOADED,   cls._on_scene_loaded)
        SceneEventBus.subscribe(SceneEventType.SCENE_UNLOADED, cls._on_scene_unloaded)
        SceneEventBus.subscribe(SceneEventType.SCENE_SAVED,    cls._on_scene_saved)
        cls._initialized = True
        log(cls).debug("SceneBridgeService initialized")

    @classmethod
    def reset(cls) -> None:
        """Unsubscribe from all events and clear internal state.  Useful for tests."""
        SceneEventBus.unsubscribe(SceneEventType.SCENE_LOADED,   cls._on_scene_loaded)
        SceneEventBus.unsubscribe(SceneEventType.SCENE_UNLOADED, cls._on_scene_unloaded)
        SceneEventBus.unsubscribe(SceneEventType.SCENE_SAVED,    cls._on_scene_saved)
        if cls._bridge and cls._bridge.is_active():
            cls._bridge.stop()
        cls._bridge = None
        cls._source_factories.clear()
        cls._initialized = False
        log(cls).info("SceneBridgeService reset")

    # ------------------------------------------------------------------
    # Public accessor
    # ------------------------------------------------------------------

    @classmethod
    def get_bridge(cls) -> Optional[ISceneBridge]:
        """Return the currently active bridge, or ``None`` if no scene is loaded."""
        return cls._bridge

    # ------------------------------------------------------------------
    # Source factory registry
    # ------------------------------------------------------------------

    @classmethod
    def register_source_factory(
        cls,
        name: str,
        factory: Callable[[], Any],  # Callable[[], Any]
    ) -> None:
        """Register a factory that produces a bound-layer source.

        The factory is called with no arguments each time a new scene is
        loaded and a fresh :class:`~pyrox.models.scene.sceneboundlayer.SceneBoundLayer`
        is created.  The returned object is added to the layer under *name*.

        If the service already has an active bridge the source is
        immediately added to the current bound layer as well.

        Args:
            name:    Source name (must be a valid Python identifier).
            factory: Zero-argument callable that returns the source instance.

        Raises:
            KeyError: If a factory is already registered under *name*.
        """
        if name in cls._source_factories:
            raise KeyError(
                f"A source factory named '{name}' is already registered. "
                f"Call unregister_source_factory first to replace it."
            )
        cls._source_factories[name] = factory
        log(cls).debug(f"SceneBridgeService: registered source factory '{name}'")

        # If a bridge is already live, add the source to the current layer now.
        if cls._bridge is not None:
            from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
            bound = cls._bridge.get_bound_object()
            if isinstance(bound, SceneBoundLayer) and not bound.has_source(name):
                bound.register_source(name, factory())

    @classmethod
    def unregister_source_factory(cls, name: str) -> None:
        """Remove a source factory.  No-op if *name* is not registered.

        Does *not* remove the source from the currently active bridge's bound
        layer — it only prevents the factory from being called on future scene
        loads.
        """
        if name in cls._source_factories:
            del cls._source_factories[name]
            log(cls).debug(f"SceneBridgeService: unregistered source factory '{name}'")

    @classmethod
    def list_source_factories(cls) -> list[str]:
        """Return the names of all registered source factories."""
        return list(cls._source_factories.keys())

    # --------------------------------------------------------------------
    # Bridge management
    # --------------------------------------------------------------------

    @classmethod
    def new_bridge(cls, scene: IScene | None) -> None:
        """Create and set a new bridge for the given scene.

        Args:
            scene: The scene to bind the new bridge to
        """
        # Lazy import to avoid circular dependencies at module level
        from pyrox.models.scene.scenebridge import SceneBridge
        from pyrox.models.scene.sceneboundlayer import SceneBoundLayer
        if cls._bridge and cls._bridge.is_active():
            cls._bridge.stop()
        cls._bridge = SceneBridge(
            scene=scene,
            bound_object=SceneBoundLayer()
        )
        bound = cls._bridge.get_bound_object()
        if not isinstance(bound, SceneBoundLayer):
            raise TypeError("SceneBridge must be created with a SceneBoundLayer as its bound object")
        for source_name, factory in cls._source_factories.items():
            bound.register_source(source_name, factory())
        log(cls).info("created new SceneBridge for loaded scene")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @classmethod
    def _on_scene_loaded(cls, event: SceneEvent) -> None:
        """Create a fresh bridge when a scene is loaded."""
        # Stop any existing bridge cleanly
        if cls._bridge and cls._bridge.is_active():
            cls._bridge.stop()

        cls.new_bridge(event.scene)
        if not cls._bridge:
            raise RuntimeError("Failed to create SceneBridge for loaded scene")

        # Attempt to restore binding config from sidecar file
        filepath = (event.data or {}).get("filepath")
        if not filepath:
            return
        sidecar = cls._sidecar_path(Path(filepath))
        if not sidecar.is_file():
            return
        try:
            with open(sidecar, 'r') as f:
                cls._bridge.from_dict(json.load(f))
            log(cls).info(f"SceneBridgeService: restored bridge config from {sidecar}")
        except Exception as exc:
            log(cls).error(f"SceneBridgeService: failed to load bridge config from {sidecar}: {exc}")

    @classmethod
    def _on_scene_unloaded(cls, event: SceneEvent) -> None:
        """Stop and discard the bridge when the scene is unloaded."""
        if cls._bridge:
            if cls._bridge.is_active():
                cls._bridge.stop()
            cls._bridge = None
            log(cls).info("SceneBridgeService: bridge closed on scene unload")

    @classmethod
    def _on_scene_saved(cls, event: SceneEvent) -> None:
        """Persist bridge binding config as a sidecar file alongside the scene."""
        if not cls._bridge:
            log(cls).warning("SceneBridgeService: no active bridge to save on scene save")
            return
        filepath = (event.data or {}).get("filepath")
        if not filepath:
            log(cls).warning("SceneBridgeService: SCENE_SAVED missing filepath — bridge config not saved")
            return
        sidecar = cls._sidecar_path(Path(filepath))
        try:
            with open(sidecar, 'w') as f:
                json.dump(cls._bridge.to_dict(), f, indent=4)
            log(cls).info(f"SceneBridgeService: saved bridge config to {sidecar}")
        except Exception as exc:
            log(cls).error(f"SceneBridgeService: failed to save bridge config to {sidecar}: {exc}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sidecar_path(scene_filepath: Path) -> Path:
        """Return the bridge config sidecar path for a given scene filepath.

        Example: ``my_scene.json`` → ``my_scene.bridge.json``
        """
        return scene_filepath.with_name(scene_filepath.stem + ".bridge.json")


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
    _environment: Optional[env.EnvironmentService] = None
    _physics_engine: Optional[physics.PhysicsEngineService] = None

    # Scene file tracking (set by load_scene, consumed once by set_scene → SceneEventBus)
    _last_scene_filepath: Optional[Path] = None

    # Events
    _event_id: Optional[int | str] = None

    def __init__(self):
        raise ValueError("SceneRunnerService is a static class and cannot be initialized directly!")

    @classmethod
    def initialize(
        cls,
        app: IApplication,
        scene: Optional[IScene] = None,
        physics_engine: Optional[physics.PhysicsEngineService] = None,
        environment: Optional[env.EnvironmentService] = None,
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
        # Boot up the SceneBridgeService to ensure it subscribes to events before we set the initial scene
        SceneBridgeService.initialize()

        # Set application context
        cls._app = app
        cls._enable_physics = enable_physics

        # Physics integration
        if enable_physics:
            importlib.reload(physics)
            importlib.reload(env)
            cls.set_environment(environment or env.EnvironmentService())
            cls.set_physics_engine(physics_engine or physics.PhysicsEngineService(
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
            scene=scene,
            data={"filepath": cls._last_scene_filepath} if cls._last_scene_filepath else {},
        ))
        cls._last_scene_filepath = None

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
            cls._last_scene_filepath = filepath
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

        SceneEventBus.publish(SceneEvent(
            event_type=SceneEventType.SCENE_SAVED,
            scene=cls._scene,
            data={"filepath": filepath},
        ))

    @classmethod
    def get_physics_engine(cls) -> physics.PhysicsEngineService | None:
        """Get the physics engine being used.

        Returns:
            Physics engine instance, or None if physics is disabled.
        """
        return cls._physics_engine

    @classmethod
    def set_physics_engine(cls, physics_engine: physics.PhysicsEngineService | None) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance.
        """
        cls._physics_engine = physics_engine

    @classmethod
    def get_environment(cls) -> env.EnvironmentService | None:
        """Get the environment service being used.

        Returns:
            Environment service instance, or None if physics is disabled.
        """
        return cls._environment

    @classmethod
    def set_environment(cls, environment: env.EnvironmentService | None) -> None:  # type: ignore
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

        log(cls).debug("Scene runner started")

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
        log(cls).debug(f"Scene runner stopped with code {stop_code}")

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
