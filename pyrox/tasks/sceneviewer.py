"""Sceneviewer task injection file.
This file is paired with the Sceneviewer GUI to initialize all command bar buttons.
They intialize as disabled until a sceneviewer is running, but all the buttons will occupy a space in the menu.
"""
import tkinter as tk
from pyrox.interfaces.application import IApplication
from pyrox.models import ApplicationTask, Scene
from pyrox.models.gui import SceneViewerFrame
from pyrox.services import (
    EnvironmentService,
    SceneRunnerService,
    SceneEventBus,
    SceneEvent,
    SceneEventType,
    MenuRegistry
)


class SceneviewerApplicationTask(ApplicationTask):
    def __init__(
        self,
        application: IApplication
    ) -> None:
        super().__init__(application)
        self._scene_viewer_frame: SceneViewerFrame | None = None

        # Store callback references for proper cleanup
        self._scene_loaded_callback = lambda event: self._enable_menu_entries(event, True)
        self._scene_unloaded_callback = lambda event: self._enable_menu_entries(event, False)
        self._frame_destroy_callback = lambda *_, **__: self._on_frame_destroyed()

        # ---------- File Menu ----------

        # Scene save / load controls
        self.register_menu_command(
            menu=self.file_menu,
            registry_id="scene.new",
            registry_path="File/New Scene",
            index=0,
            label="New Scene",
            command=self._on_new_scene,
            accelerator="Ctrl+N",
            underline=0,
            category="scene",
            subcategory="persistent"
        )

        self.register_menu_command(
            menu=self.file_menu,
            registry_id="scene.save",
            registry_path="File/Save Scene",
            index=1,
            label="Save Scene",
            command=SceneRunnerService.save_scene,
            accelerator="Ctrl+S",
            underline=0,
            category="scene",
            enabled=False
        )

        self.register_menu_command(
            menu=self.file_menu,
            registry_id="scene.load",
            registry_path="File/Load Scene",
            index=2,
            label="Load Scene",
            command=self._on_load_scene,
            accelerator="Ctrl+O",
            underline=0,
            category="scene",
            subcategory="persistent"
        )

        # ---------- Edit Menu ----------
        scene_edit_dropdown = tk.Menu(
            master=self.edit_menu,
            tearoff=0
        )

        self.register_menu_command(
            menu=scene_edit_dropdown,
            registry_id="scene.edit.delete_selected",
            registry_path="Edit/Scene Viewer/Delete Selected Objects",
            index=0,
            label="Delete Selected Objects",
            command=None,  # To be assigned by SceneViewer
            accelerator="Del",
            underline=7,
            category="scene",
            enabled=False
        )

        scene_edit_dropdown.insert_separator(1)

        self.register_menu_command(
            menu=scene_edit_dropdown,
            registry_id="scene.edit.group",
            registry_path="Edit/Scene Viewer/Group Selected",
            index=2,
            label="Group Selected",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Alt+G",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_edit_dropdown,
            registry_id="scene.edit.ungroup",
            registry_path="Edit/Scene Viewer/Ungroup",
            index=3,
            label="Ungroup",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Alt+U",
            underline=0,
            category="scene",
            enabled=False
        )

        self.register_submenu(
            menu=self.edit_menu,
            submenu=scene_edit_dropdown,
            registry_id="scene.edit",
            registry_path="Edit/Scene Viewer",
            index=0,
            label="Scene Viewer",
            underline=0,
            category="scene"
        )

        # ---------- View Menu ----------

        self.register_menu_command(
            menu=self.view_menu,
            registry_id="scene.open_scene_viewer",
            registry_path="View/Scene Viewer",
            index=3,
            label="View Scene",
            command=self._open_scene_viewer,
            accelerator="Ctrl+Shift+S",
            underline=0,
            category="scene",
            subcategory="persistent"
        )

        scene_view_dropdown = tk.Menu(
            master=self.view_menu,
            tearoff=0
        )

        # Zoom controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.zoom_in",
            registry_path="View/Scene Viewer/+Zoom In",
            index=0,
            label="+Zoom In",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl++",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.zoom_out",
            registry_path="View/Scene Viewer/-Zoom Out",
            index=1,
            label="-Zoom Out",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+-",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.reset_view",
            registry_path="View/Scene Viewer/Reset View",
            index=2,
            label="Reset View",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+0",
            underline=0,
            category="scene",
            enabled=False
        )

        scene_view_dropdown.insert_separator(3)

        # Grid controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.show_grid",
            registry_path="View/Scene Viewer/Show Grid",
            index=4,
            label="Show Grid",
            command=None,  # To be assigned by ViewportGriddingService
            accelerator="Ctrl+G",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.snap_to_grid",
            registry_path="View/Scene Viewer/Snap to Grid",
            index=5,
            label="Snap to Grid",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Shift+G",
            underline=0,
            category="scene",
            enabled=False
        )

        scene_view_dropdown.insert_separator(6)

        # Design Mode controls
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.design_mode",
            registry_path="View/Scene Viewer/Design Mode",
            index=7,
            label="Design Mode",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+D",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.object_palette",
            registry_path="View/Scene Viewer/Object Palette",
            index=8,
            label="Object Palette",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Shift+D",
            underline=0,
            category="scene",
            enabled=False
        )
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.properties_panel",
            registry_path="View/Scene Viewer/Properties Panel",
            index=9,
            label="Properties Panel",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Alt+D",
            underline=0,
            category="scene",
            enabled=False
        )

        # Scene Bridge Panel
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.bridge_panel",
            registry_path="View/Scene Viewer/Bridge Panel",
            index=10,
            label="Bridge Panel",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+Alt+B",
            underline=0,
            category="scene",
            enabled=False
        )

        # Connection editor
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.connection_editor",
            registry_path="View/Scene Viewer/Connection Editor",
            index=11,
            label="Connection Editor",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+E",
            underline=0,
            category="scene",
            enabled=False
        )

        scene_view_dropdown.insert_separator(12)

        # Entity Names Toggle
        self.register_menu_command(
            menu=scene_view_dropdown,
            registry_id="scene.view.entity_names",
            registry_path="View/Scene Viewer/Entity Names",
            index=13,
            label="Entity Names",
            command=None,  # To be assigned by SceneViewer
            accelerator="Ctrl+L",
            underline=0,
            category="scene",
            enabled=False
        )

        self.register_submenu(
            menu=self.view_menu,
            submenu=scene_view_dropdown,
            registry_id="scene.view",
            registry_path="View/Scene Viewer",
            index=2,
            label="Scene Viewer",
            underline=0,
            category="scene"
        )

        # Subscribe to scene events using stored callback references
        SceneEventBus.subscribe(
            SceneEventType.SCENE_LOADED,
            self._scene_loaded_callback
        )
        SceneEventBus.subscribe(
            SceneEventType.SCENE_UNLOADED,
            self._scene_unloaded_callback
        )

    def _enable_menu_entries(
        self,
        event: SceneEvent,
        enable: bool
    ) -> None:
        """Enable or disable all SceneViewer-related menu entries.
        Args:
            enable: True to enable, False to disable.
        """
        if enable:
            MenuRegistry.enable_items_by_owner(self.__class__.__name__)
        else:
            MenuRegistry.disable_items_by_owner(self.__class__.__name__)
            # Ensure persistent entries remain enabled/disabled regardless of scene state
            MenuRegistry.enable_items_by_owner(self.__class__.__name__, subcategory="persistent")

    def _create_scene_viewer_frame(self) -> None:
        """Create and register the SceneViewerFrame."""
        if self._scene_viewer_frame is None or not self._scene_viewer_frame.root.winfo_exists():
            self._scene_viewer_frame = SceneViewerFrame(
                parent=self.application.workspace.workspace_area,
                runner=SceneRunnerService
            )
            self.application.workspace.register_frame(self._scene_viewer_frame)
            self._scene_viewer_frame.on_destroy().append(self._frame_destroy_callback)
        else:
            self.application.workspace.raise_frame(self._scene_viewer_frame)

    def _on_new_scene(self) -> None:
        self._create_scene_viewer_frame()
        # Initialize SceneRunnerService
        SceneRunnerService.initialize(
            app=self.application,
            environment=EnvironmentService(preset='top_down'),
            enable_physics=True
        )
        SceneRunnerService.new_scene()
        SceneRunnerService.run()

    def _on_load_scene(
            self,
            scene: Scene | None = None
    ) -> None:
        self._create_scene_viewer_frame()
        if not scene:
            SceneRunnerService.initialize(
                app=self.application,
                environment=EnvironmentService(preset='top_down'),
                enable_physics=True
            )
            SceneRunnerService.load_scene()
        else:
            SceneRunnerService.initialize(
                app=self.application,
                scene=scene,
                environment=EnvironmentService(preset='top_down'),
                enable_physics=True
            )
        SceneRunnerService.run()

    def _open_scene_viewer(
        self,
        scene: Scene | None = None
    ) -> None:
        """Open the Scene Viewer frame."""

        # Initialize SceneRunnerService
        SceneRunnerService.initialize(
            app=self.application,
            scene=scene,
            environment=EnvironmentService(preset='top_down'),
            enable_physics=True
        )

        self._create_scene_viewer_frame()
        SceneRunnerService.new_scene()
        SceneRunnerService.run()

    def _on_frame_destroyed(self) -> None:
        """Handle cleanup when the SceneViewerFrame is destroyed."""
        SceneRunnerService.stop()
        SceneRunnerService.set_scene(None)
        self._scene_viewer_frame = None

    def cleanup(self) -> None:
        """Clean up all subscriptions and callbacks to prevent lingering references.

        This method should be called when the task is being removed or the application
        is shutting down to prevent memory leaks and runtime errors from stale callbacks.
        """
        # Unsubscribe from SceneEventBus using the exact callback references
        SceneEventBus.unsubscribe(
            SceneEventType.SCENE_LOADED,
            self._scene_loaded_callback
        )
        SceneEventBus.unsubscribe(
            SceneEventType.SCENE_UNLOADED,
            self._scene_unloaded_callback
        )

        # Remove frame destroy callback if frame still exists
        if self._scene_viewer_frame is not None:
            try:
                if self._frame_destroy_callback in self._scene_viewer_frame.on_destroy():
                    self._scene_viewer_frame.on_destroy().remove(self._frame_destroy_callback)
            except (AttributeError, ValueError):
                pass  # Frame might already be destroyed

        # Stop the scene runner if it's running
        try:
            SceneRunnerService.stop()
        except Exception:
            pass  # Runner might not be initialized

        self._scene_viewer_frame = None
