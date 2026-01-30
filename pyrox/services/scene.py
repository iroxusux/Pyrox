from datetime import datetime
from typing import Callable, Optional
from pyrox.interfaces import IApplication, IScene, IPhysicsBody2D
from pyrox.services import GuiManager
from pyrox.services.physics import PhysicsEngineService
from pyrox.services.environment import EnvironmentService


class SceneRunnerService:
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
        self.app = app
        self.scene = scene
        self.scene.on_scene_object_added.append(self.add_physics_body)
        self.scene.on_scene_object_removed.append(self.remove_physics_body)
        self.update_interval_ms = 16  # ~60 FPS (16ms)
        self.current_time = datetime.now().timestamp()

        # Physics integration
        self.enable_physics = enable_physics
        if enable_physics:
            self.environment = environment or EnvironmentService()
            self.physics_engine = physics_engine or PhysicsEngineService(
                environment=self.environment
            )
            self._register_physics_bodies()
        else:
            self.environment = None
            self.physics_engine = None

        self._is_running = False
        self._event_id = None
        self._on_tick_callbacks: list[Callable] = []

    def _register_physics_bodies(self) -> None:
        """Register all physics-enabled scene objects with the physics engine."""
        if not self.physics_engine:
            return

        scene_objects = self.scene.get_scene_objects()
        for scene_object in scene_objects.values():
            # Check if object implements physics body protocol
            if isinstance(scene_object, IPhysicsBody2D):
                self.physics_engine.register_body(scene_object)

    def run(self) -> None:
        """Run the scene within the application context."""
        if self._is_running:
            return

        self._is_running = True
        self.current_time = datetime.now().timestamp()

        # Schedule periodic updates
        self._event_id = GuiManager.unsafe_get_backend().schedule_event(
            self.update_interval_ms,
            lambda: self._run_scene()
        )

    def stop(self) -> None:
        """Stop the scene runner."""
        self._is_running = False
        if self._event_id:
            GuiManager.unsafe_get_backend().cancel_scheduled_event(self._event_id)
        self._event_id = None

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
        for callback in self._on_tick_callbacks:
            callback()

        # Schedule scene update on the main thread
        self._event_id = GuiManager.unsafe_get_backend().schedule_event(
            self.update_interval_ms,
            lambda: self._run_scene()
        )

    def set_update_rate(self, fps: int) -> None:
        """Set the update rate in frames per second.

        Args:
            fps: Target frames per second (1-240)
        """
        if not 1 <= fps <= 240:
            raise ValueError("FPS must be between 1 and 240")
        self.update_interval_ms = int(1000 / fps)

    def add_physics_body(self, body: IPhysicsBody2D) -> None:
        """Add a physics body to the simulation.

        Args:
            body: Object implementing IPhysicsBody protocol
        """
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

    @property
    def on_tick_callbacks(self) -> list[Callable]:
        """Get the list of on-tick callback functions.

        Returns:
            List of callback functions called each tick
        """
        return self._on_tick_callbacks
