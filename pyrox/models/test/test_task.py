"""Unit tests for task.py module."""
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from pyrox.models.task import ApplicationTask, ApplicationTaskFactory


class TestApplicationTaskFactory(unittest.TestCase):
    """Test cases for ApplicationTaskFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        ApplicationTaskFactory._registered_types = {}

    def tearDown(self):
        """Clean up registered types after each test."""
        ApplicationTaskFactory._registered_types = {}

    def test_build_tasks_calls_each_task_with_application(self):
        """Test that build_tasks instantiates each registered task type with the application."""
        mock_application = MagicMock()
        mock_task_cls_a = MagicMock()
        mock_task_cls_b = MagicMock()

        ApplicationTaskFactory._registered_types = {
            'TaskA': mock_task_cls_a,
            'TaskB': mock_task_cls_b,
        }

        ApplicationTaskFactory.build_tasks(mock_application)

        mock_task_cls_a.assert_called_once_with(application=mock_application)
        mock_task_cls_b.assert_called_once_with(application=mock_application)

    def test_build_tasks_empty_registry(self):
        """Test that build_tasks handles an empty registry without errors."""
        mock_application = MagicMock()
        ApplicationTaskFactory._registered_types = {}

        # Should not raise
        ApplicationTaskFactory.build_tasks(mock_application)

    def test_build_tasks_logs_count(self):
        """Test that build_tasks logs the number of tasks being built."""
        mock_application = MagicMock()
        mock_task_cls = MagicMock()
        ApplicationTaskFactory._registered_types = {'Task': mock_task_cls}

        with patch('pyrox.models.task.log') as mock_log:
            mock_logger = MagicMock()
            mock_log.return_value = mock_logger
            ApplicationTaskFactory.build_tasks(mock_application)

        mock_log.assert_called_once_with(ApplicationTaskFactory)
        mock_logger.debug.assert_called_once()


class TestApplicationTask(unittest.TestCase):
    """Test cases for ApplicationTask class."""

    def _make_application(self):
        application = MagicMock()
        application.name = 'TestApp'
        return application

    def test_init_registers_task_with_application(self):
        """Test that __init__ registers the task with the parent application."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        mock_app.register_task.assert_called_once_with(task)

    def test_get_application_returns_application(self):
        """Test that get_application returns the parent application."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        self.assertIs(task.get_application(), mock_app)

    def test_set_application_updates_application(self):
        """Test that set_application replaces the parent application."""
        mock_app_a = self._make_application()
        mock_app_b = self._make_application()
        mock_app_b.name = 'TestApp2'

        task = ApplicationTask(application=mock_app_a)
        task.set_application(mock_app_b)

        self.assertIs(task.get_application(), mock_app_b)

    def test_application_property_getter(self):
        """Test that the application property delegates to get_application."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        self.assertIs(task.application, mock_app)

    def test_application_property_setter(self):
        """Test that the application property setter delegates to set_application."""
        mock_app_a = self._make_application()
        mock_app_b = self._make_application()

        task = ApplicationTask(application=mock_app_a)
        task.application = mock_app_b

        self.assertIs(task.get_application(), mock_app_b)

    def test_register_menu_command_delegates_to_tk_gui_manager(self):
        """register_menu_command delegates insertion+binding to TkGuiManager."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        mock_menu = MagicMock(spec=tk.Menu)
        dummy_command = MagicMock()

        with patch('pyrox.models.task.TkGuiManager.insert_menu_command_with_accelerator') as mock_insert, \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.open',
                registry_path='File/Open',
                index=0,
                label='Open',
                command=dummy_command,
                accelerator='Ctrl+O',
                underline=0,
            )

        mock_insert.assert_called_once_with(
            menu=mock_menu,
            index=0,
            label='Open',
            command=dummy_command,
            accelerator='Ctrl+O',
            underline=0,
        )

    def test_register_menu_command_noop_when_no_command(self):
        """None command is passed through to insert_menu_command_with_accelerator without raising."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.TkGuiManager.insert_menu_command_with_accelerator') as mock_insert, \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.save',
                registry_path='File/Save',
                index=1,
                label='Save',
                command=None,
                accelerator='Ctrl+S',
                underline=0,
            )

        # None is forwarded; the no-op substitution happens inside TkGuiManager
        mock_insert.assert_called_once()
        self.assertIsNone(mock_insert.call_args.kwargs['command'])

    def test_register_menu_command_disables_when_not_enabled(self):
        """Test that a disabled menu command calls entryconfig with DISABLED state."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.TkGuiManager.insert_menu_command_with_accelerator'), \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='edit.undo',
                registry_path='Edit/Undo',
                index=0,
                label='Undo',
                command=MagicMock(),
                accelerator='Ctrl+Z',
                underline=0,
                enabled=False,
            )

        mock_menu.entryconfig.assert_called_once_with(0, state=tk.DISABLED)

    def test_register_menu_command_enabled_does_not_call_entryconfig(self):
        """Test that an enabled menu command does not call entryconfig."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.TkGuiManager.insert_menu_command_with_accelerator'), \
                patch('pyrox.models.task.MenuRegistry'):
            task.register_menu_command(
                menu=mock_menu,
                registry_id='edit.redo',
                registry_path='Edit/Redo',
                index=0,
                label='Redo',
                command=MagicMock(),
                accelerator='Ctrl+Y',
                underline=0,
                enabled=True,
            )

        mock_menu.entryconfig.assert_not_called()

    def test_register_menu_command_registers_with_registry(self):
        """Test that register_menu_command registers with MenuRegistry."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)
        dummy_command = MagicMock()

        with patch('pyrox.models.task.TkGuiManager.insert_menu_command_with_accelerator'), \
                patch('pyrox.models.task.MenuRegistry') as mock_registry:
            task.register_menu_command(
                menu=mock_menu,
                registry_id='file.exit',
                registry_path='File/Exit',
                index=2,
                label='Exit',
                command=dummy_command,
                accelerator='Alt+F4',
                underline=1,
                category='file',
                subcategory='actions',
            )

        mock_registry.register_item.assert_called_once_with(
            menu_id='file.exit',
            menu_path='File/Exit',
            menu_widget=mock_menu,
            menu_index=2,
            owner='ApplicationTask',
            command=dummy_command,
            category='file',
            subcategory='actions',
        )

    def test_register_submenu_inserts_cascade(self):
        """Test that register_submenu calls menu.insert_cascade."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)
        mock_submenu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.MenuRegistry'):
            task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='view.panels',
                registry_path='View/Panels',
                index=1,
                label='Panels',
                underline=0,
            )

        mock_menu.insert_cascade.assert_called_once_with(
            label='Panels',
            menu=mock_submenu,
            index=1,
            underline=0,
        )

    def test_register_submenu_returns_submenu(self):
        """Test that register_submenu returns the submenu passed in."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)
        mock_submenu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.MenuRegistry'):
            result = task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='view.tools',
                registry_path='View/Tools',
                index=0,
                label='Tools',
                underline=0,
            )

        self.assertIs(result, mock_submenu)

    def test_register_submenu_registers_with_registry(self):
        """Test that register_submenu registers with MenuRegistry."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        mock_menu = MagicMock(spec=tk.Menu)
        mock_submenu = MagicMock(spec=tk.Menu)

        with patch('pyrox.models.task.MenuRegistry') as mock_registry:
            task.register_submenu(
                menu=mock_menu,
                submenu=mock_submenu,
                registry_id='help.about',
                registry_path='Help/About',
                index=0,
                label='About',
                underline=0,
                category='help',
            )

        mock_registry.register_item.assert_called_once_with(
            menu_id='help.about',
            menu_path='Help/About',
            menu_widget=mock_submenu,
            menu_index=0,
            owner='ApplicationTask',
            category='help',
        )

    # ------------------------------------------------------------------
    # Frame lifecycle: _task_frame, create_or_raise_frame, _on_frame_destroyed
    # ------------------------------------------------------------------

    def test_task_frame_initially_none(self):
        """_task_frame is None immediately after construction."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        self.assertIsNone(task._task_frame)

    def test_frame_destroy_callback_is_set(self):
        """_frame_destroy_callback is a callable set during __init__."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        self.assertTrue(callable(task._frame_destroy_callback))

    def test_create_or_raise_frame_creates_when_none(self):
        """create_or_raise_frame calls create_task_frame when _task_frame is None."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        mock_frame = MagicMock()
        mock_frame.root.winfo_exists.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        self.assertIs(task._task_frame, mock_frame)

    def test_create_or_raise_frame_registers_with_workspace(self):
        """create_or_raise_frame registers the new frame with the workspace."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        mock_frame = MagicMock()
        mock_frame.root.winfo_exists.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        mock_app.workspace.register_frame.assert_called_once_with(mock_frame)

    def test_create_or_raise_frame_attaches_destroy_callback(self):
        """create_or_raise_frame appends _frame_destroy_callback to the frame's on_destroy list."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        mock_frame = MagicMock()
        mock_frame.root.winfo_exists.return_value = True

        with patch.object(task, 'create_task_frame', return_value=mock_frame):
            task.create_or_raise_frame()

        mock_frame.on_destroy().append.assert_called_once_with(task._frame_destroy_callback)

    def test_create_or_raise_frame_raises_alive_frame(self):
        """create_or_raise_frame raises an existing alive frame instead of creating a new one."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        alive_frame = MagicMock()
        alive_frame.root.winfo_exists.return_value = True
        task._task_frame = alive_frame

        with patch.object(task, 'create_task_frame') as mock_create:
            task.create_or_raise_frame()
            mock_create.assert_not_called()

        mock_app.workspace.raise_frame.assert_called_once_with(alive_frame)

    def test_create_or_raise_frame_recreates_destroyed_frame(self):
        """create_or_raise_frame creates a new frame when the existing window is destroyed."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        dead_frame = MagicMock()
        dead_frame.root.winfo_exists.return_value = False
        task._task_frame = dead_frame

        new_frame = MagicMock()
        new_frame.root.winfo_exists.return_value = True

        with patch.object(task, 'create_task_frame', return_value=new_frame):
            task.create_or_raise_frame()

        self.assertIs(task._task_frame, new_frame)

    def test_on_frame_destroyed_clears_task_frame(self):
        """_on_frame_destroyed resets _task_frame to None."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)
        task._task_frame = MagicMock()

        task._on_frame_destroyed()

        self.assertIsNone(task._task_frame)

    def test_frame_destroy_callback_triggers_on_frame_destroyed(self):
        """Invoking _frame_destroy_callback calls _on_frame_destroyed."""
        mock_app = self._make_application()
        task = ApplicationTask(application=mock_app)

        with patch.object(task, '_on_frame_destroyed') as mock_handler:
            task._frame_destroy_callback()
            mock_handler.assert_called_once()


if __name__ == '__main__':
    unittest.main()
