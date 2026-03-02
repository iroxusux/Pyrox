"""Unit tests for pyrox/tasks/sceneviewer.py"""
import unittest
from unittest.mock import MagicMock, patch

from pyrox.services import TkGuiManager
from pyrox.services.menu_registry import MenuRegistry
from pyrox.services.scene import SceneEventBus, SceneEventType


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_app(name: str = 'TestApp') -> MagicMock:
    app = MagicMock()
    app.name = name
    return app


class _SceneviewerTestBase(unittest.TestCase):
    """Base class that patches every external dependency of
    SceneviewerApplicationTask so no GUI or scene infrastructure runs."""

    def setUp(self):
        self.app = _make_app()

        self.mock_file_menu = MagicMock()
        self.mock_edit_menu = MagicMock()
        self.mock_view_menu = MagicMock()
        self.mock_help_menu = MagicMock()
        self.mock_tools_menu = MagicMock()
        self.mock_root = MagicMock()
        self.mock_submenu = MagicMock()

        self._patches = [
            # TkGuiManager menus
            patch.object(TkGuiManager, 'get_file_menu',  return_value=self.mock_file_menu),
            patch.object(TkGuiManager, 'get_edit_menu',  return_value=self.mock_edit_menu),
            patch.object(TkGuiManager, 'get_view_menu',  return_value=self.mock_view_menu),
            patch.object(TkGuiManager, 'get_help_menu',  return_value=self.mock_help_menu),
            patch.object(TkGuiManager, 'get_tools_menu', return_value=self.mock_tools_menu),
            patch.object(TkGuiManager, 'get_root',       return_value=self.mock_root),
            # MenuRegistry
            patch.object(MenuRegistry, 'register_item'),
            patch.object(MenuRegistry, 'enable_items_by_owner'),
            patch.object(MenuRegistry, 'disable_items_by_owner'),
            # SceneEventBus
            patch.object(SceneEventBus, 'subscribe'),
            patch.object(SceneEventBus, 'unsubscribe'),
            # SceneRunnerService (patch in-module reference)
            patch('pyrox.tasks.sceneviewer.SceneRunnerService'),
            # SceneViewerFrame
            patch('pyrox.tasks.sceneviewer.SceneViewerFrame'),
            # EnvironmentService
            patch('pyrox.tasks.sceneviewer.EnvironmentService'),
            # tkinter.Menu — prevents real Tk widget creation
            patch('pyrox.tasks.sceneviewer.tk.Menu', return_value=self.mock_submenu),
        ]
        self.mocks = [p.start() for p in self._patches]

        # Named references for frequently-used mocks
        self.mock_register_item = self.mocks[6]
        self.mock_enable_by_owner = self.mocks[7]
        self.mock_disable_by_owner = self.mocks[8]
        self.mock_subscribe = self.mocks[9]
        self.mock_unsubscribe = self.mocks[10]
        self.MockSceneRunnerService = self.mocks[11]
        self.MockSceneViewerFrame = self.mocks[12]
        self.MockEnvironmentService = self.mocks[13]

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def _make_task(self):
        from pyrox.tasks.sceneviewer import SceneviewerApplicationTask
        return SceneviewerApplicationTask(application=self.app)

    # ------------------------------------------------------------------
    # Helper: all menu_ids registered via MenuRegistry.register_item
    # ------------------------------------------------------------------
    def _registered_ids(self) -> list[str]:
        return [c.kwargs['menu_id'] for c in self.mock_register_item.call_args_list]


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestSceneviewerInit(_SceneviewerTestBase):

    def test_registers_task_with_application(self):
        """ApplicationTask base registers self with the application on init."""
        task = self._make_task()
        self.app.register_task.assert_called_once_with(task)

    def test_task_frame_initially_none(self):
        """_task_frame is None before any viewer is opened."""
        task = self._make_task()
        self.assertIsNone(task._task_frame)

    def test_subscribes_to_scene_loaded(self):
        """__init__ subscribes _scene_loaded_callback to SCENE_LOADED."""
        _ = self._make_task()
        subscribed_types = [c.args[0] for c in self.mock_subscribe.call_args_list]
        self.assertIn(SceneEventType.SCENE_LOADED, subscribed_types)

    def test_subscribes_to_scene_unloaded(self):
        """__init__ subscribes _scene_unloaded_callback to SCENE_UNLOADED."""
        _ = self._make_task()
        subscribed_types = [c.args[0] for c in self.mock_subscribe.call_args_list]
        self.assertIn(SceneEventType.SCENE_UNLOADED, subscribed_types)

    def test_subscribe_called_twice(self):
        """Exactly two SceneEventBus subscriptions are made in __init__."""
        self._make_task()
        self.assertEqual(self.mock_subscribe.call_count, 2)

    # ------------------------------------------------------------------
    # Menu item registration
    # ------------------------------------------------------------------

    def test_registers_scene_new_command(self):
        self._make_task()
        self.assertIn('scene.new', self._registered_ids())

    def test_registers_scene_save_command(self):
        self._make_task()
        self.assertIn('scene.save', self._registered_ids())

    def test_registers_scene_load_command(self):
        self._make_task()
        self.assertIn('scene.load', self._registered_ids())

    def test_registers_open_scene_viewer_command(self):
        self._make_task()
        self.assertIn('scene.open_scene_viewer', self._registered_ids())

    def test_registers_scene_view_submenu(self):
        self._make_task()
        self.assertIn('scene.view', self._registered_ids())

    def test_registers_scene_edit_submenu(self):
        self._make_task()
        self.assertIn('scene.edit', self._registered_ids())

    def test_registers_zoom_in(self):
        self._make_task()
        self.assertIn('scene.view.zoom_in', self._registered_ids())

    def test_registers_zoom_out(self):
        self._make_task()
        self.assertIn('scene.view.zoom_out', self._registered_ids())

    def test_registers_design_mode(self):
        self._make_task()
        self.assertIn('scene.view.design_mode', self._registered_ids())

    def test_registers_properties_panel(self):
        self._make_task()
        self.assertIn('scene.view.properties_panel', self._registered_ids())

    def test_registered_callbacks_are_bound_to_instance(self):
        """The stored callback references must be the same objects passed to subscribe."""
        task = self._make_task()
        subscribed_callbacks = [c.args[1] for c in self.mock_subscribe.call_args_list]
        self.assertIn(task._scene_loaded_callback,   subscribed_callbacks)
        self.assertIn(task._scene_unloaded_callback, subscribed_callbacks)


