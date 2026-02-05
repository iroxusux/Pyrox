""" file tasks
"""
import importlib
import sys
from pyrox import interfaces
from pyrox import models
from pyrox import services


class ExampleTask(models.ApplicationTask):

    def _open_scene_viewer(self) -> None:
        """Open the Scene Viewer frame."""
        # Reload modules to ensure the latest changes are reflected
        importlib.reload(interfaces)
        importlib.reload(models)
        importlib.reload(services)

        # Create Scene
        s = models.scene.Scene()

        # Create EnvironmentService
        environment = services.EnvironmentService(preset='top_down')

        # Create SceneRunnerService
        runner = services.SceneRunnerService(
            app=self.application,
            scene=s,
            environment=environment,
            enable_physics=True
        )

        # Create and register SceneViewerFrame
        scene_viewer = models.gui.sceneviewer.SceneViewerFrame(
            parent=self.application.workspace.workspace_area.root,  # type: ignore
            scene=s,
            runner=runner,
        )
        self.application.workspace.register_frame(scene_viewer)
        scene_viewer.on_destroy().append(lambda *_, **__: runner.stop())

        # Register runner callback to update scene viewer
        runner.on_tick_callbacks.append(scene_viewer.render_scene)

        runner.run()

    def inject(self) -> None:
        self.file_menu.add_item(
            index=0,
            label='Exit',
            command=lambda: exit(0),
            accelerator='Ctrl+Q',
            underline=0,
            binding_info=('<Control-q>', lambda e: sys.exit(0))
        )
        self.view_menu.add_item(
            index=1,
            label='View Scene',
            command=self._open_scene_viewer,
            accelerator='Ctrl+Shift+S',
            underline=0,
            binding_info=('<Control-Shift-s>', lambda e: self._open_scene_viewer())
        )
