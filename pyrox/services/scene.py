from datetime import datetime
from typing import Callable, Optional, Union
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
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService


class SceneRunnerService(
    ISceneRunnerService,
):
    """Run scenes with a supplied GUI Application context.

    Integrates physics simulation with scene updates, providing a complete
    runtime environment with fixed timestep physics and frame-rate independent
    rendering.
    """

    def __init__(
        self,
        app: IApplication,
        scene: IScene,
        physics_engine: Optional[PhysicsEngineService] = None,
        environment: Optional[EnvironmentService] = None,
        enable_physics: bool = False,
    ):
        """Initialize the service.

        Args:
            app: The Application context to use
            scene: The scene to run
            physics_engine: Optional physics engine (creates default if None and enable_physics=True)
            environment: Optional environment service (creates default if None and enable_physics=True)
            enable_physics: Whether to enable physics simulation
        """
        self._is_running = False
        self.app = app
        self.enable_physics = enable_physics
        self._scene = scene
        self._bind_to_scene_events()
        # Physics integration
        if enable_physics:
            self._environment = environment or EnvironmentService()
            self._physics_engine = physics_engine or PhysicsEngineService(
                environment=self._environment
            )
        else:
            self._environment = None
            self._physics_engine = None
        self._register_physics_bodies()

        # Update timing
        self.update_interval_ms = 16  # ~60 FPS (16ms)
        self.current_time = datetime.now().timestamp()

        self._event_id = None
        self._on_tick_callbacks: list[Callable] = []
        self._on_scene_load_callbacks: list[Callable] = []

    def is_running(self) -> bool:
        """Check if the scene runner is currently running.

        Returns:
            True if running, False otherwise.
        """
        return self._is_running

    def set_running(self, running: bool) -> None:
        """Set the running state of the scene runner.

        Args:
            running: True to set as running, False to stop.
        """
        self._is_running = running

    def get_scene(self) -> IScene:
        """Get the scene being managed.

        Returns:
            IScene: The scene instance.
        """
        return self._scene

    def set_scene(self, scene: IScene) -> None:
        """Set the scene to be managed.

        Args:
            scene: The new scene instance.
        """
        self._scene = scene
        self._register_physics_bodies()
        self._bind_to_scene_events()
        [callback(scene) for callback in self._on_scene_load_callbacks]

    def load_scene(self, filepath: str | Path) -> None:
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data = json.load(f)
            scene = self.scene.from_dict(data)
            self.set_scene(scene)

    def save_scene(self, filepath: str | Path) -> None:
        filepath = Path(filepath)
        data = self.scene.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

    def get_physics_engine(self) -> PhysicsEngineService | None:
        """Get the physics engine being used.

        Returns:
            Physics engine instance, or None if physics is disabled.
        """
        return self._physics_engine

    def set_physics_engine(self, physics_engine: PhysicsEngineService) -> None:
        """Set the physics engine to be used.

        Args:
            physics_engine: The physics engine instance.
        """
        self._physics_engine = physics_engine

    def get_environment(self) -> object | None:
        """Get the environment service being used.

        Returns:
            Environment service instance, or None if physics is disabled.
        """
        return self._environment

    def set_environment(self, environment: object) -> None:
        """Set the environment service to be used.

        Args:
            environment: The environment service instance.
        """
        self._environment = environment

    def _bind_to_scene_events(self) -> None:
        """Bind to scene events for object addition/removal."""
        self._scene.on_scene_object_added.append(self.add_physics_body)
        self._scene.on_scene_object_removed.append(self.remove_physics_body)

    def _register_physics_bodies(self) -> None:
        """Register all physics-enabled scene objects with the physics engine."""
        if not self.physics_engine or not self.enable_physics:
            return

        scene_objects = self.scene.get_scene_objects()
        for scene_object in scene_objects.values():
            # Check if object implements physics body protocol
            if isinstance(scene_object.physics_body, IPhysicsBody2D):
                self.physics_engine.register_body(scene_object.physics_body)
            else:
                raise TypeError("Scene object physics body does not implement IPhysicsBody2D protocol")

    def run(self) -> int:
        """Run the scene within the application context."""
        if self.running:
            return 1  # Already running

        self._is_running = True
        self.current_time = datetime.now().timestamp()

        # Schedule periodic updates
        self._event_id = GuiManager.unsafe_get_backend().schedule_event(
            self.update_interval_ms,
            lambda: self._run_scene()
        )
        return 0

    def stop(self, stop_code: int = 0) -> None:
        """Stop the scene runner."""
        self._is_running = False
        if self._event_id:
            GuiManager.unsafe_get_backend().cancel_scheduled_event(self._event_id)
        self._event_id = None
        log(self).info(f"Scene runner stopped with code {stop_code}")

    def _run_scene(self) -> None:
        """Internal method to update the scene each frame."""
        if not self._is_running:
            return

        # Calculate time delta
        new_time = datetime.now().timestamp()
        time_delta = new_time - self.current_time
        self.current_time = new_time

        # Clamp time delta to prevent spiral of death
        time_delta = min(time_delta, 0.1)  # Max 100ms

        # Update physics (if enabled)
        if self.enable_physics and self.physics_engine:
            self.physics_engine.step(time_delta)

        # Call on-tick callbacks
        for callback in self._on_tick_callbacks.copy():
            try:
                callback()
            except Exception as e:
                # Log error but continue
                print(f"Error in on-tick callback: {e}")
                self._on_tick_callbacks.remove(callback)

        # Schedule scene update on the main thread
        self._event_id = GuiManager.unsafe_get_backend().schedule_event(
            self.update_interval_ms,
            lambda: self._run_scene()
        )

    def get_update_rate(self) -> float:
        """Get the current update rate in frames per second.

        Returns:
            Current frames per second
        """
        return 1000.0 / self.update_interval_ms

    def set_update_rate(self, fps: float) -> None:
        """Set the update rate in frames per second.

        Args:
            fps: Target frames per second (1-240)
        """
        if not 1 <= fps <= 240:
            raise ValueError("FPS must be between 1 and 240")
        self.update_interval_ms = int(1000 / fps)

    def add_physics_body(self, body: Union[IPhysicsBody2D, ISceneObject]) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IPhysicsBody protocol
        """
        if isinstance(body, ISceneObject):
            if not isinstance(body.physics_body, IPhysicsBody2D):
                raise TypeError("SceneObject does not have a valid physics body")
            body = body.physics_body

        if self.physics_engine:
            self.physics_engine.register_body(body)

    def remove_physics_body(self, body) -> None:
        """Remove a physics body from the simulation.

        Args:
            body: Object to remove
        """
        if self.physics_engine:
            self.physics_engine.unregister_body(body)

    def get_physics_stats(self) -> dict:
        """Get physics engine statistics.

        Returns:
            Dictionary with physics stats, or empty dict if physics disabled
        """
        if self.physics_engine:
            return self.physics_engine.get_stats()
        return {}

    def get_on_tick_callbacks(self) -> list[Callable]:
        """Get the list of on-tick callback functions.

        Returns:
            List of callback functions.
        """
        return self._on_tick_callbacks

    def get_on_scene_load_callbacks(self) -> list[Callable]:
        """Get the list of on-scene-load callback functions.

        Returns:
            List of callback functions.
        """
        return self._on_scene_load_callbacks

    @property
    def running(self) -> bool:
        """Check if the scene runner is currently running.

        Returns:
            True if running, False otherwise.
        """
        return self.is_running()

    @running.setter
    def running(self, running: bool) -> None:
        """Set the running state of the scene runner.

        Args:
            running: True to set as running, False to stop.
        """
        self.set_running(running)

    @property
    def physics_engine(self) -> PhysicsEngineService | None:
        """Get the physics engine being used.

        Returns:
            Physics engine instance, or None if physics is disabled.
        """
        return self.get_physics_engine()