# ---------------------------------------------------------------------------
# _enable_menu_entries
# ---------------------------------------------------------------------------

class TestEnableMenuEntries(_SceneviewerTestBase):

    def test_enable_true_calls_enable_by_owner(self):
        """enable=True enables all menu items owned by this task."""
        from pyrox.services.scene import SceneEvent, SceneEventType
        task = self._make_task()
        event = SceneEvent(event_type=SceneEventType.SCENE_LOADED)
        task._enable_menu_entries(event, True)
        self.mock_enable_by_owner.assert_called_once_with(task.__class__.__name__)

    def test_enable_false_disables_then_re_enables_persistent(self):
        """enable=False disables all items, then re-enables persistent subcategory."""
        from pyrox.services.scene import SceneEvent, SceneEventType
        task = self._make_task()
        event = SceneEvent(event_type=SceneEventType.SCENE_UNLOADED)

        self.mock_enable_by_owner.reset_mock()
        self.mock_disable_by_owner.reset_mock()

        task._enable_menu_entries(event, False)

        self.mock_disable_by_owner.assert_called_once_with(task.__class__.__name__)
        self.mock_enable_by_owner.assert_called_once_with(
            task.__class__.__name__, subcategory='persistent'
        )

    def test_enable_false_disables_before_re_enabling(self):
        """disable_items_by_owner must be called before enable with subcategory."""
        from pyrox.services.scene import SceneEvent, SceneEventType
        task = self._make_task()
        event = SceneEvent(event_type=SceneEventType.SCENE_UNLOADED)

        call_order = []
        self.mock_disable_by_owner.side_effect = lambda *a, **kw: call_order.append('disable')
        self.mock_enable_by_owner.side_effect = lambda *a, **kw: call_order.append('enable')

        task._enable_menu_entries(event, False)

        self.assertEqual(call_order, ['disable', 'enable'])


