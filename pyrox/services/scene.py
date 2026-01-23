from datetime import datetime
from pyrox.interfaces import IApplication, IScene


class SceneRunnerService:
    """Run scenes with a supplied GUI Application context.
    """

    def __init__(
        self,
        app: IApplication,
        scene: IScene
    ):
        """Initialize the service.

        Args:
            app: The QApplication context to use.
        """
        self.app = app
        self.scene = scene
        self.update_interval_ms = 100  # Default to 100 ms
        self.current_time = datetime.now().timestamp()

    def run(self) -> None:
        """Run the scene within the application context."""
        self.app.gui_backend.schedule_event(
            100,  # TODO: Make configurable from scene settings
            lambda: self._run_scene()
        )

    def _run_scene(self) -> None:
        """Internal method to start the scene."""
        time_delta = datetime.now().timestamp() - self.current_time
        self.scene.update(time_delta)
