""" file tasks
"""
import sys
from pyrox import models
from pyrox import services


class ExampleTask(models.ApplicationTask):

    def _open_scene_viewer(self) -> None:
        """Open the Scene Viewer frame."""
        # Create EnvironmentService
        environment = services.EnvironmentService(preset='top_down')

        # Initialize SceneRunnerService
        services.SceneRunnerService.initialize(
            app=self.application,
            environment=environment,
            enable_physics=True
        )

        # Create and register SceneViewerFrame
        scene_viewer = models.gui.sceneviewer.SceneViewerFrame(
            parent=self.application.workspace.workspace_area.root,  # type: ignore
            runner=services.SceneRunnerService
        )
        self.application.workspace.register_frame(scene_viewer)
        scene_viewer.on_destroy().append(lambda *_, **__: services.SceneRunnerService.stop())

        services.SceneRunnerService.new_scene()

        # Register runner callback to update scene viewer
        on_tick_callbacks = services.SceneRunnerService.get_on_tick_callbacks()
        if scene_viewer.render_scene not in on_tick_callbacks:
            on_tick_callbacks.append(scene_viewer.render_scene)

        services.SceneRunnerService.run()

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