# ---------------------------------------------------------------------------
# create_or_raise_frame
# ---------------------------------------------------------------------------

class TestCreateOrRaiseFrame(_SceneviewerTestBase):

    def test_creates_frame_when_none(self):
        """A new SceneViewerFrame is created when _task_frame is None."""
        task = self._make_task()
        task.create_or_raise_frame()

        self.MockSceneViewerFrame.assert_called_once_with(
            parent=self.app.workspace.workspace_area,
            runner=self.MockSceneRunnerService,
        )

    def test_registers_frame_with_workspace(self):
        """The new frame is registered in the application workspace."""
        task = self._make_task()
        task.create_or_raise_frame()
        self.app.workspace.register_frame.assert_called_once()

    def test_attaches_destroy_callback(self):
        """The _frame_destroy_callback is appended to the frame's on_destroy list."""
        task = self._make_task()
        task.create_or_raise_frame()
        frame = task._task_frame
        frame.on_destroy().append.assert_called_once_with(task._frame_destroy_callback)  # type: ignore

    def test_raises_existing_alive_frame(self):
        """An existing alive frame is raised rather than re-created."""
        task = self._make_task()

        alive_frame = MagicMock()
        alive_frame.root.winfo_exists.return_value = True
        task._task_frame = alive_frame

        self.MockSceneViewerFrame.reset_mock()
        task.create_or_raise_frame()

        self.MockSceneViewerFrame.assert_not_called()
        self.app.workspace.raise_frame.assert_called_once_with(alive_frame)

    def test_recreates_frame_when_window_destroyed(self):
        """A new frame is created if the existing frame's window no longer exists."""
        task = self._make_task()

        dead_frame = MagicMock()
        dead_frame.root.winfo_exists.return_value = False
        task._task_frame = dead_frame

        self.MockSceneViewerFrame.reset_mock()
        task.create_or_raise_frame()

        self.MockSceneViewerFrame.assert_called_once()


# ---------------------------------------------------------------------------
# _on_new_scene
# ---------------------------------------------------------------------------

class TestOnNewScene(_SceneviewerTestBase):

    def test_initializes_and_runs_scene_runner(self):
        """_on_new_scene creates the viewer, initialises the runner, and runs."""
        task = self._make_task()
        with patch.object(task, 'create_or_raise_frame') as mock_create:
            task._on_new_scene()

            mock_create.assert_called_once()
            self.MockSceneRunnerService.initialize.assert_called_once()
            self.MockSceneRunnerService.new_scene.assert_called_once()
            self.MockSceneRunnerService.run.assert_called_once()

    def test_initializes_with_application(self):
        task = self._make_task()
        with patch.object(task, 'create_or_raise_frame'):
            task._on_new_scene()
            init_call = self.MockSceneRunnerService.initialize.call_args
            self.assertIs(init_call.kwargs.get('app') or init_call.args[0], self.app)


# ---------------------------------------------------------------------------
# _on_load_scene
# ---------------------------------------------------------------------------

class TestOnLoadScene(_SceneviewerTestBase):

    def test_load_scene_no_scene_arg(self):
        """Without a scene argument, load_scene is called on the runner."""
        task = self._make_task()
        with patch.object(task, 'create_or_raise_frame'):
            task._on_load_scene()
            self.MockSceneRunnerService.initialize.assert_called_once()
            self.MockSceneRunnerService.load_scene.assert_called_once()
            self.MockSceneRunnerService.run.assert_called_once()

    def test_load_scene_with_scene_arg(self):
        """With a scene argument, it is passed through initialize; load_scene not called."""
        task = self._make_task()
        mock_scene = MagicMock()
        with patch.object(task, 'create_or_raise_frame'):
            task._on_load_scene(scene=mock_scene)
            init_call = self.MockSceneRunnerService.initialize.call_args
            self.assertIs(init_call.kwargs.get('scene'), mock_scene)
            self.MockSceneRunnerService.load_scene.assert_not_called()
            self.MockSceneRunnerService.run.assert_called_once()


# ---------------------------------------------------------------------------
# _open_scene_viewer
# ---------------------------------------------------------------------------

class TestOpenSceneViewer(_SceneviewerTestBase):

    def test_open_scene_viewer_calls_runner_lifecycle(self):
        """_open_scene_viewer initialises, creates the frame, runs new_scene, and runs."""
        task = self._make_task()
        with patch.object(task, 'create_or_raise_frame') as mock_create:
            task._open_scene_viewer()
            self.MockSceneRunnerService.initialize.assert_called_once()
            mock_create.assert_called_once()
            self.MockSceneRunnerService.new_scene.assert_called_once()
            self.MockSceneRunnerService.run.assert_called_once()

    def test_open_scene_viewer_passes_scene_to_initialize(self):
        """When a scene is provided it is forwarded to SceneRunnerService.initialize."""
        task = self._make_task()
        mock_scene = MagicMock()
        with patch.object(task, 'create_or_raise_frame'):
            task._open_scene_viewer(scene=mock_scene)
            init_kwargs = self.MockSceneRunnerService.initialize.call_args.kwargs
            self.assertIs(init_kwargs.get('scene'), mock_scene)


# ---------------------------------------------------------------------------
# _on_frame_destroyed
# ---------------------------------------------------------------------------

class TestOnFrameDestroyed(_SceneviewerTestBase):

    def test_stops_scene_runner(self):
        """_on_frame_destroyed stops the SceneRunnerService."""
        task = self._make_task()
        task._on_frame_destroyed()
        self.MockSceneRunnerService.stop.assert_called_once()

    def test_clears_scene(self):
        """_on_frame_destroyed sets the active scene to None."""
        task = self._make_task()
        task._on_frame_destroyed()
        self.MockSceneRunnerService.set_scene.assert_called_once_with(None)

    def test_clears_frame_reference(self):
        """_on_frame_destroyed sets _task_frame to None."""
        task = self._make_task()
        task._task_frame = MagicMock()
        task._on_frame_destroyed()
        self.assertIsNone(task._task_frame)


# ---------------------------------------------------------------------------
# Factory registration
# ---------------------------------------------------------------------------

class TestSceneviewerFactoryRegistration(unittest.TestCase):

    def test_registered_in_application_task_factory(self):
        import importlib
        import pyrox.models
        import pyrox.models.task
        import pyrox.tasks.sceneviewer
        importlib.reload(pyrox.models.task)  # ensure factory is reloaded to pick up registrations
        importlib.reload(pyrox.models)      # Re-bind pyrox.models names to the new task classes
        importlib.reload(pyrox.tasks.sceneviewer)

        self.assertIn(
            'SceneviewerApplicationTask',
            pyrox.models.task.ApplicationTaskFactory.get_registered_types()
        )

    def test_is_subclass_of_application_task(self):
        import importlib
        import pyrox.models
        import pyrox.models.task
        import pyrox.tasks.sceneviewer
        importlib.reload(pyrox.models.task)  # ensure factory is reloaded to pick up registrations
        importlib.reload(pyrox.models)      # Re-bind pyrox.models names to the new task classes
        importlib.reload(pyrox.tasks.sceneviewer)

        self.assertTrue(
            issubclass(
                pyrox.tasks.sceneviewer.SceneviewerApplicationTask,
                pyrox.models.task.ApplicationTask
            ))


if __name__ == '__main__':
    unittest.main(verbosity=2)
